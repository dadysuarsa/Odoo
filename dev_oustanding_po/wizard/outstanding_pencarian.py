from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
import odoo.addons.decimal_precision as dp
from datetime import date
from datetime import datetime
import calendar

class OutstandingPO(models.TransientModel):
    _name = 'create.cursor.outstanding'

    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor", domain=[('supplier','=',[True])],required=False)
    purchase_id = fields.Many2one(comodel_name="purchase.order", string="PO", required=False)
    product_id = fields.Many2one(comodel_name="product.product",string="Barang",required=False)
    product_ids = fields.One2many(comodel_name="create.cursor.line.outstanding",
                                    inverse_name="wizard_id",
                                    string="Product to View",
                                    required=False)
    fill_detail = fields.Selection([('1','Cari')],string="Cari Data")
    sebelumnya = fields.Selection([('1','<< Sebelumnya')],string="Cari Data")
    berikutnya = fields.Selection([('2','Berikutnya >>')],string="Cari Data")
    nomor2 = fields.Integer('Nomor')
    
    @api.onchange('vendor_id')
    def _filtersupp(self):
        if self.vendor_id:
           res = {}
           res['domain']={'purchase_id':[('partner_id', '=', self.vendor_id.id)]}
           return res

    # @api.onchange('purchase_id')
    # def _filtersupp1(self):
    #     if self.purchase_id:
    #        res = {}
    #        res['domain']={'product_id':[('order_id', '=', self.purchase_id.id)]}
    #        return res

    @api.onchange('fill_detail')
    def _fill_outstanding_line(self):
        self.update({'product_ids':False})
        new_lines_outstanding = self.env['create.cursor.line.outstanding']
        
        #vendor dan purchase dan product
        if self.product_id and self.purchase_id and self.vendor_id:
            # raise UserError(str(self.product_id)+' '+str(self.purchase_id)+' '+str(self.vendor_id))
            query="""
                select 
                    partner as partner,name  as po_name,id as po_id, product_id,sum(terima_qty) as qty_received, sum(product_qty)  as product_qty, sum(product_qty)-sum(terima_qty)  as qty_outstanding
                from 
                ( 
                    select 
                        a.partner_id as partner,a.name  ,a.id,  b.product_id, 0  as terima_qty,sum(b.product_qty) as product_qty  from purchase_order a 
                    inner join purchase_order_line b on a.id = b.order_id                 
                    group by  a.name  , b.product_id,a.partner_id,a.id
                                
                    union all 

                    select  
                    a.partner_id as partner,a.origin as name ,c.id,  b.product_id, sum(b.product_qty) as terima_qty, 0  as product_qty    from stock_picking a 
                    inner join stock_move b on a.id = b.picking_id  and a.state = 'done'
                    inner join purchase_order c on a.origin = c.name 
                    group by b.product_id,a.origin,a.partner_id,c.id  
                ) 
                aa
                where product_id=%s and partner=%s and name=%s 
                group by id,name , product_id,partner
            """
            # raise UserError(query+' '+'test2')
            list_of_dictionary = self._cr.execute(query,(self.product_id.id,self.vendor_id.id,self.purchase_id.name))
            list_of_dictionary =self.env.cr.dictfetchall()
            # raise UserError(str(self.vendor_id.id)+' '+str(self.purchase_id.id)+' '+str(self.product_id.id))

            for r in list_of_dictionary:
                data = self._fill_detail_outstanding(r)
                new_line = new_lines_outstanding.new(data)
                new_lines_outstanding += new_line
            self.product_ids += new_lines_outstanding
            # raise UserError(list_of_dictionary)

        #product dan vendor
        if self.product_id and self.vendor_id and not self.purchase_id :
            # raise UserError(str(self.product_id)+' '+str(self.purchase_id)+' '+str(self.vendor_id))
            query="""
                select 
                    partner as partner,name  as po_name,id as po_id, product_id,sum(terima_qty) as qty_received, sum(product_qty)  as product_qty, sum(product_qty)-sum(terima_qty)  as qty_outstanding
                from 
                ( 
                    select 
                        a.partner_id as partner,a.name  ,a.id,  b.product_id, 0  as terima_qty,sum(b.product_qty) as product_qty  from purchase_order a 
                    inner join purchase_order_line b on a.id = b.order_id                 
                    group by  a.name  , b.product_id,a.partner_id,a.id
                                
                    union all 

                     select  
                        a.partner_id as partner,a.origin as name ,c.id,  b.product_id, sum(b.product_qty) as terima_qty, 0  as product_qty    from stock_picking a 
                    inner join stock_move b on a.id = b.picking_id  and a.state = 'done'
                    inner join purchase_order c on a.origin = c.name 
                    group by b.product_id,a.origin,a.partner_id,c.id  
                ) 
                aa
                where product_id=%s and partner=%s
                group by id,name , product_id,partner
            """
            # raise UserError(query+' '+'test2')
            list_of_dictionary = self._cr.execute(query,(self.product_id.id,self.vendor_id.id))
            list_of_dictionary =self.env.cr.dictfetchall()
            # raise UserError(str(self.vendor_id.id)+' '+str(self.purchase_id.id)+' '+str(self.product_id.id))

            for r in list_of_dictionary:
                data = self._fill_detail_outstanding(r)
                new_line = new_lines_outstanding.new(data)
                new_lines_outstanding += new_line
            self.product_ids += new_lines_outstanding
            # raise UserError(list_of_dictionary)
        #product  and purchase
        if self.product_id and not self.vendor_id and self.purchase_id :
            # raise UserError(str(self.product_id)+' '+str(self.purchase_id)+' '+str(self.vendor_id))
            query="""
                select 
                    partner as partner,name  as po_name,id as po_id, product_id,sum(terima_qty) as qty_received, sum(product_qty)  as product_qty, sum(product_qty)-sum(terima_qty)  as qty_outstanding
                from 
                ( 
                    select 
                        a.partner_id as partner,a.name  ,a.id,  b.product_id, 0  as terima_qty,sum(b.product_qty) as product_qty  from purchase_order a 
                    inner join purchase_order_line b on a.id = b.order_id                 
                    group by  a.name  , b.product_id,a.partner_id,a.id
                                
                    union all 

                     select  
                        a.partner_id as partner,a.origin as name ,c.id,  b.product_id, sum(b.product_qty) as terima_qty, 0  as product_qty    from stock_picking a 
                    inner join stock_move b on a.id = b.picking_id  and a.state = 'done'
                    inner join purchase_order c on a.origin = c.name 
                    group by b.product_id,a.origin,a.partner_id,c.id  
                ) 
                aa
                where product_id=%s and name=%s 
                group by id, name , product_id,partner
            """
            # raise UserError(query+' '+'test2')
            list_of_dictionary = self._cr.execute(query,(self.product_id.id,self.purchase_id.name))
            list_of_dictionary =self.env.cr.dictfetchall()
            # raise UserError(str(self.vendor_id.id)+' '+str(self.purchase_id.id)+' '+str(self.product_id.id))

            for r in list_of_dictionary:
                data = self._fill_detail_outstanding(r)
                new_line = new_lines_outstanding.new(data)
                new_lines_outstanding += new_line
            self.product_ids += new_lines_outstanding
            # raise UserError(list_of_dictionary)

        #vendor and purchase
        if not self.product_id and self.vendor_id and self.purchase_id :
            # raise UserError(str(self.product_id)+' '+str(self.purchase_id)+' '+str(self.vendor_id))
            query="""
                select 
                    partner as partner,name  as po_name,id as po_id, product_id,sum(terima_qty) as qty_received, sum(product_qty)  as product_qty, sum(product_qty)-sum(terima_qty)  as qty_outstanding
                from 
                ( 
                    select 
                        a.partner_id as partner,a.name  ,a.id,  b.product_id, 0  as terima_qty,sum(b.product_qty) as product_qty  from purchase_order a 
                    inner join purchase_order_line b on a.id = b.order_id                 
                    group by  a.name  , b.product_id,a.partner_id,a.id
                                
                    union all 

                     select  
                        a.partner_id as partner,a.origin as name ,c.id,  b.product_id, sum(b.product_qty) as terima_qty, 0  as product_qty    from stock_picking a 
                    inner join stock_move b on a.id = b.picking_id  and a.state = 'done'
                    inner join purchase_order c on a.origin = c.name 
                    group by b.product_id,a.origin,a.partner_id,c.id  
                ) 
                aa
                where partner=%s and name=%s 
                group by id,name , product_id,partner
            """
            # raise UserError(query+' '+'test2')
            list_of_dictionary = self._cr.execute(query,(self.vendor_id.id,self.purchase_id.name))
            list_of_dictionary =self.env.cr.dictfetchall()
            # raise UserError(str(self.vendor_id.id)+' '+str(self.purchase_id.id)+' '+str(self.product_id.id))

            for r in list_of_dictionary:
                data = self._fill_detail_outstanding(r)
                new_line = new_lines_outstanding.new(data)
                new_lines_outstanding += new_line
            self.product_ids += new_lines_outstanding
            # raise UserError(list_of_dictionary)
        if self.product_id and not self.purchase_id and not self.vendor_id:
            # raise UserError(str(self.product_id)+' '+str(self.purchase_id)+' '+str(self.vendor_id))
            query="""
                select 
                    partner as partner,name  as po_name,id as po_id, product_id,sum(terima_qty) as qty_received, sum(product_qty)  as product_qty, sum(product_qty)-sum(terima_qty)  as qty_outstanding
                from 
                ( 
                    select 
                        a.partner_id as partner,a.name  ,a.id,  b.product_id, 0  as terima_qty,sum(b.product_qty) as product_qty  from purchase_order a 
                    inner join purchase_order_line b on a.id = b.order_id                 
                    group by  a.name  , b.product_id,a.partner_id,a.id
                                
                    union all 

                     select  
                        a.partner_id as partner,a.origin as name ,c.id,  b.product_id, sum(b.product_qty) as terima_qty, 0  as product_qty    from stock_picking a 
                    inner join stock_move b on a.id = b.picking_id  and a.state = 'done'
                    inner join purchase_order c on a.origin = c.name 
                    group by b.product_id,a.origin,a.partner_id,c.id  
                ) 
                aa
                where product_id=%s 
                group by id,name , product_id,partner

            """
            # raise UserError(query+' '+'test2')
            list_of_dictionary = self._cr.execute(query,[self.product_id.id])
            list_of_dictionary =self.env.cr.dictfetchall()
            # raise UserError(str(self.vendor_id.id)+' '+str(self.purchase_id.id)+' '+str(self.product_id.id))

            for r in list_of_dictionary:
                data = self._fill_detail_outstanding(r)
                new_line = new_lines_outstanding.new(data)
                new_lines_outstanding += new_line
            self.product_ids += new_lines_outstanding
            # raise UserError(list_of_dictionary)
        

      
            
        if  not self.product_id and not self.purchase_id and self.vendor_id:
            query2="""
                select 
                    partner as partner,name  as po_name,id as po_id, product_id,sum(terima_qty) as qty_received, sum(product_qty)  as product_qty, sum(product_qty)-sum(terima_qty)  as qty_outstanding
                from 
                ( 
                    select 
                        a.partner_id as partner,a.name  ,a.id,  b.product_id, 0  as terima_qty,sum(b.product_qty) as product_qty  from purchase_order a 
                    inner join purchase_order_line b on a.id = b.order_id                 
                    group by  a.name  , b.product_id,a.partner_id,a.id
                                
                    union all 

                     select  
                        a.partner_id as partner,a.origin as name ,c.id,  b.product_id, sum(b.product_qty) as terima_qty, 0  as product_qty    from stock_picking a 
                    inner join stock_move b on a.id = b.picking_id  and a.state = 'done'
                    inner join purchase_order c on a.origin = c.name 
                    group by b.product_id,a.origin,a.partner_id,c.id  
                ) 
                aa
                where partner=%s 
                group by id,name , product_id,partner
            """

            # raise UserError(query+' '+'test1'+str(list_of_dictionary))
            list_of_dictionary2 = self._cr.execute(query2,[self.vendor_id.id])
            # raise UserError(query+' '+'test1'+str(list_of_dictionary2))
            list_of_dictionary2 =self.env.cr.dictfetchall()
            
            # raise UserError(str(list_of_dictionary))
            for r in list_of_dictionary2:
                data = self._fill_detail_outstanding(r)
                new_line = new_lines_outstanding.new(data)
                new_lines_outstanding += new_line
            self.product_ids += new_lines_outstanding

        if  not self.product_id and self.purchase_id and not self.vendor_id:
            query2="""
                select 
                    partner as partner,name  as po_name,id as po_id, product_id,sum(terima_qty) as qty_received, sum(product_qty)  as product_qty, sum(product_qty)-sum(terima_qty)  as qty_outstanding
                from 
                ( 
                    select 
                        a.partner_id as partner,a.name  ,a.id,  b.product_id, 0  as terima_qty,sum(b.product_qty) as product_qty  from purchase_order a 
                    inner join purchase_order_line b on a.id = b.order_id                 
                    group by  a.name  , b.product_id,a.partner_id,a.id
                                
                    union all 

                     select  
                        a.partner_id as partner,a.origin as name ,c.id,  b.product_id, sum(b.product_qty) as terima_qty, 0  as product_qty    from stock_picking a 
                    inner join stock_move b on a.id = b.picking_id  and a.state = 'done'
                    inner join purchase_order c on a.origin = c.name 
                    group by b.product_id,a.origin,a.partner_id,c.id  
                ) 
                aa
                where 
                name=%s
                group by id,name , product_id,partner
            """

            # raise UserError(query+' '+'test1'+str(list_of_dictionary))
            list_of_dictionary2 = self._cr.execute(query2,[self.purchase_id.name])
            # raise UserError(query+' '+'test1'+str(list_of_dictionary2))
            list_of_dictionary2 =self.env.cr.dictfetchall()
            
            # raise UserError(str(list_of_dictionary))
            for r in list_of_dictionary2:
                data = self._fill_detail_outstanding(r)
                new_line = new_lines_outstanding.new(data)
                new_lines_outstanding += new_line
            self.product_ids += new_lines_outstanding
              
        

        self.update({'fill_detail':False})
    
    def _fill_detail_outstanding(self,line):
        data = { 
                  'nama_vendor': line['partner'],
                  'nomor_po': line['po_name'],
                  'product_id': line['product_id'],
                  'product_qty': line['product_qty'],
                  # 'product_uom': line['product_uom'],
                  'qty_received': line['qty_received'],
                  'po_id': line['po_id'],
                  'qty_sisa': line['qty_outstanding']
                 }
        return data

class CreateCursorLine(models.TransientModel):
    _name = 'create.cursor.line.outstanding'

    line_id = fields.Many2one(comodel_name="purchase.order.line")
    line_id2 = fields.Many2one(comodel_name="stock_move")
    n_id = fields.Integer('ID')
    wizard_id = fields.Many2one(comodel_name="create.cursor.outstanding",string="Wizard",required=False,)
    nomor_po = fields.Char(string="Purchase Order")
    nama_vendor = fields.Many2one(comodel_name="res.partner")
    product_id = fields.Many2one(comodel_name="product.product")
    po_id = fields.Many2one(comodel_name="purchase.order")
    date_order = fields.Datetime(related="po_id.date_order")
    # product_qty = fields.Float(related="line_id.product_qty")
    # product_uom = fields.Many2one(comodel_name="product.uom")
    # product_id = fields.Char(string="nama Barang")
    product_qty = fields.Float(string="Qty PO")
    # product_uom = fields.Char(string="Satuan PO")
    qty_received = fields.Float(string="Qty Received")
    # product_received = fields.Many2one(comodel_name="product.uom")
    qty_sisa = fields.Float(string="Qty Outstanding")