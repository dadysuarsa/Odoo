from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError

class PiutangReportWizard(models.TransientModel):
    _name = 'piutang.report.wizard'
    
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
    
    @api.onchange('type')
    def change_type(self):
        if self.type == 'idr':
            self.currency_id = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1).id
        else:
            self.currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).id
    
    @api.multi
    def view_piutang_report(self):
        if self.type == 'idr':
            return self.view_piutang_idr_report()
        else:
            return self.view_piutang_valas_report()
        
    @api.multi
    def get_payment_amount_idr(self, move, account_type, invoice_number):
        query = """
                select 
                    aml.debit - aml.credit as balance
                from 
                    account_move_line aml
                    left join
                        account_account aa on (aa.id = aml.account_id)
                    left join
                        account_move am on (am.id = aml.move_id)
                where
                    aml.company_id = %s and
                    aml.move_id = %s and
                    aa.internal_type = '%s' and
                    aml.name = '%s'
                    
        """ %  (self.company_id.id, move, account_type, invoice_number)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchone()
        if not data:
            query = """
                select 
                    aml.debit - aml.credit as balance
                from 
                    account_move_line aml
                    left join
                        account_account aa on (aa.id = aml.account_id)
                    left join
                        account_move am on (am.id = aml.move_id)
                where
                    aml.company_id = %s and
                    aml.move_id = %s and
                    aa.internal_type = '%s' and
                    aml.name like '%s'
                    
            """ %  (self.company_id.id, move, account_type, '%'+invoice_number+'%')
            self.sudo().env.cr.execute(query)
            data = self.sudo().env.cr.dictfetchone()
        return data and abs(data.get('balance')) or 0
    
    @api.multi
    def get_payment_amount_valas(self, move, account_type, invoice_number):
        query = """
                select 
                    aml.amount_currency as balance
                from 
                    account_move_line aml
                    left join
                        account_account aa on (aa.id = aml.account_id)
                    left join
                        account_move am on (am.id = aml.move_id)
                where
                    aml.company_id = %s and
                    aml.move_id = %s and
                    aa.internal_type = '%s' and
                    aml.name = '%s'
                    
        """ %  (self.company_id.id, move, account_type, invoice_number)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchone()
        if not data:
            query = """
                select 
                    aml.amount_currency as balance
                from 
                    account_move_line aml
                    left join
                        account_account aa on (aa.id = aml.account_id)
                    left join
                        account_move am on (am.id = aml.move_id)
                where
                    aml.company_id = %s and
                    aml.move_id = %s and
                    aa.internal_type = '%s' and
                    aml.name like '%s'
                    
            """ %  (self.company_id.id, move, account_type, '%'+invoice_number+'%')
            self.sudo().env.cr.execute(query)
            data = self.sudo().env.cr.dictfetchone()
        return data and abs(data.get('balance')) or 0
    
    @api.multi
    def view_piutang_idr_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = 'All'
        datas['partner_ids'] = self.partner_ids and ', '.join(map(str, [x.name for x in self['partner_ids']])) or 'All'
              
        domain = [
            ('type', '=', 'out_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date_invoice', '<=', self.date_to),
            ('currency_id.name', '=', 'IDR')
        ]        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        invoices = self.env['account.invoice'].search(domain, order='date_invoice')
        compiled_data = {}
        total_saldo_awal = total_penjualan = total_payment = total_retur = total_klaim = total_biaya_bank = total_komisi = total_biaya_lain = total_pembulatan = total_potongan = total_saldo_ahir = 0
        for invoice in invoices:
            partner = invoice.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'invoices' : []}
            #INVOICE PAYMENTS
            retur_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3200000000','3201000000','3201010000','3202000000','3202010000','3203000000','3203010000','3204000000','3204010000'] and l.date < self.date_from).mapped('balance')))
            klaim_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103010000','5104010000','5104830000','7301040000'] and l.date < self.date_from).mapped('balance')))
            biaya_bank_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103030000','7302020000','7302020100','7302020200'] and l.date < self.date_from).mapped('balance')))
            komisi_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['2109090100','2109110000','2109120000','5103020000','5104020000'] and l.date < self.date_from).mapped('balance')))
            biaya_lain = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000','7302040000'] and l.date < self.date_from).mapped('balance')))
            kompensasi_biaya_lain = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPL','KPE'] and l.date < self.date_from).mapped('balance')))
            pembayaran_reclass = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['EUMAR','LUMAR'] and l.date < self.date_from).mapped('balance')))
            pembulatan_amount = 0
            potongan_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3300000000','3301000000','3301010000','3302000000','3302010000','3303000000','3303010000','3304000000','3304010000','3305000000','3305010000'] and \
                    l.date < self.date_from).mapped('balance')))
            payment_amount = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and l.date < self.date_from).mapped('balance'))
            #multi payment
            if payment_amount > invoice.amount_total:
                payment_amount = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in \
                    ['bank','cash'] and l.name == invoice.number and l.date < self.date_from).mapped('balance')))
            total_invoice_payments = payment_amount + retur_amount + klaim_amount + biaya_bank_amount + komisi_amount + (biaya_lain + pembayaran_reclass + kompensasi_biaya_lain) + pembulatan_amount + potongan_amount
            
            #IDR
            retur_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3200000000','3201000000','3201010000','3202000000','3202010000','3203000000','3203010000','3204000000','3204010000'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            klaim_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103010000','5104010000','5104830000','7301040000'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            biaya_bank_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103030000','7302020000','7302020100','7302020200'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            komisi_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['2109090100','2109110000','2109120000','5103020000','5104020000'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            biaya_lain = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000','7302040000'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            kompensasi_biaya_lain = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPL','KPE'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            pembayaran_reclass = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['EUMAR','LUMAR'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            pembulatan_amount = 0
            potongan_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3300000000','3301000000','3301010000','3302000000','3302010000','3303000000','3303010000','3304000000','3304010000','3305000000','3305010000'] and \
                    self.date_from <= l.date <= self.date_to).mapped('balance')))
            payment_amount = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and self.date_from <= l.date <= self.date_to).mapped('balance'))
            #multi payment
            if payment_amount > invoice.amount_total:
                payment_amount = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in \
                    ['bank','cash'] and l.name == invoice.number and self.date_from <= l.date <= self.date_to).mapped('balance')))
                    
            other_payment_amount = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and l.date > self.date_to).mapped('balance'))
                        
            saldo_awal = invoice.amount_total - total_invoice_payments
            sa_awal = saldo_awal if invoice.date_invoice < self.date_from else 0
            penjualan = invoice.amount_total if self.date_from <= invoice.date_invoice <= self.date_to else 0
            data_invoice = [
                invoice.partner_id.name,
                invoice.number,
                invoice.date_invoice,
                #Saldo Awal
                sa_awal,
                #Penjualan
                penjualan,
                #Pembayaran bank + Cash
                payment_amount,
                #Retur
                retur_amount,
                #Klaim
                klaim_amount,
                #Biaya bank
                biaya_bank_amount,
                #Komisi
                komisi_amount,
                #Biaya lain
                biaya_lain + pembayaran_reclass + kompensasi_biaya_lain,
                #Pembulatan
                pembulatan_amount,                
                #Potongan
                potongan_amount,
                #Saldo Ahir
            ]
            #remove unnecesary line paid before date_from / transaksi berjalan
            if data_invoice[3] == 0 and data_invoice[4] == 0:
                continue
            compiled_data[partner]['invoices'].append(data_invoice)
            total_saldo_awal += saldo_awal if invoice.date_invoice < self.date_from else 0
            total_penjualan += penjualan
            total_payment += payment_amount
            total_retur += retur_amount
            total_klaim += klaim_amount
            total_biaya_bank += biaya_bank_amount
            total_komisi += komisi_amount
            total_biaya_lain += biaya_lain + pembayaran_reclass + kompensasi_biaya_lain
            total_pembulatan += pembulatan_amount
            total_potongan += potongan_amount
            total_saldo_ahir += sa_awal + penjualan - payment_amount - retur_amount - klaim_amount - biaya_bank_amount - komisi_amount - biaya_lain - pembayaran_reclass - kompensasi_biaya_lain - pembulatan_amount - potongan_amount
        
        grand_total = [
            total_saldo_awal,
            total_penjualan,
            total_payment,
            total_retur,
            total_klaim,
            total_biaya_bank,
            total_komisi,
            total_biaya_lain,
            total_pembulatan,
            total_potongan,
            total_saldo_ahir
        ]
        datas['grand_total'] = grand_total
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'piutang.idr.xls',
            'nodestroy': True,
            'datas': datas,
        }
            
            
    @api.multi
    def view_piutang_valas_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = 'All'
        datas['partner_ids'] = 'All'
        
        bulan = '0%s' %(datetime.strptime(self.date_from, '%Y-%m-%d').month)
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

        if self.partner_ids:
            datas['partner_ids'] = self.partner_ids and ', '.join(map(str, [x.name for x in self['partner_ids']])) or 'All'
        
        outstanding_domain = [
            ('type', '=', 'out_invoice'),
            ('state', 'not in', ['paid','cancel', 'draft']),
            ('date_invoice', '<', self.date_from),
            ('currency_id', '=', self.currency_id.id)
        ]        
        current_domain = [
            ('type', '=', 'out_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date_invoice', '<=', self.date_to),
            ('currency_id', '=', self.currency_id.id)
        ]        
        if self.partner_ids:
            outstanding_domain.append(('partner_id', 'in', self.partner_ids.ids))
            current_domain.append(('partner_id', 'in', self.partner_ids.ids))

        outstanding_invoices = self.env['account.invoice'].search(outstanding_domain, order='date_invoice')
        current_invoices = self.env['account.invoice'].search(current_domain, order='date_invoice')
        invoices = outstanding_invoices | current_invoices
        compiled_data = {}
        total_saldo_awal = total_penjualan = total_payment = total_retur = total_klaim = total_biaya_bank = total_komisi = total_biaya_lain = total_pembulatan = total_potongan = total_saldo_ahir = 0
        total_saldo_awal_valas = total_selisih_idr = total_penjualan_valas = total_payment_valas = total_retur_valas = total_klaim_valas = total_biaya_bank_valas = total_komisi_valas = total_biaya_lain_valas = total_pembulatan_valas = total_potongan_valas = total_saldo_ahir_valas = 0
        for invoice in invoices:
            partner = invoice.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'invoices' : []}
            
            #INVOICE PAYMENTS VALAS
            retur_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3200000000','3201000000','3201010000','3202000000','3202010000','3203000000','3203010000','3204000000','3204010000'] and l.date < self.date_from).mapped('amount_currency')))
            klaim_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103010000','5104010000','5104830000','7301040000'] and l.date < self.date_from).mapped('amount_currency')))
            biaya_bank_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103030000','7302020000','7302020100','7302020200'] and l.date < self.date_from).mapped('amount_currency')))
            komisi_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['2109090100','2109110000','2109120000','5103020000','5104020000'] and l.date < self.date_from and l.name[-len(invoice.number):]==invoice.number).mapped('amount_currency')))
            biaya_lain_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000','7302040000'] and l.date < self.date_from).mapped('amount_currency')))
            kompensasi_biaya_lain_valas = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPL','KPE'] and l.date < self.date_from).mapped('amount_currency')))
            pembayaran_reclass_valas = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['EUMAR','LUMAR'] and l.date < self.date_from).mapped('amount_currency')))

            pembulatan_amount_valas = 0
            potongan_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3300000000','3301000000','3301010000','3302000000','3302010000','3303000000','3303010000','3304000000','3304010000','3305000000','3305010000'] and \
                    l.date < self.date_from).mapped('amount_currency')))

            payment_amount_valas = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and l.date < self.date_from).mapped('amount_currency'))
            #multi payment
            if payment_amount_valas > invoice.amount_total:
                payment_amount_valas = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in \
                    ['bank','cash'] and l.name == invoice.number and l.date < self.date_from).mapped('amount_currency')))
            other_payment_amount_valas = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and l.date > self.date_to).mapped('amount_currency'))

            total_invoice_payments_valas = payment_amount_valas + retur_amount_valas + klaim_amount_valas + biaya_bank_amount_valas + komisi_amount_valas + (biaya_lain_valas + \
                kompensasi_biaya_lain_valas + pembayaran_reclass_valas) + pembulatan_amount_valas + potongan_amount_valas

            #IDR
            retur_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3200000000','3201000000','3201010000','3202000000','3202010000','3203000000','3203010000','3204000000','3204010000'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            klaim_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103010000','5104010000','5104830000','7301040000'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            biaya_bank_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103030000','7302020000','7302020100','7302020200'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            komisi_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['2109090100','2109110000','2109120000','5103020000','5104020000'] and self.date_from <= l.date <= self.date_to and l.name[-len(invoice.number):]==invoice.number).mapped('balance')))

            biaya_lain = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000','7302040000'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            pembayaran_reclass = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['EUMAR','LUMAR'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            kompensasi_biaya_lain = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPL','KPE'] and self.date_from <= l.date <= self.date_to).mapped('balance')))
            pembulatan_amount = 0

            potongan_amount = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3300000000','3301000000','3301010000','3302000000','3302010000','3303000000','3303010000','3304000000','3304010000','3305000000','3305010000'] and \
                    self.date_from <= l.date <= self.date_to).mapped('balance')))

            payment_amount = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and self.date_from <= l.date <= self.date_to).mapped('balance'))
            #multi payment
            if payment_amount > invoice.amount_total:
                payment_amount = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in \
                    ['bank','cash'] and l.name == invoice.number and self.date_from <= l.date <= self.date_to).mapped('balance')))

            other_payment_amount = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and l.date > self.date_to).mapped('balance'))
            
            if invoice.amount_total == 0:
                continue
            penjualan = invoice.move_id.mapped('line_ids')[0].balance if self.date_from <= invoice.date_invoice <= self.date_to else 0

            #VALAS
            retur_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3200000000','3201000000','3201010000','3202000000','3202010000','3203000000','3203010000','3204000000','3204010000'] and self.date_from <= l.date <= self.date_to).mapped('amount_currency')))
            klaim_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103010000','5104010000','5104830000','7301040000'] and self.date_from <= l.date <= self.date_to).mapped('amount_currency')))
            biaya_bank_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['5103030000','7302020000','7302020100','7302020200'] and self.date_from <= l.date <= self.date_to).mapped('amount_currency')))
            komisi_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in \
                ['2109090100','2109110000','2109120000','5103020000','5104020000'] and self.date_from <= l.date <= self.date_to and l.name[-len(invoice.number):]==invoice.number).mapped('amount_currency')))
            biaya_lain_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code in ['7302000000','7302040000'] and self.date_from <= l.date <= self.date_to).mapped('amount_currency')))
            kompensasi_biaya_lain_valas = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPL','KPE'] and self.date_from <= l.date <= self.date_to).mapped('amount_currency')))
            pembayaran_reclass_valas = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['EUMAR','LUMAR'] and self.date_from <= l.date <= self.date_to).mapped('amount_currency')))

            pembulatan_amount_valas = 0
            potongan_amount_valas = abs(sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.code \
                in ['3300000000','3301000000','3301010000','3302000000','3302010000','3303000000','3303010000','3304000000','3304010000','3305000000','3305010000'] and \
                    self.date_from <= l.date <= self.date_to).mapped('amount_currency')))

            payment_amount_valas = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and self.date_from <= l.date <= self.date_to).mapped('amount_currency'))
            #multi payment
            if payment_amount_valas > invoice.amount_total:
                payment_amount_valas = abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in \
                    ['bank','cash'] and l.name == invoice.number and self.date_from <= l.date <= self.date_to).mapped('amount_currency')))
            other_payment_amount_valas = sum(invoice.payment_move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type in ['liquidity'] and l.date > self.date_to).mapped('amount_currency'))

            # saldo_awal_valas = invoice.residual + payment_amount_valas + retur_amount_valas + klaim_amount_valas + biaya_bank_amount_valas + komisi_amount_valas + \
            #     biaya_lain_valas + pembayaran_reclass_valas + kompensasi_biaya_lain_valas + pembulatan_amount_valas + potongan_amount_valas + other_payment_amount_valas
            saldo_awal_valas = invoice.amount_total - total_invoice_payments_valas
            sa_valas = saldo_awal_valas if invoice.date_invoice < self.date_from else 0
            sa_idr = round(saldo_awal_valas * kurs.kurs_awal, 2) if invoice.date_invoice < self.date_from else 0
            penjualan_valas = invoice.amount_total if self.date_from <= invoice.date_invoice <= self.date_to else 0
            data_invoice = [
                invoice.partner_id.name,
                invoice.number,
                invoice.date_invoice,
                #Saldo Awal
                sa_valas,
                sa_idr,
                #Penjualan
                penjualan_valas,
                penjualan,
                #Pembayaran bank + Cash
                payment_amount_valas,
                payment_amount,
                #Retur
                retur_amount_valas,
                retur_amount,
                #Klaim
                klaim_amount_valas,
                klaim_amount,
                #Biaya bank
                biaya_bank_amount_valas,
                biaya_bank_amount,
                #Komisi
                komisi_amount_valas,
                komisi_amount,
                #Biaya lain
                biaya_lain_valas + kompensasi_biaya_lain_valas + pembayaran_reclass_valas,
                biaya_lain + kompensasi_biaya_lain + pembayaran_reclass,
                #Pembulatan
                pembulatan_amount_valas,
                pembulatan_amount,                
                #Potongan
                potongan_amount_valas,
                potongan_amount,
            ]
            #remove unnecesary line paid before date_from / transaksi berjalan
            if data_invoice[3] == 0 and data_invoice[4] == 0 and data_invoice[5] == 0 and data_invoice[6] == 0:
                continue
            compiled_data[partner]['invoices'].append(data_invoice)
            
            #GRAND TOTAL VALAS
            total_saldo_awal_valas += saldo_awal_valas if invoice.date_invoice < self.date_from else 0
            total_penjualan_valas += penjualan_valas
            total_payment_valas += payment_amount_valas
            total_retur_valas += retur_amount_valas
            total_klaim_valas += klaim_amount_valas
            total_biaya_bank_valas += biaya_bank_amount_valas
            total_komisi_valas += komisi_amount_valas
            total_biaya_lain_valas += biaya_lain_valas + kompensasi_biaya_lain_valas + pembayaran_reclass_valas
            total_pembulatan_valas += pembulatan_amount_valas
            total_potongan_valas += potongan_amount_valas
            total_saldo_ahir_valas += sa_valas + penjualan_valas - payment_amount_valas - retur_amount_valas - klaim_amount_valas - \
                biaya_bank_amount_valas - komisi_amount_valas - biaya_lain_valas - kompensasi_biaya_lain_valas - pembayaran_reclass_valas - pembulatan_amount_valas - potongan_amount_valas

            #GRAND TOTAL IDR
            total_saldo_awal += round(sa_idr, 2) if invoice.date_invoice < self.date_from else 0
            total_penjualan += penjualan
            total_payment += payment_amount
            total_retur += retur_amount
            total_klaim += klaim_amount
            total_biaya_bank += biaya_bank_amount
            total_komisi += komisi_amount
            total_biaya_lain += biaya_lain + kompensasi_biaya_lain + pembayaran_reclass
            total_pembulatan += pembulatan_amount
            total_potongan += potongan_amount
            # total_saldo_ahir += total_saldo_ahir_valas
            # total_selisih_idr += (total_saldo_awal + total_penjualan) - (total_payment+total_retur+total_klaim+total_biaya_bank+total_komisi+total_biaya_lain+total_pembulatan+total_potongan+total_saldo_ahir)

        total_saldo_ahir = total_saldo_ahir_valas * kurs.kurs_akhir
        grand_total = [
            total_saldo_awal_valas,
            total_saldo_awal,
            total_penjualan_valas,
            total_penjualan,
            total_payment_valas,
            total_payment,
            total_retur_valas,
            total_retur,
            total_klaim_valas,
            total_klaim,
            total_biaya_bank_valas,
            total_biaya_bank,
            total_komisi_valas,
            total_komisi,
            total_biaya_lain_valas,
            total_biaya_lain,
            total_pembulatan_valas,
            total_pembulatan,
            total_potongan_valas,
            total_potongan,
            (total_saldo_awal+total_penjualan)-(total_payment+total_retur+total_klaim+total_biaya_bank+total_komisi+total_biaya_lain+total_pembulatan+total_potongan+total_saldo_ahir),
            total_saldo_ahir_valas,
            total_saldo_ahir
        ]
        datas['grand_total'] = grand_total

        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'piutang.valas.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
