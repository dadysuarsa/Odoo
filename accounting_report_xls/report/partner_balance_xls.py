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
              ['Partner Name', 30],
              ['Code/Ref', 15],
              ['Initial Balance', 20],
              ['Debit', 20],
              ['Credit', 20],
              ['Balance', 25]
            ]
    
class partner_balance_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Partner Balance'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(4)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'PARTNER BALANCE - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 0, 'Date', cell_style_center)
        ws.write_merge(2, 2, 1, 2, 'Account Filter', cell_style_center)
        ws.write_merge(2, 2, 3, 4, 'Partner Filter', cell_style_center)
        ws.write_merge(2, 2, 5, 5, 'Target Moves', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 0, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 1, 2, data['account_ids'], cell_style_param)
        ws.write_merge(3, 3, 3, 4, data['partner_ids'], cell_style_param)
        ws.write_merge(3, 3, 5, 5, data['target_move'], cell_style_param)

        c_hdr_cell_style = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_cell_style = xlwt.easyxf(_xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        
        row_count = 5
        col_count = 0
        for account in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            ws.write_merge(row_count, row_count, 0, 5, account[0], cell_style_header)
            row_count += 1
            if not account[1]['move_line']:
                continue
            
            for column in columns:
                ws.col(col_count).width = 256 * column[1]
                ws.write(row_count, col_count, column[0], c_hdr_cell_style)
                col_count += 1
            row_count += 1
            col_count = 0
            
            cell_init_start = xlwt.Utils.rowcol_to_cell(row_count, 2)
            cell_debit_start = xlwt.Utils.rowcol_to_cell(row_count, 3)
            cell_credit_start = xlwt.Utils.rowcol_to_cell(row_count, 4)
            for partner in sorted(account[1]['move_line'].items(), key=operator.itemgetter(0)):
                ws.write(row_count, col_count, partner[0], c_cell_style)
                col_count += 1
                ws.write(row_count, col_count, partner[1]['partner_code'], c_cell_style)
                col_count += 1
                ws.write(row_count, col_count, partner[1]['initial'], c_cell_style)
                col_count += 1
                ws.write(row_count, col_count, partner[1]['debit'], c_cell_style)
                col_count += 1
                ws.write(row_count, col_count, partner[1]['credit'], c_cell_style)
                col_count += 1

                cell_init_balance = xlwt.Utils.rowcol_to_cell(row_count, col_count-3)
                cell_debit = xlwt.Utils.rowcol_to_cell(row_count,col_count-2)
                cell_credit = xlwt.Utils.rowcol_to_cell(row_count,col_count-1)
                ws.write(row_count, col_count, xlwt.Formula(cell_init_balance+'+'+cell_debit+'-'+cell_credit), c_cell_style)
        
                col_count = 0
                row_count += 1

            ws.write_merge(row_count, row_count, 0, 1, account[0], cell_style_header)
            col_count = 2
            
            cell_init_end = xlwt.Utils.rowcol_to_cell(row_count-1, 2)
            ws.write(row_count, col_count, xlwt.Formula('sum('+cell_init_start+':'+cell_init_end+')'), cell_style_header)
            col_count += 1
            
            cell_debit_end = xlwt.Utils.rowcol_to_cell(row_count-1, 3)
            ws.write(row_count, col_count, xlwt.Formula('sum('+cell_debit_start+':'+cell_debit_end+')'), cell_style_header)
            col_count += 1

            cell_credit_end = xlwt.Utils.rowcol_to_cell(row_count-1, 4)
            ws.write(row_count, col_count, xlwt.Formula('sum('+cell_credit_start+':'+cell_credit_end+')'), cell_style_header)
            col_count += 1
            
            cell_init_bal = xlwt.Utils.rowcol_to_cell(row_count, 2)
            cell_debit_bal = xlwt.Utils.rowcol_to_cell(row_count, 3)
            cell_credit_bal = xlwt.Utils.rowcol_to_cell(row_count, 4)
            ws.write(row_count, col_count, xlwt.Formula(cell_init_bal +'+'+cell_debit_bal+'-'+cell_credit_bal) , cell_style_header)
            
            row_count += 2
            col_count = 0
            
        pass
 
partner_balance_xls('report.partner.balance.xls', 'account.move.line', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
