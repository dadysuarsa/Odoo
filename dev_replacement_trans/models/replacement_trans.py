from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

class ReplacementTrans(models.Model):
    _name = 'replacement.trans'


    name = fields.Char(string='Nomor Replacement',required = True,default=lambda self: _('New'),readonly=True)
    company_id = fields.Many2one('res.company', ondelete='set null',string='Company Id',index=True,default=lambda self: self.env['res.company']._company_default_get('replacement.trans  '))
    user_id = fields.Many2one('res.users',string='User id ', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    order_line = fields.One2many('replacement.trans.line','order_id',string='Replacement Trans Line')
    location_origin_id = fields.Many2one('stock.location', 'Source Location',readonly=True,required = True,states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(comodel_name="res.partner",
                string="Customer",
                required=False,
                related="invoice_id.partner_id",
                store=True)
    picking_id = fields.Many2one(omodel_name="stock.picking",
                string="Ref Delivery Order",
                required=False,
                related="invoice_id.picking_id",
                store=True)
    state= fields.Selection([
        ('draft',"Draft"),
        ('cancel',"Cancel"),
        ('done',"Done"),
        ], string="Status", readonly=True,copy=False,index=True,default='draft')
    invoice_id = fields.Many2one('account.invoice',string="Invoice",domain="[('state','not in',('draft','cancel'))]",readonly=True,required = True,states={'draft': [('readonly', False)]})
    divisi = fields.Selection([('1','Textile'),('2','Garment')],required=True)
    date_trans = fields.Datetime(string='Date Request', required=True, index=True, copy=False,
               default=fields.Datetime.now,help="date Transaction",readonly=True,states={'draft': [('readonly', False)]})
    amount_total = fields.Float(compute='_amount_total', string='Total Amount', store=True,
        help="total amount.")
    stock_picking_count = fields.Integer('Delvery Order Out', compute='_get_stock_picking_count')

    @api.depends('order_line')
    def _amount_total(self):
        for r in self :
            r.amount_total=sum([x.amount_subtotal for x in r.order_line])

    @api.multi
    def button_confirm(self):
        # locationreplacement_trans= self.env['stock.location'].search([('is_replacement','=',True),('company_id','=',self.company_id.id)], limit=1)
        # if not locationreplacement_trans:
        #     raise UserError(_('Lokasi  belum di setting'))
        # locationsub_cont= self.env['stock.location'].search([('is_subcont','=',True),('company_id','=',self.company_id.id)], limit=1)
        # if not locationsub_cont:
        #     raise UserError(_('Lokasi sub cont belum di setting'))

        if not self.company_id:
            raise UserError(_('Company ID is null'))
        if not self.partner_id:
            raise UserError(_('Partner ID is null'))
        stock_picking_obj = self.env['stock.picking']
        moves = self.env['stock.move']
        wh_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
        picking_type = self.env['stock.picking.type'].search([('name','=','Delivery Orders'),('warehouse_id','=',wh_id.id)], limit=1)
        # locationreplacement_trans= self.env['stock.location'].search([('is_replacement','=','True'),('company_id','=',self.company_id.id)], limit=1)
        # if not  locationreplacement_trans:
        #        raise UserError(_('Lokasi replacement belum di setting'))
        for line in self.order_line:
            pick_order = stock_picking_obj.search([('replacement_request_id','=',self.id),('partner_id','=',self.partner_id.id)])
            if pick_order:
               vals = line._get_move_values(pick_order)
               move = moves.create(vals)
               move.action_confirm()
            else:
                vals = {
                   'picking_type_id': picking_type.id,
                   'partner_id': self.partner_id.id,
                   'date': self.date_trans,
                   'origin': self.name,
                   'replacement_request_id':self.id, 
                   'location_dest_id':9,
                   'location_id': self.location_origin_id.id,
                   'company_id': self.company_id.id,
                   }    
                picking_obj = stock_picking_obj.create(vals) 
                vals = line._get_move_values(picking_obj)
                move = moves.create(vals)
                move.action_confirm()

            res = self.write({
            'state':'done',
                        })
        return res
   
    
    @api.multi
    def _get_stock_picking_count(self):
        for picking in self:
            picking_ids = self.env['stock.picking'].search([('replacement_request_id','=',picking.id)])
            picking.stock_picking_count = len(picking_ids)

    @api.multi
    def stock_picking_button(self):
            self.ensure_one()
            return {
                'name': 'Delivery Order',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'stock.picking',
                'domain': [('replacement_request_id', '=', self.id)],
            }

    @api.multi
    @api.constrains('divisi','name')
    def _check_divisi(self):
        name_o = self.name
        name_s =(name_o[:1])
        if self.name != 'New' :
            if name_s != self.divisi :
                raise ValidationError(_('Penomoran tidak sesuai dengan Divisi'))

    @api.model
    def create(self, vals):
            company_code =  self.env.user.company_id.code_company
            divisi= vals.get('divisi')
            date_o =  vals.get('date_trans')
            tahun = (date_o[2:-15])
            bulan = (date_o[5:-12])
          #  raise UserError(_('You : %s.') % (tahun+bulan,))
            if vals.get('name', 'New') == 'New' and  vals.get('divisi', '1') == '1' :
                    # values['name'] = company_code+"DS"+ tahun+bulan+self.env['ir.sequence'].next_by_code_new('delivery.operation',values.get('date_trans')) or _('New')      
                    vals['name'] = divisi+"RPLS"+tahun+bulan+self.env['ir.sequence'].next_by_code_new('replacement.trans',vals.get('date_trans')) or _('New')

            else:    
                    vals['name'] = divisi+"RPLS"+tahun+bulan+self.env['ir.sequence'].next_by_code_new('replacement.trans2',vals.get('date_trans')) or _('New')
        
                    # vals['name'] = self.env['ir.sequence'].next_by_code('replacement.trans') or _('New')
            result = super(ReplacementTrans, self).create(vals)
            return result

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
            new_lines = self.env['replacement.trans.line'] 
            pack_line = self.env['account.invoice.line'].search([('invoice_id', '=', self.invoice_id.id)])
            for line in pack_line: 
                data = self._prepare_account_line(line)
                new_line = new_lines.new(data)
                new_lines += new_line
            self.order_line = new_lines

    def _prepare_account_line(self,line):
       data = {
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'unit_price': line.price_unit,
                'qty': line.quantity
               }
       return data

class ReplacementTransLine(models.Model):
    _name = 'replacement.trans.line'

    order_id =fields.Many2one('replacement.trans',string='Order id')
    product_id  = fields.Many2one('product.product', string='Item', readonly=True)
    qty = fields.Float(string="Qty")
    uom_id = fields.Many2one('product.uom',string='Unit',readonly=True)
    unit_price =fields.Float(string ="Unit Price",readonly=True)
    amount_subtotal = fields.Float(compute='_amount_subtotal', string='Sub Total Amount', store=True,help="Sub total amount")

    @api.depends('qty','unit_price')
    def _amount_subtotal(self):
        for r in self:
            r.amount_subtotal = r.qty*r.unit_price

    def _get_move_values(self,values):
            self.ensure_one()
            return {
                 'name': (self.product_id.name or ''),
                 'origin': (self.order_id.name or ''),
                 'product_id': self.product_id.id,
                 'product_uom': self.product_id.product_tmpl_id.uom_id.id,
                 'product_uom_qty': self.qty,
                # 'product_qty': self.product_qty,
                 'date': fields.datetime.today(),
                 'company_id': self.order_id.company_id.id,
                 'state': 'confirmed',
                 'location_id': values.location_id.id,
                 'location_dest_id': values.location_dest_id.id,
                 'picking_id':values.id,
                }

class stockpicking(models.Model):
    _inherit = 'stock.picking'

    replacement_request_id = fields.Many2one('replacement.trans', string='Replacement REQUEST')

# class stocklocation(models.Model):
#     _inherit = 'stock.location'

#     is_replacement = fields.Boolean(string="Replacement Trans",default =False) 
