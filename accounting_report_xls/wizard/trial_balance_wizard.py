from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError, ValidationError

class TrialBalanceReportWizard(models.TransientModel):
    _name = 'trial.balance.report.wizard'
    
    @api.multi
    def get_first_date(self):
        current_date = date.today()
        return date(current_date.year, current_date.month, 1)
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    date_from = fields.Date('Start Date', default=get_first_date)
    date_to = fields.Date('End Date', default=date.today())
    account_ids = fields.Many2many('account.account', string='Account(s)')
    target_move = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries')], string="Target Moves", default='posted')
    
    @api.multi
    def view_tb_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['type'] = 'Trial Balance'
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = ', '.join(map(str, [x.code for x in self['account_ids']]))
        
        where_query = ''
        if self.target_move == 'all':
            state = ('draft', 'posted')
            datas['target_move'] = 'All Entries'
        else:
            state = ('posted', 'done')
            datas['target_move'] = 'All Posted Entries'
        
        if self.account_ids:
            datas['account_ids'] = ', '.join(map(str, [x.code for x in self['account_ids']]))
        else:
            datas['account_ids'] = 'All'
        if len(self.account_ids) > 1:
            where_query += " and aa.id in %s" % (str(tuple(self.account_ids.ids)))
        elif len(self.account_ids) == 1:
            where_query += " and aa.id = %s" % (tuple(self.account_ids.ids))
        
        csv = {}
        query = """
                select divisi, code, account, type, coalesce(sum(init),0) as init, coalesce(sum(debit),0) as debit, coalesce(sum(credit),0) as credit
                from 
                    ((select aml.divisi as divisi, aa.code, aa.name as account, 0 as init, coalesce(sum(aml.debit), 0) as debit, coalesce(sum(aml.credit), 0) as credit, aat.name as type
                        from account_account aa
                           left join
                              account_move_line aml on (aml.account_id=aa.id and aml.date >= '%s' and aml.date <= '%s')
                           left join
                              account_account_type aat on (aat.id = aa.user_type_id)
                           left join
                              account_move am on (am.id = aml.move_id and am.state in %s)
                        where
                            aa.company_id = %s %s
                        group by aml.divisi, aa.code, aa.name, aat.name)
                    union
                    (select aml.divisi as divisi, aa.code, aa.name as account, coalesce(sum(aml.debit),0)-coalesce(sum(aml.credit),0) as init, 0 as debit, 0 as credit, aat.name as type
                        from account_account aa
                           left join
                              account_move_line aml on (aml.account_id=aa.id and aml.date < '%s')
                           left join
                              account_account_type aat on (aat.id = aa.user_type_id)
                           left join
                              account_move am on (am.id = aml.move_id and am.state in %s)
                        where
                            aa.company_id = %s %s
                        group by aml.divisi, aa.code, aa.name, aat.name)) as a
                group by divisi, code, account, type
                order by code;
                """ %  (self.date_from, self.date_to, state, self.company_id.id, where_query, self.date_from, state, self.company_id.id, where_query)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()
        compiled_data = {}
        for line in data:
            account = '%s %s' %(line.get('code'), line.get('account'))
            if not compiled_data.get(account):
                compiled_data[account] = {
                    'account_info': [ 
                        line.get('code'),
                        line.get('account'),
                        line.get('type')
                    ], 
                    'init_all': 0, 'debit_all': 0, 'credit_all': 0,
                    'init_textile': 0, 'debit_textile': 0, 'credit_textile': 0,
                    'init_garment': 0, 'debit_garment': 0, 'credit_garment': 0,
                    'init_trading': 0, 'debit_trading': 0, 'credit_trading': 0,
                    'init_livin': 0, 'debit_livin': 0, 'credit_livin': 0,
                    'init_other': 0, 'debit_other': 0, 'credit_other': 0,
                }
            compiled_data[account]['init_all'] += line.get('init')
            compiled_data[account]['debit_all'] += line.get('debit')
            compiled_data[account]['credit_all'] += line.get('credit')
            if line.get('divisi') == '1':
                compiled_data[account]['init_textile'] += line.get('init')
                compiled_data[account]['debit_textile'] += line.get('debit')
                compiled_data[account]['credit_textile'] += line.get('credit')
            elif line.get('divisi') == '2':
                compiled_data[account]['init_garment'] += line.get('init')
                compiled_data[account]['debit_garment'] += line.get('debit')
                compiled_data[account]['credit_garment'] += line.get('credit')
            elif line.get('divisi') == '3':
                compiled_data[account]['init_trading'] += line.get('init')
                compiled_data[account]['debit_trading'] += line.get('debit')
                compiled_data[account]['credit_trading'] += line.get('credit')
            elif line.get('divisi') == '4':
                compiled_data[account]['init_livin'] += line.get('init')
                compiled_data[account]['debit_livin'] += line.get('debit')
                compiled_data[account]['credit_livin'] += line.get('credit')
            else:
                compiled_data[account]['init_other'] += line.get('init')
                compiled_data[account]['debit_other'] += line.get('debit')
                compiled_data[account]['credit_other'] += line.get('credit')
                
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'trial.balance.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
