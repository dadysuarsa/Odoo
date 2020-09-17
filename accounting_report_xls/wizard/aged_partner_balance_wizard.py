from odoo import fields, models, api, _
from datetime import datetime, date
from odoo.exceptions import UserError

class AgedPartnerBalanceReportWizard(models.TransientModel):
    _name = 'aged.partner.balance.report.wizard'
    
    @api.multi
    def get_first_date(self):
        current_date = date.today()
        return date(current_date.year, current_date.month, 1)
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    start_date = fields.Date('Start Date', default=date.today())
    period_length = fields.Char('Period Range', default='30,30,30,30,30,30')
    account_ids = fields.Many2many('account.account', string='Account(s)')
    partner_ids = fields.Many2many('res.partner', string='Partner(s)')
    target_move = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries')], string="Target Moves", default='all')
    
    @api.multi
    def view_aged_partner_balance_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['type'] = 'Partner Balance'
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['period_length'] = self.period_length
        datas['start_date'] = datetime.strptime(self.start_date, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = 'All'
        datas['partner_ids'] = 'All'
        
        compiled_data = {}
        periods = []
        last_period = 0
        try:
            for length in self.period_length.split(','):
                periods.append([last_period + 1, last_period + int(length)])
                last_period += int(length)
        except:
            raise UserError(_('Invalid Period Range'))
            
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
            
        query = """
                select  
                    aa.name as acc_name,
                    aa.code as account,
                    rp.name as partner,
                    rp.ref as partner_ref,
                    aml.date as date,
                    am.name as entry,
                    aml.name as label,
                    aj.code as journal,
                    '%s'::date - (CASE 
                                    WHEN aml.date_maturity is not null THEN
                                        aml.date_maturity
                                    ELSE
                                        aml.date
                                    END) as age, 
                    coalesce(aml.debit,0.0)-coalesce(aml.credit,0.0) as amount, 
                    sum(coalesce(apr2.amount,0.0) - coalesce(apr1.amount,0.0)) as payment
                from 
                    account_move_line aml 
                    left join account_move am on am.id=aml.move_id 
                    left join account_account aa on aa.id=aml.account_id 
                    left join account_partial_reconcile apr1 on apr1.debit_move_id = aml.id 
                    left join account_move_line aml1 on aml1.id=apr1.credit_move_id 
                    left join account_partial_reconcile apr2 on apr2.credit_move_id = aml.id 
                    left join account_move_line aml2 on aml2.id=apr2.debit_move_id 
                    left join res_partner rp on rp.id = aml.partner_id
                    left join account_journal aj on aj.id = am.journal_id
                    left join account_invoice ai on ai.move_id=aml.move_id
                where 
                    aml.company_id = %s and
                    aml.date < '%s' and 
                    (aml.reconciled is false or aml1.date > '%s' or aml2.date > '%s') and 
                    (aml2.date < '%s' or aml1.date < '%s' or (apr1.id is null and apr2.id is null)) and
                    aa.reconcile is true %s
                group by 
                    aml.id, aa.name, aa.code, rp.name, rp.ref, aml.date, am.name,aml.name, aj.code,
                    aml.name, aml.debit, aml.credit
                order by
                    aml.date, aml.id;
                    
        """ % (self.start_date, self.company_id.id, self.start_date, self.start_date, self.start_date, self.start_date, self.start_date, where_query)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()

        print (periods)
        for move_line in data:
            account = move_line['account'] + ' - ' + move_line['acc_name']
            partner = move_line.get('partner') and move_line['partner'] or 'Undefined'
            if move_line.get('partner_code'):
                partner = move_line['partner_code'] + ' - ' + partner

            if not compiled_data.get(account):
                compiled_data[account] = {'partner' : {}, 'ending' : [0 for i in range(len(periods) + 3)]}

            if not compiled_data[account]['partner'].get(move_line['partner']):
                compiled_data[account]['partner'][partner] = []
            
            balance = move_line['amount'] + move_line['payment']
            line = [
               move_line['date'],
               move_line['entry'],
               move_line['label'],
               move_line['journal'],
               balance,
            ]
            
            if move_line['age'] <= 0:
                line.append(balance)
                compiled_data[account]['ending'][1] += balance
            else:
                line.append(0)
            i = 2
            for period in periods:
                if move_line['age'] >= period[0] and  move_line['age'] <= period[1]:
                    line.append(balance)
                    compiled_data[account]['ending'][i] += balance
                else:
                    line.append(0)
                i += 1
            if move_line['age'] >= period[1]:
                line.append(balance)
                compiled_data[account]['ending'][i] += balance
            else:
                line.append(0)
                
            compiled_data[account]['partner'][partner].append(line)
            compiled_data[account]['ending'][0] += balance
            
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'aged.partner.balance.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
