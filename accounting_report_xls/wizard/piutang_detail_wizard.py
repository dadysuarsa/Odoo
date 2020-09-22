from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError


class PiutangDetailReportWizard(models.TransientModel):
    _name = 'piutang.detail.report.wizard'
    
    @api.multi
    def get_first_date(self):
        current_date = date.today()
        return date(current_date.year, current_date.month, 1)

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    date_from = fields.Date('Start Date', default=get_first_date)
    date_to = fields.Date('End Date', default=date.today())
    partner_ids = fields.Many2many('res.partner', string='Partner(s)')
    type = fields.Selection([
        ('idr', 'IDR'),
        ('valas', 'VALAS')
    ], string='Type', default='idr')
    currency_id = fields.Many2one('res.currency', string='Currency')
    report_type = fields.Selection([
        ('rekap', 'Rekap'),
        ('detail', 'Detail'),
    ], string='Report Type', default='rekap')
    internal = fields.Boolean('Internal', default=False)
    
    @api.onchange('type')
    def change_type(self):
        if self.type == 'idr':
            self.currency_id = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1).id
        else:
            self.currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).id
    
    @api.multi
    def view_piutang_detail_report(self):
        if self.type == 'idr':
            return self.view_piutang_detail_idr_report()
        else:
            return self.view_piutang_detail_valas_report()
     
    @api.multi
    def view_piutang_detail_idr_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = 'All'
        datas['partner_ids'] = 'All'
        datas['report_type'] = 'Rekap' and self.report_type == 'rekap' or 'Detail'
        
        compiled_data = {}        
        if self.partner_ids:
            datas['partner_ids'] = self.partner_ids and ', '.join(map(str, [x.name for x in self['partner_ids']])) or 'All'
        
        domain = [
            ('type', '=', 'out_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date_invoice', '<=', self.date_to),
            ('currency_id', '=', self.company_id.currency_id.id)
        ]        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        invoices = self.env['account.invoice'].search(domain, order='date_invoice')
        
        gt_saldo_awal = gt_penjualan = gt_bank = gt_retur = gt_klaim = gt_komisi = gt_bank_charges = gt_potongan = gt_others = gt_pembulatan = gt_saldo_ahir = 0
        
        compiled_data = {}
        for invoice in invoices:
            if not invoice.invoice_line_ids:
                continue
            # Remove invoice paid and payment date before date from
            if invoice.state == 'paid' and invoice.payment_move_line_ids.sorted(key=lambda l: l.date)[-1].date < self.date_from:
                continue
            partner = invoice.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'invoices' : {} }
            if not compiled_data[partner]['invoices'].get(invoice.id):
                compiled_data[partner]['invoices'][invoice.id] = {'saldo_awal': 0, 'invoice_info': [], 'payments': [], 'saldo_ahir': 0}
                
            pelunasan = payment_banks_before_amount = payment_returs_before_amount = payment_klaim_before_amount = \
                payment_komisi_before_amount = payment_bank_charges_before_amount = payment_potongan_before_amount = \
                payment_others_before_amount = payment_pembulatan_before_amount = 0

            # PAYMENT BANK & CASH
            banks = []
            payment_banks = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank', 'cash'] and self.date_from <= l.date <= self.date_to)
            payment_banks_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank', 'cash'] and l.date < self.date_from)
            for payment in payment_banks:
                payment_amount = abs(payment.balance)
                data = [
                    payment.statement_id.mutasi_bank_id.name if payment.journal_id.type == 'bank' else payment.statement_id.name,
                    payment.move_id.ref if payment.journal_id.type == 'bank' else payment.move_id.name,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_bank += payment_amount
                banks.append(data)
            for payment in payment_banks_before:
                payment_amount = abs(payment.balance)
                payment_banks_before_amount += payment_amount
            
            # RETUR
            returs = []
            payment_returs = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['RETUR'] and self.date_from <= l.date <= self.date_to)
            payment_returs_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['RETUR'] and l.date < self.date_from)
            for payment in payment_returs:
                payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_retur += payment_amount
                returs.append(data)
            for payment in payment_returs_before:
                payment_amount = abs(payment.balance)
                payment_returs_before_amount += payment_amount
            
            # KLAIM
            klaim = []
            payment_klaim = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KLAIM'] and self.date_from <= l.date <= self.date_to)
            payment_klaim_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KLAIM'] and l.date < self.date_from)
            for payment in payment_klaim:
                payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    # RETUR
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_klaim += payment_amount
                klaim.append(data)
            for payment in payment_klaim_before:
                payment_amount = abs(payment.balance)
                payment_klaim_before_amount += payment_amount
            
            # BANK CHARGE
            bank_charges = []
            payment_bank_charges = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['5103030000', '7302020000', '7302020100', '7302020200'] and self.date_from <= l.date <= self.date_to)
            payment_bank_charges_before = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['5103030000', '7302020000', '7302020100', '7302020200'] and l.date < self.date_from)
            for payment in payment_klaim:
                payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    # RETUR
                    '',
                    # KLAIM
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_bank_charges += payment_amount
                bank_charges.append(data)
            for payment in payment_bank_charges_before:
                payment_amount = abs(payment.balance)
                payment_bank_charges_before_amount += payment_amount
            
            # KOMISI
            komisi = []
            payment_komisi = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['PPH23', 'KME'] and self.date_from <= l.date <= self.date_to)
            payment_komisi_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['PPH23', 'KME'] and l.date < self.date_from)
            for payment in payment_komisi:
                payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    # RETUR
                    '',
                    # KLAIM
                    '',
                    # BANK CHARGE
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_komisi += payment_amount
                komisi.append(data)
            for payment in payment_komisi_before:
                payment_amount = abs(payment.balance)
                payment_komisi_before_amount += payment_amount
            
            # POTONGAN
            potongan = []
            payment_potongan = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['POT'] and self.date_from <= l.date <= self.date_to)
            payment_potongan_before = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['POT'] and l.date < self.date_from)
            for payment in payment_potongan:
                payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    # RETUR
                    '',
                    # KLAIM
                    '',
                    # BANK CHARGE
                    '',
                    # KOMISI
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_potongan += payment_amount
                potongan.append(data)
            for payment in payment_potongan_before:
                payment_amount = abs(payment.balance)
                payment_potongan_before_amount += payment_amount
            
            # LAIN => RECLASS, KOMPENSASI
            others = []
            preclass = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['EUMAR', 'LUMAR'] and self.date_from <= l.date <= self.date_to)
            preclass_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['EUMAR', 'LUMAR'] and l.date < self.date_from)
            pkompensasi = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KPE', 'KPL'] and self.date_from <= l.date <= self.date_to)
            pkompensasi_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KPE', 'KPL'] and l.date < self.date_from)
            pjmar = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['JMAR'] and self.date_from <= l.date <= self.date_to)
            pjmar_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['JMAR'] and l.date < self.date_from)
            
            payment_others = preclass + pkompensasi + pjmar
            payment_others_before = preclass_before + pkompensasi_before + pjmar_before
            for payment in payment_others:
                payment_amount = abs(payment.balance)
                #PEMBAYARAN GABUNG
                if payment.journal_id.code == 'JMAR':
                    for pay in payment.full_reconcile_id.reconciled_line_ids.filtered(lambda l: l.move_id.name == invoice.number):
                        payment_amount = abs(pay.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    # RETUR
                    '',
                    # KLAIM
                    '',
                    # BANK CHARGE
                    '',
                    # KOMISI
                    '',
                    # POTONGAN
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_others += payment_amount
                others.append(data)
            for payment in payment_others_before:
                payment_amount = abs(payment.balance)
                payment_others_before_amount += payment_amount
            
            # PEMBULATAN
            pembulatan = []
            payment_pembulatan = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000', '7302040000'] and self.date_from <= l.date <= self.date_to)
            payment_pembulatan_before = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000', '7302040000'] and l.date < self.date_from)
            for payment in payment_pembulatan:
                payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    # RETUR
                    '',
                    # KLAIM
                    '',
                    # BANK CHARGE
                    '',
                    # KOMISI
                    '',
                    # POTONGAN
                    '',
                    # OTHER
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_pembulatan += payment_amount
                pembulatan.append(data)
            for payment in payment_pembulatan_before:
                payment_amount = abs(payment.balance)
                payment_pembulatan_before_amount += payment_amount
            
            # DATA PAYMENTS
            payments = [
                banks,
                returs,
                klaim,
                bank_charges,
                komisi,
                potongan,
                others,
                pembulatan
            ]
            total_payment_before_date_from = payment_banks_before_amount + payment_returs_before_amount + payment_klaim_before_amount + payment_bank_charges_before_amount + \
                payment_komisi_before_amount + payment_potongan_before_amount + payment_others_before_amount + payment_pembulatan_before_amount
                
            saldo_awal = invoice.amount_total - total_payment_before_date_from if invoice.date_invoice < self.date_from else 0            
            penjualan = invoice.amount_total if self.date_from <= invoice.date_invoice <= self.date_to else 0
            
            saldo_ahir = saldo_awal + penjualan - pelunasan
            invoice_info = [
                invoice.partner_id.name,
                invoice.account_id.name,
                datetime.strptime(invoice.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                invoice.number,
                saldo_awal,
                penjualan
            ]
            
            gt_saldo_awal += saldo_awal
            gt_penjualan += penjualan
            gt_saldo_ahir += saldo_ahir
            compiled_data[partner]['invoices'][invoice.id]['saldo_awal'] = saldo_awal
            compiled_data[partner]['invoices'][invoice.id]['saldo_ahir'] = saldo_ahir
            compiled_data[partner]['invoices'][invoice.id]['invoice_info'].append(invoice_info)
            compiled_data[partner]['invoices'][invoice.id]['payments'].append(payments)
        
        grand_total = [
            gt_saldo_awal,
            gt_penjualan,
            '',
            '',
            '',
            gt_bank,
            gt_retur,
            gt_klaim,
            gt_bank_charges,
            gt_komisi,
            gt_potongan,
            gt_others,
            gt_pembulatan,
            gt_saldo_ahir
        ]
            
        datas['csv'] = compiled_data
        datas['grand_total'] = grand_total
        if self.internal:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'piutang.idr.xls',
                'nodestroy': True,
                'datas': datas,
            }
        else:
            if self.report_type == 'rekap':
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'piutang.summary.idr.xls',
                    'nodestroy': True,
                    'datas': datas,
                }
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'piutang.detail.idr.xls',
                'nodestroy': True,
                'datas': datas,
            }
            
    ############################## VALAS ##############################################################    
    @api.multi
    def view_piutang_detail_valas_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['company_name'] = self.company_id.name + ' - ' + self.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = 'All'
        datas['partner_ids'] = 'All'
        datas['partner_ids'] = self.partner_ids and ', '.join(map(str, [x.name for x in self['partner_ids']])) or 'All'
        datas['valas'] = self.currency_id.name
        datas['report_type'] = 'Rekap' and self.report_type == 'rekap' or 'Detail'
        
        # KURS
        month = datetime.strptime(self.date_from, '%Y-%m-%d').month
        bulan = month if month >= 10 else '0%s' % (month)
        tahun = datetime.strptime(self.date_from, '%Y-%m-%d').year
        domain_kurs = [
            ('bulan', '=', bulan),
            ('tahun_id.name', '=', tahun),
            ('currency_id', '=', self.currency_id.id)
        ]
        kurs = self.env['master.kurs.bi'].search(domain_kurs, limit=1)
        if not kurs:
            raise UserError(_('Master data kurs transaksi berjalan tidak ditemukan !'))
        datas['kurs_awal'] = kurs.kurs_awal
        datas['kurs_ahir'] = kurs.kurs_akhir
        
        compiled_data = {}
        domain = [
            ('type', '=', 'out_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date_invoice', '<=', self.date_to),
            ('currency_id', '=', self.currency_id.id)
        ]        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
            
        gt_saldo_awal_valas = gt_penjualan_valas = gt_bank_valas = gt_returs_valas = gt_klaim_valas = gt_bank_charges_valas = gt_komisi_valas = \
            gt_potongan_valas = gt_others_valas = gt_pembulatan_valas = gt_total_valas = gt_saldo_ahir_valas = 0
        gt_saldo_awal_idr = gt_penjualan_idr = gt_bank_idr = gt_returs_idr = gt_klaim_idr = gt_bank_charges_idr = gt_komisi_idr = \
            gt_potongan_idr = gt_others_idr = gt_pembulatan_idr = gt_total_idr = gt_selisih_idr = gt_saldo_ahir_idr = 0

        invoices = self.env['account.invoice'].search(domain, order='date_invoice')
        compiled_data = {}
        for invoice in invoices:
            if not invoice.invoice_line_ids:
                continue
            # Remove invoice paid and payment date before date from
            if invoice.state == 'paid' and (invoice.payment_move_line_ids and invoice.payment_move_line_ids.sorted(key=lambda l: l.date)[-1].date < self.date_from or False):
                continue
            partner = invoice.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'invoices' : {} }
            if not compiled_data[partner]['invoices'].get(invoice.id):
                compiled_data[partner]['invoices'][invoice.id] = {
                    'saldo_awal': 0, 'invoice_info': [], 'payments': [],
                    'total_pelunasan_valas': 0, 'total_pelunasan_idr': 0,
                    'saldo_ahir_valas': 0, 'saldo_ahir_idr': 0
                }
            
            pelunasan_valas = pelunasan_idr = payment_banks_before_valas_amount = payment_banks_before_idr_amount = payment_returs_before_valas_amount = payment_returs_before_idr_amount = \
                payment_klaim_before_valas_amount = payment_klaim_before_idr_amount = payment_bank_charges_before_valas_amount = payment_bank_charges_before_idr_amount = \
                payment_komisi_before_valas_amount = payment_komisi_before_idr_amount = payment_potongan_before_valas_amount = payment_potongan_before_idr_amount = \
                payment_others_before_valas_amount = payment_others_before_idr_amount = payment_pembulatan_before_valas_amount = payment_pembulatan_before_idr_amount = 0
                
            # PAYMENT BANK
            banks = []
            payment_banks = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank', 'cash'] and self.date_from <= l.date <= self.date_to)
            payment_banks_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank', 'cash'] and l.date < self.date_from)
            for payment in payment_banks:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.statement_id.mutasi_bank_id.name if payment.journal_id.type == 'bank' else payment.statement_id.name,
                    payment.move_id.ref if payment.journal_id.type == 'bank' else payment.move_id.name,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr
                gt_bank_valas += payment_amount_currency
                gt_bank_idr += payment_amount_idr
                banks.append(data)
            for payment in payment_banks_before:
                payment_banks_before_valas_amount += abs(payment.amount_currency)
                payment_banks_before_idr_amount += abs(payment.balance)

            # PAYMENT RETURS
            returs = []
            payment_returs = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['RETUR'] and self.date_from <= l.date <= self.date_to)
            payment_returs_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['RETUR'] and l.date < self.date_from)
            for payment in payment_returs:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr
                gt_returs_valas += payment_amount_currency
                gt_returs_idr += payment_amount_idr
                returs.append(data)
            for payment in payment_returs_before:
                payment_returs_before_valas_amount += abs(payment.amount_currency)
                payment_returs_before_idr_amount += abs(payment.balance)

            # PAYMENT KLAIM
            klaim = []
            payment_klaim = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KLAIM'] and self.date_from <= l.date <= self.date_to)
            payment_klaim_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KLAIM'] and l.date < self.date_from)
            for payment in payment_klaim:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    '',
                    # RETUR
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr
                gt_klaim_valas += payment_amount_currency
                gt_klaim_idr += payment_amount_idr
                klaim.append(data)
            for payment in payment_klaim_before:
                payment_klaim_before_valas_amount += abs(payment.amount_currency)
                payment_klaim_before_idr_amount += abs(payment.balance)

            # BANK CHARGE
            bank_charges = []
            payment_bank_charges = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['5103030000', '7302020000', '7302020100', '7302020200'] and self.date_from <= l.date <= self.date_to)
            payment_bank_charges_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['5103030000', '7302020000', '7302020100', '7302020200'] and l.date < self.date_from)
            for payment in payment_bank_charges:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    '',
                    # RETUR
                    '',
                    '',
                    # KLAIM
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr                
                gt_bank_charges_valas += payment_amount_currency
                gt_bank_charges_idr += payment_amount_idr
                bank_charges.append(data)
            for payment in payment_bank_charges_before:
                payment_bank_charges_before_valas_amount += abs(payment.amount_currency)
                payment_bank_charges_before_idr_amount += abs(payment.balance)

            # KOMISI
            komisi = []
            payment_komisi = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['PPH23', 'KME'] and self.date_from <= l.date <= self.date_to)
            payment_komisi_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['PPH23', 'KME'] and l.date < self.date_from)
            for payment in payment_komisi:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    '',
                    # RETUR
                    '',
                    '',
                    # KLAIM
                    '',
                    '',
                    # BANK CHARGES
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr                
                gt_komisi_valas += payment_amount_currency
                gt_komisi_idr += payment_amount_idr
                komisi.append(data)
            for payment in payment_komisi_before:
                payment_komisi_before_valas_amount += abs(payment.amount_currency)
                payment_komisi_before_idr_amount += abs(payment.balance)
            
            # POTONGAN
            potongan = []
            payment_potongan = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['POT'] and self.date_from <= l.date <= self.date_to)
            payment_potongan_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['POT'] and l.date < self.date_from)
            for payment in payment_potongan:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    '',
                    # RETUR
                    '',
                    '',
                    # KLAIM
                    '',
                    '',
                    # BANK CHARGES
                    '',
                    '',
                    # KOMISI
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr                
                gt_potongan_valas += payment_amount_currency
                gt_potongan_idr += payment_amount_idr
                potongan.append(data)
            for payment in payment_potongan_before:
                payment_potongan_before_valas_amount += abs(payment.amount_currency)
                payment_potongan_before_idr_amount += abs(payment.balance)
                
            # LAIN => RECLAS & KOMPENSASI
            others = []
            preclass = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['EUMAR', 'LUMAR'] and self.date_from <= l.date <= self.date_to)
            preclass_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['EUMAR', 'LUMAR'] and l.date < self.date_from)
            pkompensasi = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KPE', 'KPL'] and self.date_from <= l.date <= self.date_to)
            pkompensasi_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['KPE', 'KPL'] and l.date < self.date_from)
            pjmar = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['JMAR'] and self.date_from <= l.date <= self.date_to)
            pjmar_before = invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code.replace(" ","") in ['JMAR'] and l.date < self.date_from)
            
            payment_others = preclass + pkompensasi + pjmar
            payment_others_before = preclass_before + pkompensasi_before + pjmar_before
            for payment in payment_others:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                #PEMBAYARAN GABUNG
                if payment.journal_id.code == 'JMAR':
                    for pay in payment.full_reconcile_id.reconciled_line_ids.filtered(lambda l: l.move_id.name == invoice.number):
                        payment_amount_currency = abs(pay.amount_currency)
                        payment_amount_idr = abs(pay.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    '',
                    # RETUR
                    '',
                    '',
                    # KLAIM
                    '',
                    '',
                    # BANK CHARGES
                    '',
                    '',
                    # KOMISI
                    '',
                    '',
                    # POTONGAN
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr    
                gt_others_valas += payment_amount_currency
                gt_others_idr += payment_amount_idr
                others.append(data)
            for payment in payment_others_before:
                payment_others_before_valas_amount += abs(payment.amount_currency)
                payment_others_before_idr_amount += abs(payment.balance)
            
            # PEMBULATAN => COA BIAYA LAIN
            pembulatan = []
            payment_pembulatan = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000', '7302040000'] and self.date_from <= l.date <= self.date_to)
            payment_pembulatan_before = invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000', '7302040000'] and l.date < self.date_from)
            for payment in payment_pembulatan:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    # BANK
                    '',
                    '',
                    # RETUR
                    '',
                    '',
                    # KLAIM
                    '',
                    '',
                    # BANK CHARGES
                    '',
                    '',
                    # KOMISI
                    '',
                    '',
                    # POTONGAN
                    '',
                    '',
                    # OTHERS
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr                
                gt_pembulatan_valas += payment_amount_currency
                gt_pembulatan_idr += payment_amount_idr
                pembulatan.append(data)
            for payment in payment_pembulatan_before:
                payment_pembulatan_before_valas_amount += abs(payment.amount_currency)
                payment_pembulatan_before_idr_amount += abs(payment.balance)
            has_payment = False
            payments = [
                banks,
                returs,
                klaim,
                bank_charges,
                komisi,
                potongan,
                others,
                pembulatan
            ]
            
            total_payment_before_date_from_valas = payment_banks_before_valas_amount + payment_returs_before_valas_amount + payment_klaim_before_valas_amount + \
                payment_bank_charges_before_valas_amount + payment_komisi_before_valas_amount + payment_potongan_before_valas_amount + payment_others_before_valas_amount + payment_pembulatan_before_valas_amount

            saldo_awal_valas = invoice.amount_total - total_payment_before_date_from_valas if invoice.date_invoice < self.date_from else 0
            penjualan_valas = invoice.amount_total if self.date_from <= invoice.date_invoice <= self.date_to else 0
            if invoice.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'receivable'):
                penjualan_idr = abs(invoice.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'receivable')[0].balance) if self.date_from <= invoice.date_invoice <= self.date_to else 0
            else:
                penjualan_idr = 0
            saldo_ahir_valas = saldo_awal_valas + penjualan_valas - pelunasan_valas
            selisih_idr = (pelunasan_idr + (round(saldo_ahir_valas * datas['kurs_ahir'], 2))) - ((round(datas['kurs_awal'] * saldo_awal_valas, 2)) + penjualan_idr)

            invoice_info = [
                invoice.partner_id.name,
                invoice.account_id.name,
                datetime.strptime(invoice.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                invoice.number,
                datas['kurs_awal'] or 0,
                saldo_awal_valas or 0,
                round(datas['kurs_awal'] * saldo_awal_valas, 2),
                penjualan_valas,
                penjualan_idr
            ]

            compiled_data[partner]['invoices'][invoice.id]['invoice_info'].append(invoice_info)
            compiled_data[partner]['invoices'][invoice.id]['payments'].append(payments)
            compiled_data[partner]['invoices'][invoice.id]['total_pelunasan_valas'] = pelunasan_valas
            compiled_data[partner]['invoices'][invoice.id]['total_pelunasan_idr'] = pelunasan_idr
            compiled_data[partner]['invoices'][invoice.id]['total_selisih_idr'] = selisih_idr
            compiled_data[partner]['invoices'][invoice.id]['saldo_ahir_valas'] = saldo_ahir_valas
            compiled_data[partner]['invoices'][invoice.id]['saldo_ahir_idr'] = round(saldo_ahir_valas * datas['kurs_ahir'], 2)
            
            gt_saldo_awal_valas += saldo_awal_valas
            gt_saldo_awal_idr += round(datas['kurs_awal'] * saldo_awal_valas, 2)
            gt_penjualan_valas += penjualan_valas
            gt_penjualan_idr += penjualan_idr
            gt_total_valas += pelunasan_valas
            gt_total_idr += pelunasan_idr
            gt_selisih_idr += selisih_idr
            gt_saldo_ahir_valas += saldo_ahir_valas
            gt_saldo_ahir_idr += round(saldo_ahir_valas * datas['kurs_ahir'], 2)
        
        grand_total = [
            datas['kurs_awal'],
            gt_saldo_awal_valas,
            gt_saldo_awal_idr,
            gt_penjualan_valas,
            gt_penjualan_idr,
            '',
            '',
            '',
            gt_bank_valas,
            gt_bank_idr,
            gt_returs_valas,
            gt_returs_idr,
            gt_klaim_valas,
            gt_klaim_idr,
            gt_bank_charges_valas,
            gt_bank_charges_idr,
            gt_komisi_valas,
            gt_komisi_idr,
            gt_potongan_valas,
            gt_potongan_idr,
            gt_others_valas,
            gt_others_idr,
            gt_pembulatan_valas,
            gt_pembulatan_idr,
            gt_total_valas,
            gt_total_idr,
            gt_selisih_idr,
            gt_saldo_ahir_valas,
            gt_saldo_ahir_idr,
            datas['kurs_ahir']

        ]
            
        datas['csv'] = compiled_data
        datas['grand_total'] = grand_total
        if self.internal:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'piutang.valas.xls',
                'nodestroy': True,
                'datas': datas,
            }
        else:
            if self.report_type == 'rekap':
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'piutang.detail.valas.summary.xls',
                    'nodestroy': True,
                    'datas': datas,
                }
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'piutang.detail.valas.xls',
                'nodestroy': True,
                'datas': datas,
            }
    
