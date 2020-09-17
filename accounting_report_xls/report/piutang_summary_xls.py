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
        ['BUYER', 20],
        ['NO. INVOICE', 20],
        ['TGL. INVOICE', 10],
        ['NILAI INVOICE', 20],
        ['MATA UANG', 10],
        ['NO. BM/JM', 20],
        ['TGL. BM/JM', 10],
        ['NILAI PEMBAYARAN', 20],
        ['MATA UANG', 10],
        ['KETERANGAN', 20],
        ['OUTSTANDING AR', 20],
    ]
    
class piutang_summary_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Laporan Hutang by Buyer'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(7)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'LAPORAN HUTANG by BUYER - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 2, 'Period', cell_style_center)
        ws.write_merge(2, 2, 3, 3, 'Mata Uang', cell_style_center)
        ws.write_merge(2, 2, 4, 4, 'Inv. Status', cell_style_center)
        ws.write_merge(2, 2, 5, 10, 'Customer Filters', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 2, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 3, 3, data['type'], cell_style_param)
        ws.write_merge(3, 3, 4, 4, data['invoice_status'], cell_style_param)
        ws.write_merge(3, 3, 5, 10, data['partner_ids'], cell_style_param)

        c_hdr_cell_style = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_hdr_cell_style_grey = xlwt.easyxf(_xs['bold'] + _xs['fill_grey'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_cell_style = xlwt.easyxf(_xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_cell_style_bold = xlwt.easyxf(_xs['borders_all']+ _xs['bold'],
            num_format_str=report_xls.decimal_format)
        
        row_count = 6
        col_count = 0    
        
        ws.write_merge(row_count-1, row_count-1, 1, 4, 'INVOICE', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 5, 9, 'PEMBAYARAN', cell_style_center)

        for column in columns:
            ws.col(col_count).width = 256 * column[1]
            ws.write(row_count, col_count, column[0], cell_style_header)
            col_count += 1
        
        has_payment = False
        for partner in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            row_count += 1
            ws.write_merge(row_count, row_count, 0, 10, partner[0], c_hdr_cell_style)
            row_start = row_count
            for invoice in partner[1]['invoices']:
                col_count = 0
                ws.write(row_count + 1, 10, partner[1]['invoices'][invoice]['residual'], c_cell_style_bold)
                for data_invoice in partner[1]['invoices'][invoice]['invoice_info']:
                    row_count += 1
                    for line in data_invoice:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                has_payment = False
                for payments in partner[1]['invoices'][invoice]['payments']:
                    for pay in payments:
                        if pay != []:
                            has_payment = True
                    if not has_payment:
                        continue
                    for payment in payments:
                        col_count = 5
                        for line in payment:
                            ws.write(row_count, col_count, line, c_cell_style)
                            col_count += 1
                        row_count += 1
                if has_payment:
                    row_count -= 1
                col_count = 0
            
            col_count = 3
            row_count += 1
            while col_count < 4:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1
            while col_count < 7:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
                col_count += 1
            while col_count < 8:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1
            while col_count < 10:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
                col_count += 1
            while col_count < 11:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1
            ws.write_merge(row_count, row_count, 0, 2, 'TOTAL %s' %(partner[0]), c_hdr_cell_style_grey)
            
        #GRAND TOTAL
        row_count += 2
        col_count = 0
        for line in data['grand_total']:
            ws.write(row_count, col_count, line, c_hdr_cell_style_grey)
            col_count += 1 

        pass
 
piutang_summary_xls('report.piutang.summary.xls', 'account.invoice', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)