import re
import time
import xlwt, operator
from openerp.report import report_sxw
from report_engine_xls import report_xls
from openerp.tools.translate import _
 
class ReportStatus(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(ReportStatus, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'cr': cr,
            'uid': uid,
            'time': time,
        })
        
columns = [
              ['NO BILL', 10],
              ['VENDOR', 20],
              ['COA HUTANG', 20],
              ['NO KB', 10],
              ['NO PO', 10],
              ['TGL BILL', 10],
              ['NO STPB', 10],
              ['TGL STPB', 10],
              ['PRODUK', 10],
              ['NOTES', 10],
              ['VENDOR REF', 10],
              ['QTY GR/IR', 10],
              ['SATUAN', 10],
              ['HARGA PO', 10],
              ['MATA UANG', 10],
              ['KURS', 10],
              #GR/IR
              ['VALAS', 10],
              ['IDR', 10],
              #BIAYA SERVICE KENDARAAN
              ['VALAS', 10],
              ['IDR', 10],
              #BIAYA PERBAIKAN / JASA LAINNYA
              ['VALAS', 10],
              ['IDR', 10],
              #SURCHARGE
              ['VALAS', 10],
              ['IDR', 10],
              #BI LOKAL
              ['VALAS', 10],
              ['IDR', 10],
              #BI IMPORT
              ['VALAS', 10],
              ['IDR', 10],
              #PPH22 DIBAYAR DIMUKA
              ['VALAS', 10],
              ['IDR', 10],
              #PPH23
              ['VALAS', 10],
              ['IDR', 10],
              #PPH23 SEBELUM
              ['VALAS', 10],
              ['IDR', 10],
              #RETUR PEMBELIAN
              ['VALAS', 10],
              ['IDR', 10],
              #PURCHASE ADJ
              ['VALAS', 10],
              ['IDR', 10],
              #LAIN-LAIN
              ['VALAS', 10],
              ['IDR', 10],
              #TOTAL VBILL
              ['VALAS', 10],
              ['IDR', 10],
        ]
    
class bill_valas_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Laporan Bills (Valas)'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(8)   
        ws.set_vert_split_pos(11)     
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'VENDOR BILLS (VALAS) - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['center'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)         
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        cell_style_center_grey = xlwt.easyxf(_xs['bold'] + _xs['borders_all'] + _xs['center']+ _xs['fill_grey'], num_format_str=report_xls.decimal_format)       
        cell_style_grey = xlwt.easyxf(_xs['bold'] + _xs['borders_all'] + _xs['fill_grey'], num_format_str=report_xls.decimal_format)             
        ws.write_merge(2, 2, 0, 2, 'Date', cell_style_center)
        ws.write_merge(2, 2, 3, 7, 'Vendor Filters', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 2, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 3, 7, data['partner_ids'], cell_style_param)

        c_hdr_cell_style = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_title_cell_style = xlwt.easyxf(_xs['bold'], num_format_str=report_xls.decimal_format)
        c_cell_style = xlwt.easyxf(_xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_cell_style_center = xlwt.easyxf(_xs['borders_all'] + _xs['center'],
            num_format_str=report_xls.decimal_format)
        cell_style_red = xlwt.easyxf(_xs['bold'] + _xs['fill_red'] + _xs['borders_all'] + _xs['center'],
            num_format_str=report_xls.decimal_format)

        row_count = 6
        col_count = 0

        ws.write_merge(row_count-1, row_count-1, 16, 17, 'GR/IR', cell_style_center)
        ws.write_merge(row_count, row_count, 16, 17, '2106010000', cell_style_center)

        ws.write_merge(row_count-1, row_count-1, 18, 19, 'BIAYA SERVICE KENDARAAN', cell_style_center)
        ws.write_merge(row_count, row_count, 18, 19, '4102051900', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 20, 21, 'BIAYA PERBAIKAN/JASA LAIN', cell_style_center)
        ws.write_merge(row_count, row_count, 20, 21, '4102063100', cell_style_center)

        ws.write_merge(row_count-2, row_count-2, 22, 29, 'PENAMBAHAN VENDOR BILL', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 22, 23, 'MIN ORDER QTY/SURCHAGE', cell_style_center)
        ws.write_merge(row_count, row_count, 22, 23, '4102061100', cell_style_center)

        ws.write_merge(row_count-1, row_count-1, 24, 25, 'BI LOKAL', cell_style_center)
        ws.write_merge(row_count, row_count, 24, 25, '6405110000', cell_style_center)

        ws.write_merge(row_count-1, row_count-1, 26, 27, 'BI IMPORT', cell_style_center)
        ws.write_merge(row_count, row_count, 26, 27, '4101010400', cell_style_center)

        ws.write_merge(row_count-1, row_count-1, 28, 29, 'PPH 22 DIBYR DMK', cell_style_center)
        ws.write_merge(row_count, row_count, 28, 29, '1108020200', cell_style_center)

        ws.write_merge(row_count-2, row_count-2, 30, 35, 'PENGURANGAN VENDOR BILL', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 30, 31, 'PPH 23 TH 2020 + IA', cell_style_center)
        ws.write_merge(row_count, row_count, 30, 31, '2108020300', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 32, 33, 'PPH 23 SEBELUM TH 2020', cell_style_center)
        ws.write_merge(row_count, row_count, 32, 33, '1109080000', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 34, 35, 'RETUR PEMBELIAN', cell_style_center)
        ws.write_merge(row_count, row_count, 34, 35, '2106010000', cell_style_center)

        ws.write_merge(row_count-2, row_count-2, 36, 37, 'KOREKSI HARGA/PEMBULATAN', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 36, 37, 'PRICE PURCHASE ADJ', cell_style_center)
        ws.write_merge(row_count, row_count, 36, 37, '4203040000', cell_style_center)

        ws.write_merge(row_count, row_count, 38, 39, 'LAIN-LAIN', cell_style_center)
        ws.write_merge(row_count, row_count, 40, 41, 'TOTAL BILL DIBAYAR', cell_style_center)

        row_count += 1
        for column in columns:
            ws.col(col_count).width = 256 * column[1]
            ws.write(row_count, col_count, column[0], cell_style_center)
            col_count += 1

        row_count += 1
        col_count = 0
        for partner in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            for bill in partner[1]['bills']:
                sum_row = row_count
                ws.write_merge(row_count, row_count, col_count, col_count, partner[1]['bills'][bill]['number'], c_cell_style)
                col_count += 1
                ws.write_merge(row_count, row_count, col_count, col_count, partner[1]['bills'][bill]['partner'], c_cell_style)
                col_count += 1
                ws.write_merge(row_count, row_count, col_count, col_count, partner[1]['bills'][bill]['account'], c_cell_style)
                col_count += 1
                ws.write_merge(row_count, row_count, col_count, col_count, partner[1]['bills'][bill]['kb'], c_cell_style)
                col_count += 1

                row_start = row_count
                for lines in partner[1]['bills'][bill]['grir']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                
                for lines in partner[1]['bills'][bill]['biaya_service']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['jasa_lain']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                
                
                for lines in partner[1]['bills'][bill]['min_order_qty']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                
                
                for lines in partner[1]['bills'][bill]['bi_lokal']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['bi_import']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['pph22']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['pph23']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['pph23s']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['retur_pembelian']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['price_adjustment']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                

                for lines in partner[1]['bills'][bill]['lain']:
                    col_count = 4
                    for line in lines:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    row_count +=1   
                    col_count = 16
                    cell_grir_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_grir_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_service_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_service_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2  
                    cell_jasa_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_jasa_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2
                    cell_surchage_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_surchage_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2  
                    cell_bi_lokal_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_lokal_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)   
                    col_count += 2 
                    cell_bi_import_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_bi_import_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph22_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph22_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_pph23s_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_pph23s_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_retur_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_retur_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_adj_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_adj_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  
                    col_count += 2 
                    cell_lain_valas = xlwt.Utils.rowcol_to_cell(row_count -1, col_count)
                    cell_lain_idr = xlwt.Utils.rowcol_to_cell(row_count -1, col_count + 1)  

                    ws.write(row_count -1, 40, xlwt.Formula('(' + cell_grir_valas + '+' + cell_service_valas + '+' + cell_jasa_valas + '+' + cell_surchage_valas +\
                        '+' + cell_bi_lokal_valas + '+' + cell_bi_import_valas + '+' + cell_pph22_valas + '+' + cell_pph23_valas + '+' + cell_pph23s_valas + '+' + cell_retur_valas + '+' + cell_adj_valas + '+' + cell_lain_valas + ')'), c_title_cell_style)
                    ws.write(row_count -1, 41, xlwt.Formula('(' + cell_grir_idr + '+' + cell_service_idr + '+' + cell_jasa_idr + '+' + cell_surchage_idr +\
                        '+' + cell_bi_lokal_idr + '+' + cell_bi_import_idr + '+' + cell_pph22_idr + '+' + cell_pph23_idr + '+' + cell_pph23s_idr + '+' + cell_retur_idr + '+' + cell_adj_idr + '+' + cell_lain_idr + ')'), c_title_cell_style)
                
                
                ws.write_merge(row_count, row_count, 10, 15, 'TOTAL %s : %s' % (partner[1]['bills'][bill]['number'], partner[0]), cell_style_grey)
                index_col = 16
                while index_col <= 41:
                    sum_cell_start = xlwt.Utils.rowcol_to_cell(sum_row, index_col)
                    sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, index_col)                    
                    ws.write(row_count, index_col, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), cell_style_grey)
                    col_count += 1
                    index_col += 1
                row_count += 1         
                col_count = 0
        
        #GRAND TOTAL
        row_count += 2
        ws.write_merge(row_count, row_count, 10, 15, 'GRAND TOTAL', cell_style_grey)
        col_count = 16
        for line in data['grand_total']:
            ws.write(row_count, col_count, line, cell_style_grey)
            col_count += 1 
            
        pass
 
bill_valas_xls('report.bill.valas.xls', 'account.invoice', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
