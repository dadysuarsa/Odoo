from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError


class PiutangSummaryReportWizard(models.TransientModel):
    _name = 'piutang.summary.report.wizard'
    
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
        ('valas', 'VALAS'),
        ('all', 'All')
    ], string='Mata Uang', default='all')
    state = fields.Selection([
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('all', 'All')
    ], string='Invoice Status', default='all')
    currency_id = fields.Many2one('res.currency', string='Currency')
    
    @api.onchange('type')
    def change_type(self):
        if self.type == 'idr':
            self.currency_id = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1).id
        else:
            self.currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).id
    
    @api.multi
    def view_piutang_summary_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['partner_ids'] = self.partner_ids and ', '.join(map(str, [x.name for x in self['partner_ids']])) or 'All'
        if self.state == 'open':
            datas['invoice_status'] = 'Open / Not Paid'
        elif self.state == 'paid':
            datas['invoice_status'] = 'Paid'
        else:
            datas['invoice_status'] = 'All'
            
        if self.type == 'idr':
            datas['type'] = 'IDR'
        elif self.type == 'valas':
            datas['type'] = self.currency_id.name
        else:
            datas['type'] = 'All'
              
        domain = [
            ('type', '=', 'out_invoice'),
            ('date_invoice', '>=', self.date_from),
            ('date_invoice', '<=', self.date_to)
        ]        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
            
        if self.type == 'idr':
            domain.append(('currency_id', '=', self.currency_id.id))
        elif self.type == 'valas':
            domain.append(('currency_id', '=', self.currency_id.id))
            
        if self.state == 'open':
            domain.append(('state', '=', 'open'))
        elif self.state == 'paid':
            domain.append(('state', '=', 'paid'))
        else:
            domain.append(('state', 'not in', ('draft', 'cancel')))

        invoices = self.env['account.invoice'].search(domain, order='date_invoice')
        
        compiled_data = {}
        gt_invoice = gt_payment = gt_residual = 0
        for invoice in invoices:
            partner = invoice.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'invoices' : {}}
            if not compiled_data[partner]['invoices'].get(invoice.id):
                compiled_data[partner]['invoices'][invoice.id] = {
                        'invoice_info': [],
                        'payments': [],
                        'residual': 0
                    }
            
            invoice_info = [
                partner,
                invoice.number,
                datetime.strptime(invoice.date_invoice, "%Y-%m-%d").strftime("%d-%m-%Y"),
                invoice.amount_total,
                invoice.currency_id.name
            ]
            payments = []
            for payment in invoice.payment_move_line_ids.sorted(key=lambda l: l.date).filtered(lambda l: l.journal_id.code != 'KURS'):
                data = [
                    payment.statement_id.mutasi_bank_id.name if payment.journal_id.type == 'bank' else payment.move_id.name,
                    datetime.strptime(payment.statement_id.mutasi_bank_id.payment_date, "%Y-%m-%d").strftime("%d-%m-%Y") if payment.statement_id.mutasi_bank_id.payment_date else \
                    datetime.strptime(payment.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    abs(payment.amount_currency) if payment.currency_id else abs(payment.balance),
                    payment.currency_id and payment.currency_id.name or 'IDR',
                    payment.ref
                ]
                gt_payment += abs(payment.amount_currency) if payment.currency_id else abs(payment.balance)
                payments.append(data)
            gt_invoice += invoice.amount_total
            gt_residual += invoice.residual
            compiled_data[partner]['invoices'][invoice.id]['invoice_info'].append(invoice_info)
            compiled_data[partner]['invoices'][invoice.id]['payments'].append(payments)
            compiled_data[partner]['invoices'][invoice.id]['residual'] = invoice.residual
        
        grand_total = [
            'GRAND TOTAL',
            '',
            '',
            gt_invoice,
            '',
            '',
            '',
            gt_payment,
            '',
            '',
            gt_residual,
            
        ]
        
        datas['grand_total'] = grand_total
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'piutang.summary.xls',
            'nodestroy': True,
            'datas': datas,
        }
            
