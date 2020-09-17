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
              #TOTAL VBILL
              ['VALAS', 10],
              ['IDR', 10],
        ]
    
class bill_valas_summary_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Laporan Bills Summary (Valas)'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(8)   
        
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

        ws.write_merge(row_count, row_count, 16, 17, 'SUBTOTAL', cell_style_center)

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
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
                
                for lines in partner[1]['bills'][bill]['biaya_service']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1

                for lines in partner[1]['bills'][bill]['jasa_lain']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
                    
                for lines in partner[1]['bills'][bill]['min_order_qty']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
                    
                for lines in partner[1]['bills'][bill]['bi_lokal']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
                      
                for lines in partner[1]['bills'][bill]['bi_import']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
 
                for lines in partner[1]['bills'][bill]['pph22']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
                    
                for lines in partner[1]['bills'][bill]['pph23']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
 
                for lines in partner[1]['bills'][bill]['pph23s']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
                    
                for lines in partner[1]['bills'][bill]['retur_pembelian']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
 
                for lines in partner[1]['bills'][bill]['price_adjustment']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
 
                for lines in partner[1]['bills'][bill]['lain']:
                    col_count = 4
                    for line in lines[:12]:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    ws.write(row_count, col_count, lines[-2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, lines[-1], c_cell_style)
                    row_count +=1
                 
                ws.write_merge(row_count, row_count, 10, 15, 'TOTAL %s : %s' % (partner[1]['bills'][bill]['number'], partner[0]), cell_style_grey)
                index_col = 16
                while index_col <= 17:
                    sum_cell_start = xlwt.Utils.rowcol_to_cell(sum_row, index_col)
                    sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, index_col)                    
                    ws.write(row_count, index_col, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), cell_style_grey)
                    col_count += 1
                    index_col += 1
                row_count += 1         
                col_count = 0
        
        #GRAND TOTAL
        row_count += 1
        ws.write_merge(row_count, row_count, 10, 15, 'GRAND TOTAL', cell_style_grey)
        ws.write(row_count, 16, data['grand_total'][-2], cell_style_grey)
        ws.write(row_count, 17, data['grand_total'][-1], cell_style_grey)
            
        pass
 
bill_valas_summary_xls('report.bill.valas.summary.xls', 'account.invoice', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
