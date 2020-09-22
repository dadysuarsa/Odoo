from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError, ValidationError

class GeneralLedgerReportWizard(models.TransientModel):
    _name = 'general.ledger.report.wizard'
    
    @api.multi
    def get_first_date(self):
        current_date = date.today()
        return date(current_date.year, current_date.month, 1)
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    date_from = fields.Date('Start Date', default=get_first_date)
    date_to = fields.Date('End Date', default=date.today())
    include_amount_currency = fields.Boolean('Include Amount Currency', default=False)
    account_ids = fields.Many2many('account.account', string='Account(s)')
    target_move = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries')], string="Target Moves", default='posted')
    
    @api.multi
    def view_gl_report(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['type'] = 'General Ledger'
        datas['company_name'] = self.company_id.name + ' - ' + self.company_id.currency_id.name
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['account_ids'] = ', '.join(map(str, [x.code for x in self['account_ids']]))
        datas['include_amount_currency'] = self.include_amount_currency or False
        
        compiled_data = {}
        where_query = c_where_query = ''
        
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
            where_query += " and aml.account_id in %s" % (str(tuple(self.account_ids.ids)))
        elif len(self.account_ids) == 1:
            where_query += " and aml.account_id = %s" % (tuple(self.account_ids.ids))

        divisi = dict({
            ('1', 'Textile'),
            ('2', 'Garment'),
            ('3', 'Trading'),
            ('4', 'Livin')
        })

        ####### INITIAL BALANCE
        query = """
                select 
                    aa.code as account, 
                    aa.name as acc_name,
                    sum(aml.debit) as debit, 
                    sum(aml.credit) as credit
                from 
                    account_move_line aml
                    left join
                        account_account aa on (aa.id = aml.account_id)
                    left join
                        account_move am on (am.id = aml.move_id)
                where
                    aml.company_id = %s and
                    aml.date < '%s' %s
                group by 
                    aa.code, aa.name;
                    
        """ %  (self.company_id.id, self.date_from, where_query)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()
        for move_line in data:
            account = move_line['account'] + ' - ' + move_line['acc_name']
            if not compiled_data.get(account):
                compiled_data[account] = {'init_debit' : 0, 'init_credit' : 0, 'move_line' : []}
            compiled_data[account]['init_debit'] += move_line['debit']
            compiled_data[account]['init_credit'] += move_line['credit']
            
        query = """
                select 
                    aml.date, aml.divisi as divisi, 
                    CASE WHEN aml.currency_id is not null THEN rc.name
                        ELSE 'IDR' END as currency,
                    CASE WHEN statement.mutasi_bank_id is not null THEN mb.name
                        ELSE statement.name END as mutation,
                    am.name as entries, aj.code as journal, aa.code as account, aa.name as acc_name, 
                    rp.name as partner, aml.name as label, string_agg(aa1.code, ', ') as counterpart, string_agg(aa1.name, ', ') as counterpart_name, aml.debit, aml.credit, aml.amount_currency
                from account_move_line aml
                    left join 
                        account_move_line aml1 on (aml1.move_id=aml.move_id and aml1.id !=aml.id ) 
                    left join 
                        account_account aa1 on (aa1.id=aml1.account_id) 
                    left join
                        account_move am on (am.id = aml.move_id)
                    left join
                        account_journal aj on (aj.id = aml.journal_id)
                    left join
                        account_account aa on (aa.id = aml.account_id)
                    left join 
                        res_partner rp on (rp.id = aml.partner_id)
                    left join 
                        account_bank_statement statement on (statement.id = aml.statement_id)
                    left join
                        mutasi_bank mb on (mb.id = statement.mutasi_bank_id)
                    left join res_currency rc on (rc.id = aml.currency_id)
                where 
                    aml.company_id = %s and
                    aml.date >= '%s' and
                    aml.date <= '%s' and
                    am.state in %s %s
                group by
                    aml.date, aml.divisi, aml.currency_id, rc.name, mb.name, statement.name, statement.mutasi_bank_id, aml.id, am.name, aj.code, aa.code, aa.name, 
                    rp.name, aml.name, aml.debit, aml.credit, aml.amount_currency
                order by aml.date, aml.id;
                """ %  (self.company_id.id, self.date_from, self.date_to, state, where_query)
        
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()
        if not data:
            raise UserError(_('There is no move in this period'))
        
        for move_line in data:
            account = move_line['account'] + ' - ' + move_line['acc_name']
            if not compiled_data.get(account):
                compiled_data[account] = {'init_debit' : 0, 'init_credit' : 0, 'move_line' : []}
            if self.include_amount_currency:
                compiled_data[account]['move_line'].append([
                                                            datetime.strptime(move_line['date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                                                            divisi.get(move_line['divisi']) or '', 
                                                            move_line['mutation'], 
                                                            move_line['entries'], 
                                                            move_line['journal'], 
                                                            move_line['account'], 
                                                            move_line['acc_name'], 
                                                            move_line['partner'], 
                                                            move_line['label'], 
                                                            move_line['counterpart'],
                                                            move_line['counterpart_name'],
                                                            '',
                                                            move_line['currency'], 
                                                            move_line['amount_currency'], 
                                                            move_line['debit'], 
                                                            move_line['credit']])
            else:
                compiled_data[account]['move_line'].append([
                                                            datetime.strptime(move_line['date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                                                            divisi.get(move_line['divisi']) or '', 
                                                            move_line['mutation'], 
                                                            move_line['entries'], 
                                                            move_line['journal'], 
                                                            move_line['account'], 
                                                            move_line['acc_name'], 
                                                            move_line['partner'], 
                                                            move_line['label'], 
                                                            move_line['counterpart'],
                                                            move_line['counterpart_name'],
                                                            '',
                                                            move_line['debit'], 
                                                            move_line['credit']])
            
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'general.ledger.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
