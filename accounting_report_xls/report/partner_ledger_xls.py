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
              ['   Date', 15],
              ['Entry', 20],
              ['Journal', 10],
              ['Label', 35],
              ['Rec', 5],
              ['Debit', 20],
              ['Credit', 20],
              ['Balance', 25]
            ]
    
class partner_ledger_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Partner Ledger'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(4)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'PARTNER LEDGER - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 2, 'Date', cell_style_center)
        ws.write_merge(2, 2, 3, 4, 'Account Filter', cell_style_center)
        ws.write_merge(2, 2, 5, 6, 'Partner Filter', cell_style_center)
        ws.write_merge(2, 2, 7, 7, 'Target Moves', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 2, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 3, 4, data['account_ids'], cell_style_param)
        ws.write_merge(3, 3, 5, 6, data['partner_ids'], cell_style_param)
        ws.write_merge(3, 3, 7, 7, data['target_move'], cell_style_param)

        c_hdr_cell_style = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_title_cell_style = xlwt.easyxf(_xs['bold'], num_format_str=report_xls.decimal_format)
        c_cell_style = xlwt.easyxf(_xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        
        row_count = 5
        col_count = 0
        for account in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            ws.write_merge(row_count, row_count, 0, 7, account[0], cell_style_header)
            row_count += 1
            if not account[1]['partner']:
                continue
            
            for partner in sorted(account[1]['partner'].items(), key=operator.itemgetter(0)):
                ws.write_merge(row_count, row_count, 0, 7, partner[0], c_title_cell_style)
                row_count += 1
                
                for column in columns:
                    ws.col(col_count).width = 256 * column[1]
                    ws.write(row_count, col_count, column[0], c_hdr_cell_style)
                    col_count += 1
                row_count += 1
                
                ws.write_merge(row_count, row_count, 0, 4, '   Initial Balance', c_title_cell_style)
                ws.write_merge(row_count, row_count, 5, 5, partner[1]['init_debit'], c_title_cell_style)
                ws.write_merge(row_count, row_count, 6, 6, partner[1]['init_credit'], c_title_cell_style)
                cell_debit = xlwt.Utils.rowcol_to_cell(row_count,col_count-3)
                cell_credit = xlwt.Utils.rowcol_to_cell(row_count,col_count-2)
                ws.write_merge(row_count, row_count, 7, 7, xlwt.Formula(cell_debit+'-'+cell_credit) , c_title_cell_style)
                
                row_count += 1
                col_count = 0
                if not partner[1]['move_line']:
                    continue
                
                cell_debit_start = xlwt.Utils.rowcol_to_cell(row_count, 5)
                cell_credit_start = xlwt.Utils.rowcol_to_cell(row_count, 6)
                for move_line in partner[1]['move_line']:
                    for line in move_line:
                        if col_count == 0:
                            ws.write(row_count, col_count, '   ' + str(line), c_cell_style)
                            col_count += 1
                        else:
                            ws.write(row_count, col_count, line, c_cell_style)
                            col_count += 1

                    cell_balance = xlwt.Utils.rowcol_to_cell(row_count-1,col_count)
                    cell_debit = xlwt.Utils.rowcol_to_cell(row_count,col_count-2)
                    cell_credit = xlwt.Utils.rowcol_to_cell(row_count,col_count-1)
                    ws.write(row_count, col_count, xlwt.Formula(cell_balance+'+'+cell_debit+'-'+cell_credit), c_cell_style)
            
                    col_count = 0
                    row_count += 1
                
                ws.write_merge(row_count, row_count, 0, 4, '   Ending Balance', c_hdr_cell_style)
                col_count = 5
                
                cell_debit_end = xlwt.Utils.rowcol_to_cell(row_count-1, 5)
                ws.write(row_count, col_count, xlwt.Formula('sum('+cell_debit_start+':'+cell_debit_end+')'), c_hdr_cell_style)
                col_count += 1
                
                cell_credit_end = xlwt.Utils.rowcol_to_cell(row_count-1, 6)
                ws.write(row_count, col_count, xlwt.Formula('sum('+cell_credit_start+':'+cell_credit_end+')'), c_hdr_cell_style)
                col_count += 1
                
                cell_debit_bal = xlwt.Utils.rowcol_to_cell(row_count, col_count-2)
                cell_credit_bal = xlwt.Utils.rowcol_to_cell(row_count, col_count-1)
                ws.write(row_count, col_count, xlwt.Formula(cell_debit_bal+'-'+cell_credit_bal) , c_hdr_cell_style)
                
                col_count = 0
                row_count += 1
            
            ws.write_merge(row_count, row_count, 0, 2, account[0], cell_style_header)
            ws.write_merge(row_count, row_count, 3, 4, 'Ending Balance on Account', cell_style_header)
            ws.write(row_count, 5, account[1]['ending_debit'], cell_style_header)
            ws.write(row_count, 6, account[1]['ending_credit'], cell_style_header)
            end_debit_bal = xlwt.Utils.rowcol_to_cell(row_count, 5)
            end_credit_bal = xlwt.Utils.rowcol_to_cell(row_count, 6)
            ws.write(row_count, 7, xlwt.Formula(end_debit_bal+'-'+end_credit_bal) , cell_style_header)
            
            row_count += 2
            col_count = 0
            
        pass
 
partner_ledger_xls('report.partner.ledger.xls', 'account.move.line', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
