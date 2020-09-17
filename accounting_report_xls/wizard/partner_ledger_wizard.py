from openerp import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from openerp.exceptions import UserError, ValidationError

class PartnerLedgerReportWizard(models.TransientModel):
    _name = 'partner.ledger.report.wizard'
    
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
    def view_partner_ledger_report(self):
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
            
        query = """
                select 
                    rp.name as partner,
                    rp.ref as partner_code,
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
                    left join
                        res_partner rp on (rp.id = aml.partner_id)
                    left join
                        account_journal aj on (aj.id = aml.journal_id)
                    left join
                        account_full_reconcile afr on (afr.id = aml.full_reconcile_id)
                where
                    aml.company_id = %s and
                    aml.date < '%s' %s
                group by 
                    aa.code, rp.name, rp.ref, aa.code, aa.name;
        """ %  (self.company_id.id, self.date_from, where_query)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()
        
        for move_line in data:
            account = move_line['account'] + ' - ' + move_line['acc_name']
            partner = move_line.get('partner') and move_line['partner'] or 'Undefined'
            if move_line.get('partner_code'):
                partner = move_line['partner_code'] + ' - ' + partner
                
            if not compiled_data.get(account):
                compiled_data[account] = {'ending_debit' : 0, 'ending_credit' : 0, 'partner' : {}}
            
            if not compiled_data[account]['partner'].get(partner):
                compiled_data[account]['partner'][partner] = {
                                                                    'init_debit' : move_line['debit'],
                                                                    'init_credit' : move_line['credit'],
                                                                    'move_line' : []}
            compiled_data[account]['ending_debit'] += move_line['debit']
            compiled_data[account]['ending_credit'] += move_line['credit']
            
        query = """
                select 
                    rp.name as partner,
                    rp.ref as partner_code, 
                    aml.date, 
                    am.name as entry, 
                    aa.code as account, 
                    aa.name as acc_name, 
                    aj.code as journal, 
                    aml.name as label, 
                    afr.name as rec, 
                    sum(aml.debit) as debit, 
                    sum(aml.credit) as credit
                from 
                    account_move_line aml
                    left join
                        account_account aa on (aa.id = aml.account_id)
                    left join
                        account_move am on (am.id = aml.move_id)
                    left join
                        res_partner rp on (rp.id = aml.partner_id)
                    left join
                        account_journal aj on (aj.id = aml.journal_id)
                    left join
                        account_full_reconcile afr on (afr.id = aml.full_reconcile_id)
                where
                    aml.company_id = %s and
                    aml.date >= '%s' and
                    aml.date <= '%s' %s
                group by 
                    rp.name, rp.ref, aml.date, aml.id, aa.code, aa.name, am.name, aj.code, aml.name, afr.name
                order by 
                    aa.code, rp.name, aml.date, aml.id;
        """ %  (self.company_id.id, self.date_from, self.date_to, where_query)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()
        for move_line in data:
            account = move_line['account'] + ' - ' + move_line['acc_name']
            partner = move_line.get('partner') and move_line['partner'] or 'Undefined'
            if move_line.get('partner_code'):
                partner = move_line['partner_code'] + ' - ' + partner
            if not compiled_data.get(account):
                compiled_data[account] = {'ending_debit' : 0, 'ending_credit' : 0, 'partner' : {}}
            
            if not compiled_data[account]['partner'].get(partner):
                compiled_data[account]['partner'][partner] = {'init_debit' : 0,
                                                                           'init_credit' : 0,
                                                                           'move_line' : []}
            
            compiled_data[account]['partner'][partner]['move_line'].append([
                                                                    move_line['date'], 
                                                                    move_line['entry'], 
                                                                    move_line['journal'], 
                                                                    move_line['label'], 
                                                                    move_line['rec'], 
                                                                    move_line['debit'], 
                                                                    move_line['credit']])
            compiled_data[account]['ending_debit'] += move_line['debit']
            compiled_data[account]['ending_credit'] += move_line['credit']
            
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'partner.ledger.xls',
            'nodestroy': True,
            'datas': datas,
        }
    
