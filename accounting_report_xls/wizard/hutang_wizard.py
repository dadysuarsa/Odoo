from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError

class HutangReportWizard(models.TransientModel):
    _name = 'hutang.report.wizard'
    
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
    
    @api.onchange('type')
    def change_type(self):
        if self.type == 'idr':
            self.currency_id = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1).id
        else:
            self.currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).id
    
    @api.multi
    def view_hutang_report(self):
        if self.type == 'idr':
            return self.view_hutang_idr_report()
        else:
            return self.view_hutang_valas_report()
     
    @api.multi
    def view_hutang_idr_report(self):
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
            ('type', '=', 'in_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date_invoice', '<=', self.date_to),
            ('currency_id.name', '=', 'IDR')
        ]        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        bills = self.env['account.invoice'].search(domain, order='date_invoice')
        gt_saldo_awal = gt_penambahan = gt_bank = gt_kompensasi = gt_perantara = gt_reclass = gt_retur = gt_lain = gt_saldo_ahir = 0
        compiled_data = {}
        for bill in bills:
            if not bill.invoice_line_ids:
                continue
            #Remove invoice paid and payment date before date from
            if bill.state == 'paid' and bill.payment_move_line_ids.sorted(key=lambda l: l.date)[-1].date < self.date_from:
                continue
            partner = bill.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'bills' : {} }
            if not compiled_data[partner]['bills'].get(bill.id):
                compiled_data[partner]['bills'][bill.id] = {'saldo_awal': 0, 'bill_info': [], 'payments': [], 'saldo_ahir': 0}
            pelunasan = payment_banks_before_amount = payment_kompensasi_before_amount = payment_perantara_before_amount = \
                payment_reclass_before_amount = payment_retur_before_amount = payment_lain_before_amount = 0

            #PAYMENT BANK
            banks = []
            payment_banks = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank','cash'] and self.date_from <= l.date <= self.date_to)
            payment_banks_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank','cash'] and l.date < self.date_from)
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
            #PAYMENT KOMPENSASI
            kompensasi = []
            payment_kompensasi = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPE','KPL'] and self.date_from <= l.date <= self.date_to)
            payment_kompensasi_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPE','KPL'] and l.date < self.date_from)
            for payment in payment_kompensasi_before:
                payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_kompensasi += payment_amount
                kompensasi.append(data)
            for payment in payment_kompensasi_before:
                payment_amount = abs(payment.balance)
                payment_kompensasi_before_amount += payment_amount
            #PAYMENT PERANTARA
            perantara = []
            payment_perantara = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['PRLC','PRTB'] and self.date_from <= l.date <= self.date_to)
            payment_perantara_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['PRLC','PRTB'] and l.date < self.date_from)
            for payment in payment_perantara:
                payment_amount = payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    '',
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_perantara += payment_amount
                perantara.append(data)
            for payment in payment_perantara_before:
                payment_amount = abs(payment.balance)
                payment_perantara_before_amount += payment_amount
            #RECLASS
            reclass = []
            payment_reclass = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['LUMAP','IUMAP'] and self.date_from <= l.date <= self.date_to)
            payment_reclass_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['LUMAP','IUMAP'] and l.date < self.date_from)
            for payment in payment_reclass:
                payment_amount = payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    '',
                    '',
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_reclass += payment_amount
                reclass.append(data)
            for payment in payment_reclass_before:
                payment_amount = payment_amount = abs(payment.balance)
                payment_reclass_before_amount += payment_amount
            #RETUR
            retur = []
            payment_retur = []
            payment_retur_before = []
            for payment in payment_retur:
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    '',
                    '',
                    '',
                    '',
                    '',
                ]
                pelunasan += 0
                gt_retur += 0
                payment_retur_before_amount += 0
                retur.append(data)
            #LAIN
            lain = []
            payment_lain = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['JMAP'] and self.date_from <= l.date <= self.date_to)
            payment_lain_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['JMAP'] and l.date < self.date_from)
            for payment in payment_lain:
                payment_amount = payment_amount = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    '',
                    '',
                    '',
                    '',
                    '',
                    payment_amount
                ]
                pelunasan += payment_amount
                gt_lain += payment_amount
                lain.append(data)
            for payment in payment_lain_before:
                payment_amount = payment_amount = abs(payment.balance)
                payment_retur_before_amount += payment_amount

            payments = [
                banks,
                kompensasi,
                perantara,
                reclass,
                retur,
                lain
            ]

            total_payment_before_date_from = payment_banks_before_amount + payment_kompensasi_before_amount + payment_perantara_before_amount + payment_reclass_before_amount + \
                payment_retur_before_amount + payment_lain_before_amount
            saldo_awal = bill.amount_total - total_payment_before_date_from if bill.date_invoice < self.date_from else 0
            penambahan = bill.amount_total if self.date_from <= bill.date_invoice <= self.date_to else 0
            saldo_ahir = saldo_awal + penambahan - pelunasan
            bill_info = [
                bill.partner_id.name,
                bill.account_id.name,
                datetime.strptime(bill.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                bill.number,
                bill.nobukti_kontrabon.name or '',
                bill.reference or '',
                saldo_awal,
                penambahan
            ]
            gt_saldo_awal += saldo_awal
            gt_penambahan += penambahan
            gt_saldo_ahir += saldo_ahir
            compiled_data[partner]['bills'][bill.id]['saldo_awal'] = saldo_awal
            compiled_data[partner]['bills'][bill.id]['saldo_ahir'] = saldo_ahir
            compiled_data[partner]['bills'][bill.id]['bill_info'].append(bill_info)
            compiled_data[partner]['bills'][bill.id]['payments'].append(payments)
        
        grand_total = [
            gt_saldo_awal,
            gt_penambahan,
            '',
            '',
            '',
            gt_bank,
            gt_kompensasi,
            gt_perantara,
            gt_reclass,
            gt_retur,
            gt_lain,
            gt_saldo_ahir
        ]
            
        datas['csv'] = compiled_data
        datas['grand_total'] = grand_total
        if self.report_type == 'rekap':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hutang.summary.idr.xls',
                'nodestroy': True,
                'datas': datas,
            }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hutang.idr.xls',
            'nodestroy': True,
            'datas': datas,
        }
            
    ############################## VALAS ##############################################################    
    @api.multi
    def view_hutang_valas_report(self):
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
        
        #KURS
        month = datetime.strptime(self.date_from, '%Y-%m-%d').month
        bulan = month if month >= 10 else '0%s' %(month)
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
            ('type', '=', 'in_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date_invoice', '<=', self.date_to),
            ('currency_id', '=', self.currency_id.id)
        ]        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        bills = self.env['account.invoice'].search(domain, order='date_invoice')
        
        gt_saldo_awal_valas = gt_penambahan_valas = gt_bank_valas = gt_kompensasi_valas = gt_perantara_valas = gt_reclass_valas = gt_retur_valas = gt_lain_valas = gt_total_valas = gt_saldo_ahir_valas = 0
        gt_saldo_awal_idr = gt_penambahan_idr = gt_bank_idr = gt_kompensasi_idr = gt_perantara_idr = gt_reclass_idr = gt_retur_idr = gt_lain_idr = gt_total_idr = gt_selisih_idr = gt_saldo_ahir_idr = 0
        compiled_data = {}
        for bill in bills:
            if not bill.invoice_line_ids:
                continue
            #Remove invoice paid and payment date before date from
            if bill.state == 'paid' and bill.payment_move_line_ids.sorted(key=lambda l: l.date)[-1].date < self.date_from:
                continue
            partner = bill.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'bills' : {} }
            if not compiled_data[partner]['bills'].get(bill.id):
                compiled_data[partner]['bills'][bill.id] = {
                    'saldo_awal': 0, 'bill_info': [], 'payments': [], 
                    'total_pelunasan_valas': 0, 'total_pelunasan_idr': 0, 
                    'saldo_ahir_valas': 0, 'saldo_ahir_idr': 0
                }
            
            pelunasan_valas = pelunasan_idr = payment_banks_before_valas_amount = payment_banks_before_idr_amount = payment_kompensasi_before_valas_amount = payment_kompensasi_before_idr_amount = \
                payment_perantara_before_valas_amount = payment_perantara_before_idr_amount = payment_reclass_before_valas_amount = payment_reclass_before_idr_amount = \
                payment_lain_before_valas_amount = payment_lain_before_idr_amount = 0
            #PAYMENT BANK
            banks = []
            payment_banks = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank','cash'] and self.date_from <= l.date <= self.date_to)
            payment_banks_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['bank','cash'] and l.date < self.date_from)
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

            #PAYMENT KOMPENSASI
            kompensasi = []
            payment_kompensasi = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPE','KPL'] and self.date_from <= l.date <= self.date_to)
            payment_kompensasi_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['KPE','KPL'] and l.date < self.date_from)
            for payment in payment_kompensasi:
                print(bill.number)
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    #BANK
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr
                gt_kompensasi_valas += payment_amount_currency
                gt_kompensasi_idr += payment_amount_idr
                kompensasi.append(data)
            for payment in payment_kompensasi_before:
                payment_kompensasi_before_valas_amount += abs(payment.amount_currency)
                payment_kompensasi_before_idr_amount += abs(payment.balance)

            #PAYMENT PERANTARA
            perantara = []
            payment_perantara = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['PRLC','PRTB'] and self.date_from <= l.date <= self.date_to)
            payment_perantara_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['PRLC','PRTB'] and l.date < self.date_from)
            for payment in payment_perantara:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    #BANK
                    '',
                    '',
                    #KOMPENSASI
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr
                gt_perantara_valas += payment_amount_currency
                gt_perantara_idr += payment_amount_idr
                perantara.append(data)
            for payment in payment_perantara_before:
                payment_perantara_before_valas_amount += abs(payment.amount_currency)
                payment_perantara_before_idr_amount += abs(payment.balance)

            #RECLASS
            reclass = []
            payment_reclass = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['LUMAP','IUMAP'] and self.date_from <= l.date <= self.date_to)
            payment_reclass_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['LUMAP','IUMAP'] and l.date < self.date_from)
            for payment in payment_reclass:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    #BANK
                    '',
                    '',
                    #KOMPENSASI
                    '',
                    '',
                    #PERANTARA
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += payment_amount_currency
                pelunasan_idr += payment_amount_idr                
                gt_reclass_valas += payment_amount_currency
                gt_reclass_idr += payment_amount_idr
                reclass.append(data)
            for payment in payment_reclass_before:
                payment_reclass_before_valas_amount += abs(payment.amount_currency)
                payment_reclass_before_idr_amount += abs(payment.balance)

            #RETUR
            retur = []
            payment_retur = []
            payment_retur_before = []
            for payment in payment_retur:
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    #BANK
                    '',
                    '',
                    #KOMPENSASI
                    '',
                    '',
                    #PERANTARA
                    '',
                    '',
                    #RECLAS UM
                    '',
                    '',
                    0,
                    0
                ]
                pelunasan_valas += 0
                pelunasan_idr += 0                
                gt_retur_valas += 0
                gt_retur_idr += 0
                retur.append(data)
            #LAIN
            lain = []
            payment_lain = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['JMAP'] and self.date_from <= l.date <= self.date_to)
            payment_lain_before = bill.payment_move_line_ids.filtered(lambda l: l.journal_id.code in ['JMAP'] and l.date < self.date_from)
            for payment in payment_lain:
                payment_amount_currency = abs(payment.amount_currency)
                payment_amount_idr = abs(payment.balance)
                data = [
                    payment.move_id.name,
                    payment.move_id.ref,
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    #BANK
                    '',
                    '',
                    #KOMPENSASI
                    '',
                    '',
                    #PERANTARA
                    '',
                    '',
                    #RECLAS UM
                    '',
                    '',
                    #RETUR
                    '',
                    '',
                    payment_amount_currency,
                    payment_amount_idr
                ]
                pelunasan_valas += 0
                pelunasan_idr += 0
                gt_lain_valas += payment_amount_currency
                gt_lain_idr += payment_amount_idr
                lain.append(data)
            for payment in payment_lain_before:
                payment_lain_before_valas_amount += abs(payment.amount_currency)
                payment_lain_before_idr_amount += abs(payment.balance)

            payments = [
                banks,
                kompensasi,
                perantara,
                reclass,
                retur,
                lain
            ]

            total_payment_before_date_from_valas = payment_banks_before_valas_amount + payment_kompensasi_before_valas_amount + payment_perantara_before_valas_amount +\
                payment_reclass_before_valas_amount + 0 + payment_lain_before_valas_amount

            saldo_awal_valas = bill.amount_total - total_payment_before_date_from_valas if bill.date_invoice < self.date_from else 0
            penambahan_valas = bill.amount_total if self.date_from <= bill.date_invoice <= self.date_to else 0
            penambahan_idr = abs(bill.move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable')[0].balance) if self.date_from <= bill.date_invoice <= self.date_to else 0

            saldo_ahir_valas = saldo_awal_valas + penambahan_valas - pelunasan_valas
            selisih_idr = (pelunasan_idr + (round(saldo_ahir_valas * datas['kurs_ahir'], 2))) - ((round(datas['kurs_awal'] * saldo_awal_valas, 2 )) + penambahan_idr)

            bill_info = [
                bill.partner_id.name,
                bill.account_id.name,
                datetime.strptime(bill.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                bill.number,
                bill.nobukti_kontrabon.name or '',
                bill.reference or '',
                datas['kurs_awal'] or 0,
                saldo_awal_valas or 0,
                round(datas['kurs_awal'] * saldo_awal_valas, 2 ),
                penambahan_valas,
                penambahan_idr
            ]

            compiled_data[partner]['bills'][bill.id]['bill_info'].append(bill_info)
            compiled_data[partner]['bills'][bill.id]['payments'].append(payments)
            compiled_data[partner]['bills'][bill.id]['total_pelunasan_valas'] = pelunasan_valas
            compiled_data[partner]['bills'][bill.id]['total_pelunasan_idr'] = pelunasan_idr
            compiled_data[partner]['bills'][bill.id]['total_selisih_idr'] = selisih_idr
            compiled_data[partner]['bills'][bill.id]['saldo_ahir_valas'] = saldo_ahir_valas
            compiled_data[partner]['bills'][bill.id]['saldo_ahir_idr'] = round(saldo_ahir_valas * datas['kurs_ahir'], 2)
            
            gt_saldo_awal_valas += saldo_awal_valas
            gt_saldo_awal_idr += round(datas['kurs_awal'] * saldo_awal_valas, 2 )
            gt_penambahan_valas += penambahan_valas
            gt_penambahan_idr += penambahan_idr
            gt_total_valas += pelunasan_valas
            gt_total_idr += pelunasan_idr
            gt_selisih_idr += selisih_idr
            gt_saldo_ahir_valas += saldo_ahir_valas
            gt_saldo_ahir_idr += round(saldo_ahir_valas * datas['kurs_ahir'], 2)
        
        grand_total = [
            datas['kurs_awal'],
            gt_saldo_awal_valas,
            gt_saldo_awal_idr,
            gt_penambahan_valas,
            gt_penambahan_idr,
            '',
            '',
            '',
            gt_bank_valas,
            gt_bank_idr,
            gt_kompensasi_valas,
            gt_kompensasi_idr,
            gt_perantara_valas,
            gt_perantara_idr,
            gt_reclass_valas,
            gt_reclass_idr,
            gt_retur_valas,
            gt_retur_idr,
            gt_lain_valas,
            gt_lain_idr,
            gt_total_valas,
            gt_total_idr,
            gt_selisih_idr,
            gt_saldo_ahir_valas,
            gt_saldo_ahir_idr,
            datas['kurs_ahir']

        ]
            
        datas['csv'] = compiled_data
        datas['grand_total'] = grand_total
        if self.report_type == 'rekap':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hutang.valas.summary.xls',
                'nodestroy': True,
                'datas': datas,
            }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hutang.valas.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
