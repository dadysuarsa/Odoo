from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp


class RevisiPurchase(models.Model):
    _name = 'revisi.purchase'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
             })

    name = fields.Char('Revisi Reference Number',required = True,default=lambda self: _('New'),readonly=True)
    purchase_id = fields.Many2one('purchase.order',string='Purchase Order',domain="[('state','not in',('draft','cancel'))]")
    partner_id = fields.Many2one('res.partner', related='purchase_id.partner_id',string='Vendor',readonly=True)
    # divisi = fields.Many2one(related='purchase_id.divisi',string='divisi')
    date_order = fields.Datetime('Revisi Date', required=True, readonly=True,index=True, copy=False, default=fields.Datetime.now)
    reason = fields.Text(string = 'Reason for Revision', required=True)
    order_line = fields.One2many('revisi.purchase.line', 'order_id', string='Order Lines', copy=True)
    # currency_id = fields.Many2one('res.currency', store=True, string='Currency')
    company_id = fields.Many2one('res.company', related='purchase_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(related='purchase_id.currency_id', store=True, string='Currency')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    state = fields.Selection([
       ('draft', 'Draft'),
       ('confirm', 'Confirm'),
       ('cancel', 'Cancel'),
       ('done', 'Done'),
        ], string='Status', readonly=True, copy=False, index=True, default='draft')
    createby  = fields.Many2one('res.partner', 'Propose by', required=True,readonly=True,default=lambda self: self.env.user.partner_id.id)
    approveby = fields.Many2one('res.partner', 'Approved by',readonly=True)
    
    @api.model
    def create(self, vals):
        now=datetime.now()
        year=now.strftime("%y")
        nmsequence=year
        if vals.get('name', 'New') == 'New':
           vals['name'] = self.env['ir.sequence'].get_sequence('name',nmsequence,'RPO%(y)s',6)
        self.write({'state':'draft',})
        return super(RevisiPurchase, self).create(vals)
    
    @api.multi
    def action_change(self):
        res = self.write({
           'name':self.ref,
                      })
        return res
    
    @api.multi
    def cancel(self):
        res = self.write({
            'state':'cancel',
            # 'approveby' : self.env.user.partner_id.id,
            })
        return res

    @api.multi
    def confirm(self):
        for r in self.order_line :
                Po_line = r.env['purchase.order.line'].search([('id','=',r.purchase_line_id.id)])
                if Po_line.qty_received > 0 :
                    if Po_line.product_qty  != r.product_qty :
                        raise UserError(_('Qty tidak bisa dirubah karena sudah di STPB pada nama barang  %s')%(r.name))

        res = self.write({
            'state':'confirm',
            # 'approveby' : self.env.user.partner_id.id,
            })
        return res

    @api.multi
    def validate(self):        
        Po_mst = self.env['purchase.order'].search([('id','=',self.purchase_id.id)])

        if Po_mst :
            Po_mst.currency_id = self.currency_id
            Po_mst.amount_untaxed = self.amount_untaxed
            Po_mst.amount_tax = self.amount_tax
            Po_mst.amount_total = self.amount_total
            for r in self.order_line :
                Po_line = r.env['purchase.order.line'].search([('id','=',r.purchase_line_id.id)])
                Po_line.price_unit = r.price_unit 
                Po_line.taxes_id = r.taxes_id 
                Po_line.price_total =r.price_total 
                Po_line.price_tax = r.price_tax
                Po_line.currency_id = r.currency_id
                if Po_line.qty_received == 0 :
                    Po_line.product_qty = r.product_qty
                else :
                    if Po_line.product_qty  != r.product_qty :
                       raise UserError(_('Qty tidak bisa dirubah karena sudah di STPB pada nama barang  %s')%(r.name))

        res = self.write({
            'state':'done',
            'approveby' : self.env.user.partner_id.id,
            })
        return res

   
    @api.onchange('purchase_id')
    def onchange_invoice_id(self):
            new_lines = self.env['revisi.purchase.line'] 
            pack_line = self.env['purchase.order.line'].search([('order_id', '=', self.purchase_id.id)])
            for line in pack_line: 
                data = self._prepare_account_line(line)
                new_line = new_lines.new(data)
                new_lines += new_line
            self.order_line = new_lines

    def _prepare_account_line(self,line):
       data = {
                'product_id': line.product_id.id,
                'product_uom': line.product_uom,
                'price_unit': line.price_unit,
                'product_qty': line.product_qty,
                'taxes_id': line.taxes_id,
                'name': line.name,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_total,
                'price_tax': line.price_tax,
                'qty_invoiced': line.qty_invoiced,
                'partner_id': line.partner_id.id,
                'currency_id': line.currency_id.id,
                'purchase_line_id': line.id
               }
       # raise UserError (line.id)
       return data

class RevisiPurchaseLine(models.Model):
    _name = 'revisi.purchase.line'

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
   
    name = fields.Text(string='Description',readonly=True)
    purchase_line_id = fields.Many2one('purchase.order.line',string='purchase line order')
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True)
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    product_uom = fields.Many2one('product.uom', string='Product Unit of Measure', required=True,readonly=True,)
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True, required=True,readonly=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)

    order_id = fields.Many2one('revisi.purchase', string='Revisi Purchase Reference', index=True, required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', related='order_id.company_id', string='Company', store=True, readonly=True)
    state = fields.Selection(related='order_id.state', store=True)

    partner_id = fields.Many2one('res.partner', related='order_id.partner_id', string='Partner', readonly=True, store=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)

    # @api.onchange('product_qty')
    # def onchange_product_qty(self):
        
    #     Po_line2 = self.env['purchase.order.line'].search([('id','=',self.purchase_line_id.id)])
    #     for a in Po_line2 :
    #         raise UserError(a.id)
    #         if not Po_line2 :
    #             if Po_line2.qty_received > 0 :
    #                 raise UserError(_('Qty tidak bisa dirubah, karena sudah di STPB pada kode barang %s')%(self.name))

                # if Po._line.qty_recived == 0:
            #     Po_line.product_id = self.product_id
            #     Po_line.name = self.name
            #     Po_line.product_uom = self.product_uom 



        