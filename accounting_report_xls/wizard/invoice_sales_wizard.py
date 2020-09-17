from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError, ValidationError

class InvoiceSalesReporttWizard(models.TransientModel):
    _name = 'invoice.sales.report.wizard'

    @api.multi
    def get_first_date(self):
        current_date = date.today()
        return date(current_date.year, current_date.month, 1)
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    date_from = fields.Date('Start Date', default=get_first_date)
    date_to = fields.Date('End Date', default=date.today())
    divisi = fields.Selection([('1','Textile'), ('2','Garment'), ('3','All')], string="Divisi", default='1')
    
    @api.multi
    def view_delivery_detial(self):
        datas = {}
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        if self.divisi=='3':
            datas['divisi'] = 'Textile & Garment'
        elif self.divisi=='1':
            datas['divisi'] = 'Textile'
        else:
            datas['divisi'] ='Garment'
        
        if self.divisi=='3':
            domain = [
                    ('date_invoice', '>=', self.date_from),
                    ('date_invoice.min_date', '<=', self.date_to),
                    ('state', 'not in', ('draft','cancel')),
                    ('type', '=','out_invoice')

            ]
        else:            
                    
            domain = [
                    ('date_invoice', '>=', self.date_from),
                    ('date_invoice.min_date', '<=', self.date_to),
                    ('state', 'not in', ('draft','cancel')),
                    ('type', '=','out_invoice'),
                    ('divisi','=',self.divisi),
            ]

        cate_id = dict({
            ('1', 'Textile'),
            ('2', 'Garment'),
            ('3', 'Trading'),
            ('4', 'Livin')
        })

        invoices = self.env['account.invoice'].search(domain)
        compiled_data = []
        for invoice in invoices:
            # import ipdb;ipdb.set_trace()
            data_invoice = [
                invoice.number,
                invoice.date_invoice,
                invoice.partner_id.name,
                cate_id.get(invoice.cate_id) or '',
            ]
            compiled_data.append(data_invoice) 
        datas['csv'] = compiled_data
        # import ipdb;ipdb.set_trace()
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'invoice.sales.rekap.xls',
            'nodestroy': True,
            'datas': datas,
        }

# {} = dictionary => update => panggil by key
# [] = List => append => panggill by index