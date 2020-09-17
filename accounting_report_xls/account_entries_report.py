# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models, fields
import openerp.addons.decimal_precision as dp

class AccountEntiresReport(models.Model):
    _name = "report.account.move.line"
    _description = "Journal Items Analysis"
    _auto = False

    date = fields.Date('Date', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    account_id = fields.Many2one('account.account', string='Account', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    balance = fields.Float('Balance', readonly=True)
    debit_cb = fields.Float('Debit (Cash Basis)', readonly=True)
    credit_cb = fields.Float('Credit (Cash Basis)', readonly=True)
    balance_cb = fields.Float('Balance (Cash Basis)', readonly=True)
    user_type_id = fields.Many2one('account.account.type', string='Type', required=True, oldname="user_type", 
        help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries.")
    unreconciled = fields.Boolean('Unreconciled', readonly=True)
    reconciled = fields.Boolean('Reconciled', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    amount_currency = fields.Float('Amount Currency', digits_compute=dp.get_precision('Account'), readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')])
    
    def init(self, cr):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(cr, 'account_move_line_report')
        cr.execute("""
            CREATE OR REPLACE view report_account_move_line AS (
                SELECT 
                    min(aml.id) as id,
                    aml.company_id as company_id,
                    aml.date as date,
                    aml.currency_id as currency_id,
                    aml.amount_currency as amount_currency,
                    aml.journal_id as journal_id,
                    aml.account_id as account_id,
                    aml.analytic_account_id as analytic_account_id,
                    aml.partner_id as partner_id,
                    aml.product_id as product_id,
                    aml.product_uom_id as uom_id,
                    COALESCE(SUM(aml.quantity), 0) as quantity,
                    COALESCE(SUM(aml.debit), 0) as debit,
                    COALESCE(SUM(aml.credit), 0) as credit,
                    COALESCE(SUM(aml.debit),0) - COALESCE(SUM(aml.credit), 0) as balance,
                    COALESCE(SUM(aml.debit_cash_basis), 0) as debit_cb,
                    COALESCE(SUM(aml.credit_cash_basis), 0) as credit_cb,
                    COALESCE(SUM(aml.debit_cash_basis),0) - COALESCE(SUM(aml.credit_cash_basis), 0) as balance_cb,
                    (not aml.reconciled and aa.reconcile) as unreconciled,
                    aml.reconciled as reconciled,
                    aml.user_type_id,
                    am.state as state
                FROM 
                    account_move_line as aml 
                    LEFT JOIN account_move as am on (am.id = aml.move_id)
                    LEFT JOIN account_account as aa on (aa.id = aml.account_id)
                GROUP BY
                    aml.journal_id,
                    aml.account_id,
                    aml.analytic_account_id,
                    aml.partner_id,
                    aml.product_id,
                    aml.product_uom_id,
                    aml.date,
                    aml.reconciled,
                    aml.user_type_id,
                    aml.amount_currency,
                    aml.currency_id,
                    aml.company_id,
                    am.state,
                    aa.reconcile
            )
        """ )
    
AccountEntiresReport()