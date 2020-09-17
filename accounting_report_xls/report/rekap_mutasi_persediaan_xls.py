import time
import xlwt, operator
from odoo.report import report_sxw
from report_engine_xls import report_xls
from odoo.tools.translate import _
 
class ReportStatus(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(ReportStatus, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'cr': cr,
            'uid': uid,
            'time': time,
        })
        
        
_xs = report_xls.xls_styles
style_title = xlwt.easyxf(_xs['xls_title'])
style_blue = xlwt.easyxf(_xs['wrap'] + _xs['bold'] + _xs['fill_blue'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
style_blue_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['center'] + _xs['borders_all'])
style_blue_center.alignment.middle = 1
style_yellow = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
style_yellow_right = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['right'], num_format_str=report_xls.decimal_format)
style_yellow_percent = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'], num_format_str=report_xls.percentage_format)
style_normal_bold = xlwt.easyxf(_xs['bold'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
style_normal = xlwt.easyxf(_xs['borders_all'], num_format_str=report_xls.decimal_format)
style_normal_date = xlwt.easyxf(_xs['borders_all'], num_format_str=report_xls.date_format)
style_normal_center = xlwt.easyxf(_xs['wrap'] + _xs['top'] + _xs['center'] + _xs['borders_all'])  
style_normal_italic = xlwt.easyxf(_xs['italic'] + _xs['borders_all'])
style_normal_percent = xlwt.easyxf(_xs['borders_all'], num_format_str=report_xls.percentage_format)

columns = [
              ['Kode TMW', 12],
              ['Deskripsi', 70],
              ['Isi Kemasan (Pcs/Cs)', 14],
              ['Saldo Awal', 17],
              ['Amount Masuk', 17],
              ['Amount Keluar', 17],
              ['Saldo Akhir', 17]
            ]

class rekap_mutasi_persediaan_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Rekap Mutasi Persediaan'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape 
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(7)    
        
        ws.write_merge(0, 0, 0, 5, 'REKAP MUTASI PERSEDIAAN', style_title)
        ws.write_merge(2, 2, 0, 1, 'Tanggal', style_blue_center)
        ws.write_merge(2, 2, 2, 2, 'Filter Produk', style_blue_center)
        ws.write_merge(2, 2, 3, 6, 'Filter Gudang', style_blue_center)
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 1, data['date_from'] + ' - ' + data['date_to'], style_normal_center)
        ws.write_merge(3, 3, 2, 2, data['product_ids'], style_normal_center)
        ws.write_merge(3, 3, 3, 6, data['warehouse_ids'], style_normal_center)
        
        col_count = 0
        row_count = 5
        
        for warehouse in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            ws.write_merge(row_count, row_count, 0, 2, warehouse[0], style_blue)
            ws.write(row_count, 3, data['date_init'], style_yellow)
            row_count += 1
            for column in columns:
                if column[0] not in ['Amount Masuk', 'Amount Keluar']:
                    ws.write(row_count, col_count, column[0], style_blue)
                    ws.col(col_count).width = 256 * column[1]
                    col_count += 1
                else:
                    direction = 'In' if column[0] == 'Amount Masuk' else 'Out'
                    pick_types = data['pick_type'][warehouse[0]][direction]
                    ws.write_merge(row_count - 1, row_count - 1, col_count, col_count + len(pick_types) - 1, column[0], style_blue_center)
                    for pick_type in pick_types:
                        ws.write(row_count, col_count, pick_type or 'Adjustment', style_blue)
                        ws.col(col_count).width = 256 * column[1]
                        col_count += 1
            ws.write(row_count - 1, col_count - 1, data['date_to'], style_yellow)
            row_count += 1
            col_count = 0
            for product in warehouse[1]:
                ws.write(row_count, col_count, warehouse[1][product]['tmw_code'], style_normal)
                col_count += 1
                ws.write(row_count, col_count, warehouse[1][product]['description'], style_normal)
                col_count += 1
                ws.write(row_count, col_count, warehouse[1][product]['kemasan'], style_normal)
                col_count += 1
                ws.write(row_count, col_count, warehouse[1][product]['init_product'], style_normal_bold)
                col_count += 1
                col_total = []
                for direction in ['In', 'Out']:
                    col_total.append(xlwt.Utils.rowcol_to_cell(row_count, col_count))
                    for pick_type in data['pick_type'][warehouse[0]][direction]:
                        ws.write(row_count, col_count, warehouse[1][product][direction].get(pick_type or 'null', 0), style_normal)
                        col_count += 1
                    col_total.append(xlwt.Utils.rowcol_to_cell(row_count, col_count - 1))
                cell_init = xlwt.Utils.rowcol_to_cell(row_count, 3)
                cell_in = 'SUM(' + col_total[0] + ':' + col_total[1] + ')'
                cell_out = 'SUM(' + col_total[2] + ':' + col_total[3] + ')'
                ws.write(row_count, col_count, xlwt.Formula(cell_init + '+' + cell_in + '-' + cell_out), style_normal_bold)
 
                row_count += 1
                col_count = 0
            row_count += 1
        pass
        
rekap_mutasi_persediaan_xls('report.rekap.mutasi.persediaan.xls', 'stock.move', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
