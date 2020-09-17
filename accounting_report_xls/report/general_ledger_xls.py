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
              ['Date', 13],
              ['Divisi', 10],
              ['Mutasi Bank/Cash', 10],
              ['Entry', 20],
              ['Journal', 10],
              ['Account', 10],
              ['Account Name', 10],
              ['Partner', 20],
              ['Label', 35],
              ['Counterpart', 20],
              ['Counterpart Name', 20],
              ['Initial Balance', 15],
              ['Debit', 15],
              ['Credit', 15],
              ['Balance without Initial Balance', 20],
              ['Balance with Initial Balance', 20]
            ]
    
class general_ledger_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('General Ledger'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(4)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'GENERAL LEDGER - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['wrap'], num_format_str=report_xls.decimal_format)         
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 2, 'Date', cell_style_center)
        ws.write_merge(2, 2, 3, 7, 'Account Filters', cell_style_center)
        ws.write_merge(2, 2, 8, 9, 'Target Moves', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 2, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 3, 7, data['account_ids'], cell_style_param)
        ws.write_merge(3, 3, 8, 9, data['target_move'], cell_style_param)

        c_hdr_cell_style = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_title_cell_style = xlwt.easyxf(_xs['bold'], num_format_str=report_xls.decimal_format)
        c_cell_style = xlwt.easyxf(_xs['borders_all'],
            num_format_str=report_xls.decimal_format)

        row_count = 5
        col_count = 0
        for account in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            ws.write_merge(row_count, row_count, 0, 0, account[0], cell_style_header)
            col_count += 1
            while col_count <= 15:
                ws.write_merge(row_count, row_count, col_count, col_count, '', cell_style_header)
                col_count += 1
                
            row_count += 1
            col_count = 0
            for column in columns:
                ws.col(col_count).width = 256 * column[1]
                ws.write(row_count, col_count, column[0], c_hdr_cell_style)
                col_count += 1
                
            row_count += 1
            ws.write_merge(row_count, row_count, 9, 10, 'Initial Balance on Account', c_title_cell_style)
            ws.write_merge(row_count, row_count, 11, 11, (account[1]['init_debit'] - account[1]['init_credit']) or 0.0, c_title_cell_style)
            
            col_count = 0
            row_count += 1
            
            cell_debit_start = xlwt.Utils.rowcol_to_cell(row_count-1, 12)
            cell_credit_start = xlwt.Utils.rowcol_to_cell(row_count-1, 13)
            cell_balance_start = xlwt.Utils.rowcol_to_cell(row_count-1, 14)
            for move_line in account[1]['move_line']:
                for line in move_line:
                    ws.write(row_count, col_count, line, c_cell_style)
                    col_count += 1  
                #Balance without IB
                cell_debit = xlwt.Utils.rowcol_to_cell(row_count,col_count-2)
                cell_credit = xlwt.Utils.rowcol_to_cell(row_count,col_count-1)
                ws.write(row_count, col_count, xlwt.Formula(cell_debit+'-'+cell_credit), c_cell_style)
                col_count += 1
                #Balance with IB
                if account[1]['move_line'].index(move_line) == 0:
                    cell_balance = xlwt.Utils.rowcol_to_cell(row_count-1, 11)
                else:
                    cell_balance = xlwt.Utils.rowcol_to_cell(row_count-1, col_count)
                cell_debit = xlwt.Utils.rowcol_to_cell(row_count,col_count-3)
                cell_credit = xlwt.Utils.rowcol_to_cell(row_count,col_count-2)
                ws.write(row_count, col_count, xlwt.Formula(cell_balance+'+'+cell_debit+'-'+cell_credit), c_cell_style)
                
                col_count = 0
                row_count += 1
            
            ws.write_merge(row_count, row_count, 0, 8, account[0], cell_style_header)
            ws.write_merge(row_count, row_count, 9, 11, 'Ending Balance on Account', cell_style_header)
            col_count = 12
            
            cell_debit_end = xlwt.Utils.rowcol_to_cell(row_count-1, 12)
            cell_credit_end = xlwt.Utils.rowcol_to_cell(row_count-1, 13)
            cell_balance_end = xlwt.Utils.rowcol_to_cell(row_count-1, 14)
            if not account[1]['move_line']:
                cell_debit_end = cell_debit_start
                cell_credit_end = cell_credit_start
                cell_balance_end = cell_balance_start
            ws.write(row_count, col_count, xlwt.Formula('sum('+cell_debit_start+':'+cell_debit_end+')'), cell_style_header)
            col_count += 1
            ws.write(row_count, col_count, xlwt.Formula('sum('+cell_credit_start+':'+cell_credit_end+')'), cell_style_header)
            col_count += 1
            ws.write(row_count, col_count, xlwt.Formula('sum('+cell_balance_start+':'+cell_balance_end+')'), cell_style_header)
            col_count += 1
            
            cell_ending_balance = xlwt.Utils.rowcol_to_cell(row_count-1, 15)
            cell_debit_bal = xlwt.Utils.rowcol_to_cell(row_count, col_count-3)
            cell_credit_bal = xlwt.Utils.rowcol_to_cell(row_count, col_count-2)
            ws.write(row_count, col_count, xlwt.Formula(cell_ending_balance), cell_style_header)
            
            row_count += 2      
            col_count = 0
            
        pass
 
general_ledger_xls('report.general.ledger.xls', 'account.move.line', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
