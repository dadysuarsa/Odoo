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
              ['Code', 10],
              ['Account', 40],
              ['Type', 20],
              ['Initial Balance', 15],
              ['Debit', 15],
              ['Credit', 15],
              ['Ending Balance', 20],
              #Textile
              ['Debit', 15],
              ['Credit', 15],
              #GARMENT
              ['Debit', 15],
              ['Credit', 15],
              #TRADING
              ['Debit', 15],
              ['Credit', 15],
              #LIVIN
              ['Debit', 15],
              ['Credit', 15],
              #OTHER
              ['Debit', 15],
              ['Credit', 15]
            ]
    
class trial_balance_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Trial Balance'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(6)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'TRIAL BALANCE - ' + data['company_name'], title_style)
                 
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 1, 'Date', cell_style_center)
        ws.write_merge(2, 2, 2, 5, 'Account Filters', cell_style_center)
        ws.write_merge(2, 2, 6, 6, 'Target Moves', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 1, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 2, 5, data['account_ids'], cell_style_param)
        ws.write_merge(3, 3, 6, 6, data['target_move'], cell_style_param)

        c_hdr_cell_style = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_hdr_cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['center'],
            num_format_str=report_xls.decimal_format)
        c_hdr_cell_style_right = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        c_hdr_cell_style_left = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['left'],
            num_format_str=report_xls.decimal_format)
        c_title_cell_style = xlwt.easyxf(_xs['bold'])
        c_cell_style = xlwt.easyxf(_xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_cell_style_bold = xlwt.easyxf(_xs['borders_all'] + _xs['bold'],
            num_format_str=report_xls.decimal_format)
        c_italic_cell_style = xlwt.easyxf(_xs['italic'] + _xs['borders_all'])
        c_title_cell_style_grey = xlwt.easyxf(_xs['bold']+ _xs['fill_grey'], num_format_str=report_xls.decimal_format)
        
        row_count = 5
        col_count = 0
        for column in columns:
            ws.col(col_count).width = 256 * column[1]
            ws.write(row_count, col_count, column[0], c_hdr_cell_style)
            col_count += 1

        ws.write_merge(row_count - 1, row_count - 1, 3, 6, 'ALL DIVISI', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 7, 8, 'TEXTILE', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 9, 10, 'GARMENT', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 11, 12, 'TRADING', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 13, 14, 'LIVIN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 15, 16, 'OTHER', cell_style_center)
        
        col_count = 0
        row_count += 1
        row_start = row_count
        for line in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            for account_info in line[1].get('account_info'):
                ws.write(row_count, col_count, account_info, c_cell_style)
                col_count += 1
            ws.write(row_count, col_count, line[1].get('init_all'), c_cell_style)
            col_count += 1
            ws.write(row_count, col_count, line[1].get('debit_all'), c_cell_style)
            col_count += 1
            ws.write(row_count, col_count, line[1].get('credit_all'), c_cell_style)
            col_count += 1
            cell_init = xlwt.Utils.rowcol_to_cell(row_count,col_count-3)
            cell_debit = xlwt.Utils.rowcol_to_cell(row_count,col_count-2)
            cell_credit = xlwt.Utils.rowcol_to_cell(row_count,col_count-1)
            ws.write(row_count, col_count, xlwt.Formula(cell_init+'+'+cell_debit+'-'+cell_credit), c_cell_style)
            
            col_count += 1
            ws.write(row_count, col_count, line[1].get('debit_textile'), c_cell_style)
            col_count += 1
            ws.write(row_count, col_count, line[1].get('credit_textile'), c_cell_style)

            col_count += 1
            ws.write(row_count, col_count, line[1].get('debit_garment'), c_cell_style)
            col_count += 1
            ws.write(row_count, col_count, line[1].get('credit_garment'), c_cell_style)
            
            col_count += 1
            ws.write(row_count, col_count, line[1].get('debit_trading'), c_cell_style)
            col_count += 1
            ws.write(row_count, col_count, line[1].get('credit_trading'), c_cell_style)
            
            col_count += 1
            ws.write(row_count, col_count, line[1].get('debit_livin'), c_cell_style)
            col_count += 1
            ws.write(row_count, col_count, line[1].get('credit_livin'), c_cell_style)

            col_count += 1
            ws.write(row_count, col_count, line[1].get('debit_other'), c_cell_style)
            col_count += 1
            ws.write(row_count, col_count, line[1].get('credit_other'), c_cell_style)
            
            row_count += 1    
            col_count = 0
        col_count = 3
        row_count += 1
        ws.write_merge(row_count, row_count, 0, 2, 'GRAND TOTAL', c_title_cell_style_grey)
        while col_count <= 16:
            sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start, col_count)
            sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 2, col_count)
            ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_title_cell_style_grey)
            col_count += 1
        pass
 
trial_balance_xls('report.trial.balance.xls', 'account.move.line', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
