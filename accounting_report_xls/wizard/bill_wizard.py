from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError, ValidationError

class BillReportWizard(models.TransientModel):
    _name = 'bill.report.wizard'
    
    @api.multi
    def get_first_date(self):
        current_date = date.today()
        return date(current_date.year, current_date.month, 1)

    @api.multi
    def _default_currency(self):
        currency = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1)
        return currency and currency.id or False
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    date_from = fields.Date('Start Date', default=get_first_date)
    date_to = fields.Date('End Date', default=date.today())
    partner_ids = fields.Many2many('res.partner', string='Partner(s)')
    type = fields.Selection([
        ('idr', 'IDR'),
        ('valas', 'VALAS')
    ], string='Type', default='idr')
    report_type = fields.Selection([
        ('rekap', 'Rekap'),
        ('detail', 'Detail')
    ], string='Report Type', default='rekap')
    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency)
    invoice_ids = fields.Many2many('account.invoice', string='Invoice(s)')
    
    @api.onchange('type')
    def change_type(self):
        if self.type == 'idr':
            self.currency_id = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1).id
        else:
            self.currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).id
    
    @api.multi
    def _get_stpb_date(self, stpb):
        picking = self.env['stock.picking'].search([('name', '=', stpb)], limit=1)
        return picking and datetime.strptime(picking.min_date[:10], "%Y-%m-%d").strftime("%d-%m-%Y") or ''

    @api.multi
    def view_bill_report(self):
        if self.type == 'idr':
            return self.view_bill_idr_report()
        else:
            return self.view_bill_valas_report()

    @api.multi
    def view_bill_idr_report(self):
        datas = {}        
        compiled_data = {}
        datas['ids'] = [self['id']]
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['partner_ids'] = self.partner_ids and ', '.join(map(str, [x.name for x in self['partner_ids']])) or 'All'
        datas['invoice_ids'] = self.invoice_ids and ', '.join(map(str, [x.number for x in self['invoice_ids']])) or 'All'
        datas['report_type'] = 'Rekap' and self.report_type == 'rekap' or 'Detail'

        if not self.invoice_ids:
            domain = [
                ('date_invoice', '>=', self.date_from),
                ('date_invoice', '<=', self.date_to),
                ('state', 'not in', ('cancel','draft')),
                ('currency_id', '=', self.currency_id.id),
                ('type', '=', 'in_invoice')
            ]
            if self.partner_ids:
                domain.append(('partner_id', 'in', self.partner_ids.ids))
        else:
            domain = [
                ('id', 'in', self.invoice_ids.ids)
            ]

        bills = self.env['account.invoice'].search(domain, order='date_invoice')
        gt_total = gt_biaya_service = gt_jasa_lain = gt_min_order_dpp = gt_min_order_dpp_ppn = gt_bi_lokal = gt_bi_import = \
            gt_pph22 = gt_pph23 = gt_pph23s = gt_retur = gt_retur_ppn = gt_price_adj = gt_price_adj_ppn = gt_lain = gt_total_dibayar = 0
        for bill in bills:
            if not bill.invoice_line_ids:
                continue
            partner = bill.partner_id.name or 'Undefined'
            bill_id = bill.id
            if not compiled_data.get(partner):
                compiled_data[partner] = {
                    'bills' : {}
                }
            if not compiled_data[partner]['bills'].get(bill_id):
                compiled_data[partner]['bills'][bill_id] = {
                    'number': bill.number,
                    'partner': bill.partner_id.name,
                    'account': '%s %s' % (bill.account_id.code, bill.account_id.name),
                    'kb': bill.nobukti_kontrabon.name or '',
                    'grir': [],
                    'biaya_service': [],
                    'jasa_lain': [],
                    'min_order_qty': [],
                    'bi_lokal': [],
                    'bi_import': [],
                    'pph22': [],
                    'pph23': [],
                    'pph23s': [],
                    'retur_pembelian': [],
                    'price_adjustment': [],
                    'lain': [],
                }      
            #GR/IR DPP: 2106010000 PPN: 1108010100
            grir_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '2106010000' and l.price_subtotal > 0)
            for grir_line in grir_lines:
                data = [
                    grir_line.purchase_id.name,
                    datetime.strptime(grir_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    grir_line.nostpb or '',
                    self._get_stpb_date(grir_line.nostpb) if grir_line.nostpb else '',
                    grir_line.product_id.display_name or '',
                    grir_line.notes or '',
                    grir_line.invoice_id.reference or '',
                    grir_line.quantity,
                    grir_line.uom_id.name,
                    grir_line.price_unit,
                    grir_line.price_subtotal,
                    grir_line.invoice_line_tax_ids and grir_line.invoice_line_tax_ids[0].amount / 100 * grir_line.price_subtotal or 0
                ]
                gt_total += grir_line.price_subtotal + (grir_line.invoice_line_tax_ids and grir_line.invoice_line_tax_ids[0].amount / 100 * grir_line.price_subtotal or 0)
                compiled_data[partner]['bills'][bill_id]['grir'].append(data)
            #BIAYA SERVICE KENDARAAN: 4102051900
            biaya_service_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4102051900')
            for biaya_service_line in biaya_service_lines:
                data = [
                    biaya_service_line.purchase_id.name or '',
                    datetime.strptime(biaya_service_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    '',
                    '',
                    biaya_service_line.product_id.display_name or '',
                    biaya_service_line.notes or '',
                    biaya_service_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    biaya_service_line.price_subtotal or 0
                ]
                gt_biaya_service += biaya_service_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['biaya_service'].append(data)
            #JASA LAINNYA: 4102063100
            jasa_lain_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4102063100')
            for jasa_lain_line in jasa_lain_lines:
                data = [
                    jasa_lain_line.purchase_id.name or '',
                    datetime.strptime(jasa_lain_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    '',
                    '',
                    jasa_lain_line.product_id.display_name or '',
                    jasa_lain_line.notes or '',
                    jasa_lain_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    jasa_lain_line.price_subtotal or 0
                ]
                gt_jasa_lain += jasa_lain_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['jasa_lain'].append(data)
            #MIN ORDER QTY / SURCHAGE: 4102061100
            min_order_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4102061100')
            for min_order_line in min_order_lines:
                data = [
                    min_order_line.purchase_id.name or '',
                    datetime.strptime(min_order_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    min_order_line.nostpb or '',
                    '',
                    min_order_line.product_id.display_name or '',
                    min_order_line.notes or '',
                    min_order_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    min_order_line.price_subtotal or 0,
                    min_order_line.invoice_line_tax_ids and min_order_line.invoice_line_tax_ids[0].amount / 100 * min_order_line.price_subtotal or 0
                ]
                gt_min_order_dpp += min_order_line.price_subtotal or 0
                gt_min_order_dpp_ppn += min_order_line.invoice_line_tax_ids and min_order_line.invoice_line_tax_ids[0].amount / 100 * min_order_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['min_order_qty'].append(data)
            #BI LOKAL: 6405110000
            bi_local_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '6405110000')
            for bi_local_line in bi_local_lines:
                data = [
                    bi_local_line.purchase_id.name or '',
                    datetime.strptime(bi_local_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    bi_local_line.nostpb or '',
                    '',
                    bi_local_line.product_id.display_name or '',
                    bi_local_line.notes or '',
                    bi_local_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    bi_local_line.price_subtotal or 0
                ]
                gt_bi_lokal += bi_local_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['bi_lokal'].append(data)
            #BI IMPORT: 4101010400
            bi_import_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4101010400')
            for bi_import_line in bi_import_lines:
                data = [
                    bi_import_line.purchase_id.name or '',
                    datetime.strptime(bi_import_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    bi_import_line.nostpb or '',
                    '',
                    bi_import_line.product_id.display_name or '',
                    bi_import_line.notes or '',
                    bi_import_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    bi_import_line.price_subtotal or 0
                ]
                gt_bi_import += bi_import_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['bi_import'].append(data)
            #PPH 22 DIBYR DMK: 1108020200
            pph22_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '1108020200')
            for pph22_line in pph22_lines:
                data = [
                    pph22_line.purchase_id.name or '',
                    datetime.strptime(pph22_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    pph22_line.nostpb or '',
                    '',
                    pph22_line.product_id.display_name or '',
                    pph22_line.notes or '',
                    pph22_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    pph22_line.price_subtotal or 0
                ]
                gt_pph22 += pph22_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['bi_import'].append(data)
            #PPH 23: 2108020300
            pph23_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '2108020300')
            for pph23_line in pph23_lines:
                data = [
                    pph23_line.purchase_id.name or '',
                    datetime.strptime(pph23_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    pph23_line.nostpb or '',
                    '',
                    pph23_line.product_id.display_name or '',
                    pph23_line.notes or '',
                    pph23_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    pph23_line.price_subtotal or 0
                ]
                gt_pph23 += pph23_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['pph23'].append(data)
            #PPH 23s: 1109080000
            pph23s_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '1109080000')
            for pph23s_line in pph23s_lines:
                data = [
                    pph23s_line.purchase_id.name or '',
                    datetime.strptime(pph23s_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    pph23s_line.nostpb or '',
                    '',
                    pph23s_line.product_id.display_name or '',
                    pph23s_line.notes or '',
                    pph23s_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    pph23s_line.price_subtotal or 0
                ]
                gt_pph23s += pph23s_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['pph23s'].append(data)
            #RETUR PEMBELIAN: 2106010000
            retur_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '2106010000' and l.price_subtotal < 0)
            for retur_line in retur_lines:
                data = [
                    retur_line.purchase_id.name or '',
                    datetime.strptime(retur_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    retur_line.nostpb or '',
                    '',
                    retur_line.product_id.display_name or '',
                    retur_line.notes or '',
                    retur_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    retur_line.price_subtotal or 0,
                    retur_line.invoice_line_tax_ids and retur_line.invoice_line_tax_ids[0].amount / 100 * retur_line.price_subtotal or 0
                ]
                gt_retur += retur_line.price_subtotal or 0
                gt_retur_ppn += retur_line.invoice_line_tax_ids and retur_line.invoice_line_tax_ids[0].amount / 100 * retur_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['retur_pembelian'].append(data)
            #PRICE ADJUSTMENT: 4203040000
            adj_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4203040000')
            for adj_line in adj_lines:
                data = [
                    adj_line.purchase_id.name or '',
                    datetime.strptime(adj_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    adj_line.nostpb or '',
                    '',
                    adj_line.product_id.display_name or '',
                    adj_line.notes or '',
                    adj_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    adj_line.price_subtotal or 0,
                    adj_line.invoice_line_tax_ids and adj_line.invoice_line_tax_ids[0].amount / 100 * adj_line.price_subtotal or 0
                ]
                gt_price_adj += adj_line.price_subtotal or 0
                gt_price_adj_ppn += adj_line.invoice_line_tax_ids and adj_line.invoice_line_tax_ids[0].amount / 100 * adj_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['price_adjustment'].append(data)
            #LAIN2: COA not in ALL
            other_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code not in \
                ['2106010000','4102051900','4102063100','4102061100','6405110000','4101010400','1108020200','2108020300','1109080000','2106010000','4203040000'])
            for other_line in other_lines:
                data = [
                    other_line.purchase_id.name or '',
                    datetime.strptime(other_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    other_line.nostpb or '',
                    '',
                    other_line.product_id.display_name or '',
                    other_line.notes or '',
                    other_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    other_line.price_subtotal or 0
                ]
                gt_lain += other_line.price_subtotal or 0
                compiled_data[partner]['bills'][bill_id]['lain'].append(data)
        grand_total = [
            gt_total,
            gt_biaya_service,
            gt_jasa_lain,
            gt_min_order_dpp,
            gt_min_order_dpp_ppn,
            gt_bi_lokal,
            gt_bi_import,
            gt_pph22,
            gt_pph23,
            gt_pph23s,
            gt_retur,
            gt_retur_ppn,
            gt_price_adj,
            gt_price_adj_ppn,
            gt_lain,
            gt_total + gt_biaya_service + gt_jasa_lain + gt_min_order_dpp + gt_min_order_dpp_ppn + gt_bi_lokal + \
                gt_bi_import + gt_pph22 + gt_pph23 + gt_pph23s + gt_retur + gt_retur_ppn + gt_price_adj + gt_price_adj_ppn + gt_lain
        ]
        datas['grand_total'] = grand_total
        datas['csv'] = compiled_data
        if self.report_type == 'rekap':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'bill.summary.xls',
                'nodestroy': True,
                'datas': datas,
            }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bill.xls',
            'nodestroy': True,
            'datas': datas,
        }

    #VALAS
    @api.multi
    def view_bill_valas_report(self):
        datas = {}        
        compiled_data = {}
        datas['ids'] = [self['id']]
        datas['company_name'] = self.company_id.name + ' - ' + self.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['partner_ids'] = self.partner_ids and ', '.join(map(str, [x.name for x in self['partner_ids']])) or 'All'
        datas['invoice_ids'] = self.invoice_ids and ', '.join(map(str, [x.number for x in self['invoice_ids']])) or 'All'

        if not self.invoice_ids:
            domain = [
                ('date_invoice', '>=', self.date_from),
                ('date_invoice', '<=', self.date_to),
                ('state', 'not in', ('cancel','draft')),
                ('currency_id', '=', self.currency_id.id),
                ('type', '=', 'in_invoice')
            ]
            if self.partner_ids:
                domain.append(('partner_id', 'in', self.partner_ids.ids))
        else:
            domain = [
                ('id', 'in', self.invoice_ids.ids)
            ]
        bills = self.env['account.invoice'].search(domain, order='date_invoice')
        gt_total_valas = gt_biaya_service_valas = gt_jasa_lain_valas = gt_min_order_dpp_valas = gt_min_order_dpp_ppn_valas = gt_bi_lokal_valas = gt_bi_import_valas = \
            gt_pph22_valas = gt_pph23_valas = gt_pph23s_valas = gt_retur_valas = gt_retur_ppn_valas = gt_price_adj_valas = gt_price_adj_ppn_valas = gt_lain_valas = gt_total_dibayar_valas = 0        
        gt_total = gt_biaya_service = gt_jasa_lain = gt_min_order_dpp = gt_min_order_dpp_ppn = gt_bi_lokal = gt_bi_import = \
            gt_pph22 = gt_pph23 = gt_pph23s = gt_retur = gt_retur_ppn = gt_price_adj = gt_price_adj_ppn = gt_lain = gt_total_dibayar = 0
        for bill in bills:
            if not bill.invoice_line_ids:
                continue
            partner = bill.partner_id.name or 'Undefined'
            bill_id = bill.id
            if not compiled_data.get(partner):
                compiled_data[partner] = {
                    'bills' : {}
                }
            if not compiled_data[partner]['bills'].get(bill_id):
                compiled_data[partner]['bills'][bill_id] = {
                    'number': bill.number,
                    'partner': bill.partner_id.name,
                    'account': '%s %s' % (bill.account_id.code, bill.account_id.name),
                    'kb': bill.nobukti_kontrabon.name or '',
                    'grir': [],
                    'biaya_service': [],
                    'jasa_lain': [],
                    'min_order_qty': [],
                    'bi_lokal': [],
                    'bi_import': [],
                    'pph22': [],
                    'pph23': [],
                    'pph23s': [],
                    'retur_pembelian': [],
                    'price_adjustment': [],
                    'lain': [],
                }
            
            #GR/IR DPP: 2106010000 PPN: 1108010100
            grir_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '2106010000' and l.price_subtotal > 0)
            for grir_line in grir_lines:
                if grir_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = grir_line.rate_kurs_line
                data = [
                    grir_line.purchase_id.name,
                    datetime.strptime(grir_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    grir_line.nostpb,
                    self._get_stpb_date(grir_line.nostpb) if grir_line.nostpb else '',
                    grir_line.product_id.display_name or '',
                    grir_line.notes or '',
                    grir_line.invoice_id.reference or '',
                    grir_line.quantity,
                    grir_line.uom_id.name,
                    grir_line.price_unit,
                    bill.currency_id.name,
                    rate_kurs_line,
                    #GR/IR
                    grir_line.price_subtotal,
                    rate_kurs_line * grir_line.price_subtotal,
                ]
                gt_total_valas += grir_line.price_subtotal
                gt_total += rate_kurs_line * grir_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['grir'].append(data)
            #BIAYA SERVICE KENDARAAN: 4102051900
            biaya_service_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4102051900')
            for biaya_service_line in biaya_service_lines:
                if biaya_service_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = biaya_service_line.rate_kurs_line
                data = [
                    biaya_service_line.purchase_id.name or '',
                    datetime.strptime(biaya_service_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    biaya_service_line.nostpb or '',
                    '',
                    biaya_service_line.product_id.display_name or '',
                    biaya_service_line.notes or '',
                    biaya_service_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    biaya_service_line.price_subtotal or 0,
                    rate_kurs_line * biaya_service_line.price_subtotal or 0
                ]
                gt_biaya_service_valas += biaya_service_line.price_subtotal
                gt_biaya_service += rate_kurs_line * biaya_service_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['biaya_service'].append(data)
            # #JASA LAINNYA: 4102063100
            jasa_lain_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4102063100')
            for jasa_lain_line in jasa_lain_lines:
                if jasa_lain_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = jasa_lain_line.rate_kurs_line
                data = [
                    jasa_lain_line.purchase_id.name or '',
                    datetime.strptime(jasa_lain_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    jasa_lain_line.nostpb or '',
                    '',
                    jasa_lain_line.product_id.display_name or '',
                    jasa_lain_line.notes or '',
                    jasa_lain_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    jasa_lain_line.price_subtotal or 0,
                    rate_kurs_line * jasa_lain_line.price_subtotal or 0
                ]
                gt_jasa_lain_valas += jasa_lain_line.price_subtotal
                gt_jasa_lain += rate_kurs_line * jasa_lain_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['jasa_lain'].append(data)
            # #MIN ORDER QTY / SURCHAGE: 4102061100
            min_order_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4102061100')
            for min_order_line in min_order_lines:
                if min_order_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = min_order_line.rate_kurs_line
                data = [
                    min_order_line.purchase_id.name or '',
                    datetime.strptime(min_order_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    min_order_line.nostpb or '',
                    '',
                    min_order_line.product_id.display_name or '',
                    min_order_line.notes or '',
                    min_order_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    min_order_line.price_subtotal or 0,
                    rate_kurs_line * min_order_line.price_subtotal or 0
                ]
                gt_min_order_dpp_valas += min_order_line.price_subtotal
                gt_min_order_dpp += rate_kurs_line * min_order_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['min_order_qty'].append(data)
            #BI LOKAL: 6405110000
            bi_local_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '6405110000')
            for bi_local_line in bi_local_lines:
                if bi_local_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = bi_local_line.rate_kurs_line
                data = [
                    bi_local_line.purchase_id.name or '',
                    datetime.strptime(bi_local_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    bi_local_line.nostpb or '',
                    '',
                    bi_local_line.product_id.display_name or '',
                    bi_local_line.notes or '',
                    bi_local_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    bi_local_line.price_subtotal or 0,
                    rate_kurs_line * bi_local_line.price_subtotal or 0
                ]
                gt_bi_lokal_valas += bi_local_line.price_subtotal
                gt_bi_lokal += rate_kurs_line * bi_local_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['bi_lokal'].append(data)
            # #BI IMPORT: 4101010400
            bi_import_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4101010400')
            for bi_import_line in bi_import_lines:
                if bi_import_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = bi_import_line.rate_kurs_line
                data = [
                    bi_import_line.purchase_id.name or '',
                    datetime.strptime(bi_import_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    bi_import_line.nostpb or '',
                    '',
                    bi_import_line.product_id.display_name or '',
                    bi_import_line.notes or '',
                    bi_import_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    #BI LOKAL
                    '',
                    '',
                    bi_import_line.price_subtotal or 0,
                    rate_kurs_line * bi_import_line.price_subtotal or 0
                ]
                gt_bi_import_valas += bi_import_line.price_subtotal
                gt_bi_import += rate_kurs_line * bi_import_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['bi_import'].append(data)
            # #PPH 22 DIBYR DMK: 1108020200
            pph22_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '1108020200')
            for pph22_line in pph22_lines:
                if pph22_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = pph22_line.rate_kurs_line
                data = [
                    pph22_line.purchase_id.name or '',
                    datetime.strptime(pph22_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    pph22_line.nostpb or '',
                    '',
                    pph22_line.product_id.display_name or '',
                    pph22_line.notes or '',
                    pph22_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    #BI LOKAL
                    '',
                    '',
                    #BI IMPORT
                    '',
                    '',
                    pph22_line.price_subtotal or 0,
                    rate_kurs_line * pph22_line.price_subtotal or 0
                ]
                gt_pph22_valas += pph22_line.price_subtotal
                gt_pph22 += rate_kurs_line * pph22_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['bi_import'].append(data)
            # #PPH 23: 2108020300
            pph23_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '2108020300')
            for pph23_line in pph23_lines:
                if pph23_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = pph23_line.rate_kurs_line
                data = [
                    pph23_line.purchase_id.name or '',
                    datetime.strptime(pph23_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    pph23_line.nostpb or '',
                    '',
                    pph23_line.product_id.display_name or '',
                    pph23_line.notes or '',
                    pph23_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    #BI LOKAL
                    '',
                    '',
                    #BI IMPORT
                    '',
                    '',
                    #PPH22
                    '',
                    '',
                    pph23_line.price_subtotal or 0,
                    rate_kurs_line * pph23_line.price_subtotal or 0
                ]
                gt_pph23_valas += pph23_line.price_subtotal
                gt_pph23 += rate_kurs_line * pph23_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['pph23'].append(data)
            # #PPH 23s: 1109080000
            pph23s_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '1109080000')
            for pph23s_line in pph23s_lines:
                if pph23s_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = pph23s_line.rate_kurs_line
                data = [
                    pph23s_line.purchase_id.name or '',
                    datetime.strptime(pph23s_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    pph23s_line.nostpb or '',
                    '',
                    pph23s_line.product_id.display_name or '',
                    pph23s_line.notes or '',
                    pph23s_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    #BI LOKAL
                    '',
                    '',
                    #BI IMPORT
                    '',
                    '',
                    #PPH22
                    '',
                    '',
                    #PPH23
                    '',
                    '',
                    pph23s_line.price_subtotal or 0,
                    rate_kurs_line * pph23s_line.price_subtotal or 0
                ]
                gt_pph23s_valas += pph23s_line.price_subtotal
                gt_pph23s += rate_kurs_line * pph23s_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['pph23s'].append(data)
            # #RETUR PEMBELIAN: 2106010000
            retur_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '2106010000' and l.price_subtotal < 0)
            for retur_line in retur_lines:
                if retur_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = retur_line.rate_kurs_line
                data = [
                    retur_line.purchase_id.name or '',
                    datetime.strptime(retur_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    retur_line.nostpb or '',
                    '',
                    retur_line.product_id.display_name or '',
                    retur_line.notes or '',
                    retur_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    #BI LOKAL
                    '',
                    '',
                    #BI IMPORT
                    '',
                    '',
                    #PPH22
                    '',
                    '',
                    #PPH23
                    '',
                    '',
                    #PPH23s
                    '',
                    '',
                    retur_line.price_subtotal or 0,
                    rate_kurs_line * retur_line.price_subtotal or 0
                ]
                gt_retur_valas += retur_line.price_subtotal
                gt_retur += rate_kurs_line * retur_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['retur_pembelian'].append(data)
            # #PRICE ADJUSTMENT: 4203040000
            adj_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code == '4203040000')
            for adj_line in adj_lines:
                if adj_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = adj_line.rate_kurs_line
                data = [
                    adj_line.purchase_id.name or '',
                    datetime.strptime(adj_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    adj_line.nostpb or '',
                    '',
                    adj_line.product_id.display_name or '',
                    adj_line.notes or '',
                    adj_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    #BI LOKAL
                    '',
                    '',
                    #BI IMPORT
                    '',
                    '',
                    #PPH22
                    '',
                    '',
                    #PPH23
                    '',
                    '',
                    #PPH23s
                    '',
                    '',
                    #RETUR
                    '',
                    '',
                    adj_line.price_subtotal or 0,
                    rate_kurs_line * adj_line.price_subtotal or 0,
                ]
                gt_price_adj_valas += adj_line.price_subtotal
                gt_price_adj += rate_kurs_line * adj_line.price_subtotal
                compiled_data[partner]['bills'][bill_id]['price_adjustment'].append(data)
            # #LAIN2: COA not in ALL
            other_lines = bill.invoice_line_ids.filtered(lambda l: l.account_id.code not in \
                ['2106010000','4102051900','4102063100','4102061100','6405110000','4101010400','1108020200','2108020300','1109080000','2106010000','4203040000'])
            for other_line in other_lines:
                if other_line.rate_kurs_line <= 0:
                    rate_kurs_line = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) / bill.amount_total
                else:
                    rate_kurs_line = other_line.rate_kurs_line
                data = [
                    other_line.purchase_id.name or '',
                    datetime.strptime(other_line.invoice_id.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    other_line.nostpb or '',
                    '',
                    other_line.product_id.display_name or '',
                    other_line.notes or '',
                    other_line.invoice_id.reference or '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    #GRIR
                    '',
                    '',
                    #SERVICE LAIN
                    '',
                    '',
                    #JASA LAIN
                    '',
                    '',
                    #MIN ORDER
                    '',
                    '',
                    #BI LOKAL
                    '',
                    '',
                    #BI IMPORT
                    '',
                    '',
                    #PPH22
                    '',
                    '',
                    #PPH23
                    '',
                    '',
                    #PPH23s
                    '',
                    '',
                    #RETUR
                    '',
                    '',
                    #ADJ
                    '',
                    '',
                    other_line.price_subtotal or 0,
                    rate_kurs_line * other_line.price_subtotal or 0
                ]
                gt_lain_valas += other_line.price_subtotal
                gt_lain += rate_kurs_line * other_line.price_subtotal 
                compiled_data[partner]['bills'][bill_id]['lain'].append(data)
        
        grand_total = [
            gt_total_valas,
            gt_total,
            gt_biaya_service_valas,
            gt_biaya_service,
            gt_jasa_lain_valas,
            gt_jasa_lain,
            gt_min_order_dpp_valas,
            gt_min_order_dpp,
            gt_bi_lokal_valas,
            gt_bi_lokal,
            gt_bi_import_valas,
            gt_bi_import,
            gt_pph22_valas,
            gt_pph22,
            gt_pph23_valas,
            gt_pph23,
            gt_pph23s_valas,
            gt_pph23s,
            gt_retur_valas,
            gt_retur,
            gt_price_adj_valas,
            gt_price_adj,
            gt_lain_valas,
            gt_lain,
            gt_total_valas + gt_biaya_service_valas + gt_jasa_lain_valas + gt_min_order_dpp_valas + gt_bi_lokal_valas + \
                gt_bi_import_valas + gt_pph22_valas + gt_pph23_valas + gt_pph23s_valas + gt_retur_valas + gt_price_adj_valas + gt_lain_valas,
                
            gt_total + gt_biaya_service + gt_jasa_lain + gt_min_order_dpp + gt_bi_lokal + \
                gt_bi_import + gt_pph22 + gt_pph23 + gt_pph23s + gt_retur + gt_price_adj + gt_lain
        ]
        datas['grand_total'] = grand_total
        datas['csv'] = compiled_data
        if self.report_type == 'rekap':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'bill.valas.summary.xls',
                'nodestroy': True,
                'datas': datas,
            }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bill.valas.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
