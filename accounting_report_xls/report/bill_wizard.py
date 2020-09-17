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
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    date_from = fields.Date('Start Date', default=get_first_date)
    date_to = fields.Date('End Date', default=date.today())
    account_ids = fields.Many2many('account.account', string='Account(s)')
    partner_ids = fields.Many2many('res.partner', string='Partner(s)')
    target_move = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries')], string="Target Moves", default='posted')
    
    @api.multi
    def view_piutang_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['type'] = 'Partner Ledger'
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = 'All'
        datas['partner_ids'] = 'All'
        
        compiled_data = {}
        where_query = ''
        if self.target_move != 'all':
            where_query += "and am.state='posted'"
            datas['target_move'] = 'All Posted Entries'
        else:
            datas['target_move'] = 'All Entries'
        
        if self.account_ids:
            datas['account_ids'] = ', '.join(map(str, [x.code for x in self['account_ids']]))
        if len(self.account_ids) > 1:
            where_query += " and aml.account_id in %s" % (str(tuple(self.account_ids.ids)))
        elif len(self.account_ids) == 1:
            where_query += " and aml.account_id = %s" % (tuple(self.account_ids.ids))
        else :
            where_query += " and aa.reconcile is true"
        
        if self.partner_ids:
            datas['partner_ids'] = ', '.join(map(str, [x.name for x in self['partner_ids']]))
        if len(self.partner_ids) > 1:
            where_query += " and aml.partner_id in %s" % (str(tuple(self.partner_ids.ids)))
        elif len(self.partner_ids) == 1:
            where_query += " and aml.partner_id = %s" % (tuple(self.partner_ids.ids))
        invoice_status = {
            ('draft', 'Draft'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('open', 'Open'),
            ('paid', 'Paid')
        }

        domain = [
            ('partner_id.customer', '=', True),
            ('date_invoice', '>=', self.date_from),
            ('date_invoice', '<=', self.date_to),
            ('state', '!=', 'cancel')
        ]
        invoices = self.env['account.invoice'].search(domain, order='date_invoice')
        compiled_data = {}

        for invoice in invoices:
            partner = invoice.partner_id.name or 'Undefined'
            if not compiled_data.get(partner):
                compiled_data[partner] = {'initial' : 0, 'ending' : 0, 'invoices' : []}
            data_invoice = [
                invoice.number,
                invoice.date_invoice,
                0,
                0,
                abs(invoice.move_id.line_ids.filtered(lambda l: l.account_id.user_type_id.type == 'receivable').amount_currency),
                abs(invoice.move_id.line_ids.filtered(lambda l: l.account_id.user_type_id.type == 'receivable').balance),
                abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['cash', 'bank']).mapped('amount_currency'))),
                abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type in ['cash', 'bank']).mapped('balance'))),
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                abs(sum(invoice.payment_move_line_ids.filtered(lambda l: l.journal_id.type == 'general').mapped('balance'))),
                0,
                0,
                invoice.state
            ]
            compiled_data[partner]['invoices'].append(data_invoice)
            
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'vendor.bill.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
