from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict

class MutasiPersediaanWizard(models.TransientModel):
    _name = 'mutasi.persediaan.wizard'
    
    @api.multi
    def get_first_date(self):
        current_date = date.today()
        return date(current_date.year, current_date.month, 1)
    
    date_from = fields.Date('Dari Tanggal', default=get_first_date)
    date_to = fields.Date('Sampai Tanggal', default=date.today())
    type = fields.Selection([('rekap', 'Rekap'),
                             ('detail', 'Detail')], default='sum', string='Tipe')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Gudang')
    product_ids = fields.Many2many('product.product', string='Produk')
    
    @api.multi
    def view_mutasi_persediaan(self):
        if self.type == 'rekap':
            return self.view_rekap_mutasi_persediaan()
        else:
            return self.view_detail_mutasi_persediaan()
    
    ########################################### REKAP MUTASI PERSEDIAAN #####################################################
    @api.multi
    def view_rekap_mutasi_persediaan(self):
        datas = {}

    ########################################### DETAIL MUTASI PERSEDIAAN #####################################################
    @api.multi
    def view_detail_mutasi_persediaan(self):
        datas = {}
        datas['ids'] = [self['id']]
        datas['model'] = self._name
        datas['form'] = self.read()[0]
        datas['date_init'] = (datetime.strptime(self.date_from, '%Y-%m-%d') - relativedelta(days=1)).strftime('%d %B %Y')
        datas['date_from'] = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%d %B %Y')
        datas['date_to'] = datetime.strptime(self.date_to, '%Y-%m-%d').strftime('%d %B %Y')
        datas['product_ids'] = 'All'
        datas['warehouse_ids'] = 'All'
        datas['type'] = self.type == 'rekap' and 'Rekap Mutasi Persediaan' or 'Detail Mutasi Persediaan'
        datas['picking_type'] = {}
        compiled_data = {}
        where_query = ''
         
        if self.product_ids:
            datas['product_ids'] = ', '.join(map(str, [x.code for x in self['product_ids']]))
        if len(self.product_ids) > 1:
            where_query += " and sm.product_id in %s" % (str(tuple(self.product_ids.ids)))
        elif len(self.product_ids) == 1:
            where_query += " and sm.product_id = %s" % (tuple(self.product_ids.ids))
         
        if self.warehouse_ids:
            datas['warehouse_ids'] = ', '.join(map(str, [x.name for x in self['warehouse_ids']]))
        warehouse_ids = self.warehouse_ids if self.warehouse_ids else self.env['stock.warehouse'].search([])
        if len(warehouse_ids) > 1:
            where_query += " and sw.id in %s" % (str(tuple(warehouse_ids.ids)))
         
        elif len(warehouse_ids) == 1:
            where_query += " and sw.id = %s" % (tuple(warehouse_ids.ids))
            
        datas['pick_type'] = {}
        for wh in warehouse_ids:
            datas['pick_type'][wh.name] = {
                'In' : self.env['stock.picking.type'].search([('warehouse_id', '=', wh.id), ('code', '=', 'incoming')]).mapped('name') or [],
                'Out': self.env['stock.picking.type'].search([('warehouse_id', '=', wh.id), ('code', '=', 'outgoing')]).mapped('name') or []
            }
        ############# INITIAL ################
        query = """
               (select 
                    pp.default_code as product_code, 
                    pp.barcode as barcode, 
                    pt.name as product_name,  
                    sw.name as warehouse,
                    'Out' as direction, 
                    sum(aml.credit) as qty
                from 
                    stock_move sm
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join stock_location sls on sls.id=sm.location_id
                    LEFT JOIN stock_warehouse sw ON (sw.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sls.parent_left AND sl.parent_right >= sls.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    left join stock_location sld on (sld.id=sm.location_dest_id)
                    LEFT JOIN stock_warehouse swd ON (swd.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sld.parent_left AND sl.parent_right >= sld.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    left join account_move_line aml on (aml.product_id=sm.product_id and aml.name=sm.name and ((sp.id IS NULL and aml.ref is NULL) or aml.ref=sp.name) and aml.credit>0)
                     
                where
                    pt.type = 'product' and
                    sls.usage = 'internal' and 
                    sw.id is not null and
                    (swd.id is null or swd.id != sw.id) and
                    sm.state = 'done' and
                    sm.date < '%s' %s
                group by 
                    pp.default_code, 
                    pp.barcode,
                    pt.name, 
                    sls.name,
                    sw.name
                ) UNION ALL (
                select 
                    pp.default_code as product_code, 
                    pp.barcode as barcode, 
                    pt.name as product_name,  
                    sw.name as warehouse,
                    'In' as direction, 
                    sum(aml.debit) as qty
                from 
                    stock_move sm
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join stock_location sls on (sls.id=sm.location_id)
                    LEFT JOIN stock_warehouse sws ON (sws.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sls.parent_left AND sl.parent_right >= sls.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    
                    left join stock_location sld on (sld.id=sm.location_dest_id)
                    LEFT JOIN stock_warehouse sw ON (sw.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sld.parent_left AND sl.parent_right >= sld.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    left join account_move_line aml on (aml.product_id=sm.product_id and aml.name=sm.name and ((sp.id IS NULL and aml.ref is NULL) or aml.ref=sp.name) and aml.debit>0)
                where
                    pt.type = 'product' and
                    sld.usage = 'internal' and 
                    sw.id is not null and
                    (sws.id is null or sws.id != sw.id) and
                    sm.state = 'done' and
                    sm.date < '%s' %s
                group by 
                    pp.default_code, 
                    pp.barcode, 
                    pt.name, 
                    sld.name,
                    sw.name)
        """ % (self.date_from + ' 00:00:00', where_query, \
               self.date_from + ' 00:00:00', where_query)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()

        for move_line in data:
            product = move_line.get('product_code') and "[%s] %s" % (move_line['product_code'], move_line['product_name']) \
                        or move_line['product_name']
            direction = move_line['direction']
            warehouse = move_line['warehouse']
            tmw_code = move_line['product_code']
            barcode = move_line['barcode']
            kemasan = 'Pcs'
            description = move_line['product_name']
            qty = move_line['qty'] or 0
            
            if not compiled_data.get(warehouse):
                compiled_data[warehouse] = {}
            if not compiled_data[warehouse].get(product):
                compiled_data[warehouse][product] = {
                    'tmw_code': tmw_code,
                    'barcode': barcode,
                    'description': description,
                    'kemasan': kemasan,
                    'init_product': 0,
                    'In' : defaultdict(lambda:0),
                    'Out' : defaultdict(lambda:0)}
            compiled_data[warehouse][product]['init_product'] += qty if move_line['direction'] == 'In' else -qty
        
        ############# MUTATION ################
        query = """
               (select 
                    pp.default_code as product_code, 
                    pp.barcode as barcode, 
                    pt.name as product_name,  
                    sw.name as warehouse,
                    'Out' as direction, 
                    spt.name as pick_type,
                    sum(aml.credit) as qty
                from 
                    stock_move sm
                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join stock_picking_type spt on spt.id=sp.picking_type_id
                     
                    left join stock_location sls on (sls.id=sm.location_id)
                    LEFT JOIN stock_warehouse sw ON (sw.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sls.parent_left AND sl.parent_right >= sls.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    
                    left join stock_location sld on (sld.id=sm.location_dest_id)
                    LEFT JOIN stock_warehouse swd ON (swd.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sld.parent_left AND sl.parent_right >= sld.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    left join account_move_line aml on (aml.product_id=sm.product_id and aml.name=sm.name and ((sp.id IS NULL and aml.ref is NULL) or aml.ref=sp.name) and aml.credit>0)
                where
                    pt.type = 'product' and
                    sls.usage = 'internal' and 
                    sw.id is not null and
                    (swd.id is null or swd.id != sw.id) and
                    sm.state = 'done' and
                    sm.date >= '%s' and
                    sm.date <= '%s' %s
                group by 
                    spt.name, 
                    pp.default_code, 
                    pp.barcode,
                    pt.name, 
                    sls.name,
                    sw.name
                ) UNION ALL (
                select 
                    pp.default_code as product_code, 
                    pp.barcode as barcode, 
                    pt.name as product_name,  
                    sw.name as warehouse,
                    'In' as direction, 
                    spt.name as pick_type,
                    sum(aml.debit) as qty
                from 
                    stock_move sm
                    left join product_product pp on pp.id=sm.product_id
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join stock_picking sp on sp.id=sm.picking_id
                    left join stock_picking_type spt on spt.id=sp.picking_type_id
                    
                    left join stock_location sls on (sls.id=sm.location_id)
                    LEFT JOIN stock_warehouse sws ON (sws.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sls.parent_left AND sl.parent_right >= sls.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    
                    left join stock_location sld on (sld.id=sm.location_dest_id)
                    LEFT JOIN stock_warehouse sw ON (sw.id = 
                        (SELECT
                            swi.id
                        FROM 
                            stock_location sl
                            LEFT JOIN stock_warehouse swi ON (swi.view_location_id=sl.id)
                        WHERE
                            sl.parent_left <= sld.parent_left AND sl.parent_right >= sld.parent_right AND swi.id IS NOT NULL LIMIT 1)
                    )
                    left join account_move_line aml on (aml.product_id=sm.product_id and aml.name=sm.name and ((sp.id IS NULL and aml.ref is NULL) or aml.ref=sp.name) and aml.debit>0)
                where
                    pt.type = 'product' and
                    sld.usage = 'internal' and 
                    sw.id is not null and
                    (sws.id is null or sws.id != sw.id) and
                    sm.state = 'done' and
                    sm.date >= '%s' and
                    sm.date <= '%s' %s
                group by 
                    spt.name, 
                    pp.default_code, 
                    pp.barcode,
                    pt.name, 
                    sld.name,
                    sw.name)
        """ % (self.date_from + ' 00:00:00', self.date_to + ' 23:59:59', where_query, \
               self.date_from + ' 00:00:00', self.date_to + ' 23:59:59', where_query)
        self.sudo().env.cr.execute(query)
        data = self.sudo().env.cr.dictfetchall()
        for move_line in data:
            product = move_line.get('product_code') and "[%s] %s" % (move_line['product_code'], move_line['product_name']) \
                        or move_line['product_name']
            direction = move_line['direction']
            warehouse = move_line['warehouse']
            tmw_code = move_line['product_code']
            barcode = move_line['barcode']
            kemasan = 'Pcs'
            description = move_line['product_name']
            pick_type = move_line['pick_type']
            qty = move_line['qty'] or 0
            
            if not compiled_data.get(warehouse):
                compiled_data[warehouse] = {}
            if not compiled_data[warehouse].get(product):
                compiled_data[warehouse][product] = {'tmw_code': tmw_code, 'barcode': barcode,
                                                     'description': description, 'kemasan': kemasan,
                                                     'init_product': 0, 'In' : defaultdict(lambda:0), 'Out' :  defaultdict(lambda:0)}
            if direction == 'In':
                compiled_data[warehouse][product][direction][pick_type] += qty
            elif direction == 'Out':
                compiled_data[warehouse][product][direction][pick_type] += qty
            if pick_type not in datas['pick_type'][warehouse][direction]:
                datas['pick_type'][warehouse][direction].append(pick_type)
        datas['csv'] = compiled_data
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'detail.mutasi.persediaan.xls',
            'nodestroy': True,
            'datas': datas,
        }
           
