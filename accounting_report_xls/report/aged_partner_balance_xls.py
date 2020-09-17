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
              ['   Date', 12],
              ['Entry', 15],
              ['Label', 20],
              ['Journal', 8]
            ]


class aged_partner_balance_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Aged Partner Balance'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(4)    
        ws.set_vert_split_pos(5)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'AGED PARTNER BALANCE - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 0, 'Start Date', cell_style_center)
        ws.write_merge(2, 2, 1, 2, 'Account Filter', cell_style_center)
        ws.write_merge(2, 2, 3, 4, 'Partner Filter', cell_style_center)
        ws.write_merge(2, 2, 5, 5, 'Target Moves', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 0, data['start_date'], cell_style_param)
        ws.write_merge(3, 3, 1, 2, data['account_ids'], cell_style_param)
        ws.write_merge(3, 3, 3, 4, data['partner_ids'], cell_style_param)
        ws.write_merge(3, 3, 5, 5, data['target_move'], cell_style_param)

        c_hdr_cell_style = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'],
            num_format_str=report_xls.decimal_format)
        c_hdr_cell_style_right = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        c_cell_style = xlwt.easyxf(_xs['borders_all'],
            num_format_str=report_xls.decimal_format)

        list_overdues = []
        list_overdues.append(['Balance', 15])
        list_overdues.append(['Not Due', 15])
        od = 'Overdue <'
        periods = data['period_length'].split(',')
        a = 0
        for period in periods:
            overdue = [od + ' ' + str(int(period) + int(a)), 15]
            a += int(period)
            list_overdues.append(overdue)
        list_overdues.append(['Older', 15])
        len_overdues = len(list_overdues)

        row_count = 5
        col_count = 0
        for account in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            ws.write_merge(row_count, row_count, 0, 5, account[0], cell_style_header)
            row_count += 1
            for partner in sorted(account[1]['partner'].items(), key=operator.itemgetter(0)):
                ws.write_merge(row_count, row_count, 0, 5, partner[0], c_cell_style)
                row_count += 1
                for column in columns:
                    ws.col(col_count).width = 256 * column[1]
                    ws.write(row_count, col_count, column[0], c_hdr_cell_style)
                    col_count += 1
                
                for list_overdue in list_overdues:
                    ws.col(col_count).width = 256 * list_overdue[1]
                    ws.write(row_count, col_count, list_overdue[0], c_hdr_cell_style_right)
                    col_count += 1
                ws.write(row_count, col_count, 'Jumlah Penagihan', c_hdr_cell_style)
                col_count += 1
                ws.write(row_count, col_count, 'Alasan Gagal', c_hdr_cell_style)
                col_count = 0
                row_count += 1
                row_overdue = row_count
                for lines in partner[1]:
                    for line in lines:
                        if col_count == 0:
                            ws.write(row_count, col_count, '   ' + str(line), c_cell_style)
                        else:
                            ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                    col_count = 0
                    row_count += 1
                ws.write_merge(row_count, row_count, 0, 3, partner[0], c_hdr_cell_style)
                col_count = 4
                len_overdue = 0
                while len_overdue < len_overdues:
                    cell_overdue_start = xlwt.Utils.rowcol_to_cell(row_overdue, col_count)
                    cell_overdue_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                    ws.write(row_count, col_count, xlwt.Formula('sum(' + cell_overdue_start + ':' + cell_overdue_end + ')'), c_hdr_cell_style)
                    col_count += 1
                    len_overdue += 1
                    
                ws.write(row_count, col_count, '', c_hdr_cell_style)
                ws.col(col_count).width = 256 * 20
                col_count += 1
                ws.write(row_count, col_count, '', c_hdr_cell_style)
                ws.col(col_count).width = 256 * 20
                col_count = 0
                row_count += 1
            ws.write_merge(row_count, row_count, 0, 3, account[0], cell_style_header)
            col_count = 4
            for ending in account[1]['ending']:
                ws.write_merge(row_count, row_count, col_count, col_count, ending, cell_style_header)
                col_count += 1
            ws.write(row_count, col_count, '', cell_style_header)
            col_count += 1
            ws.write(row_count, col_count, '', cell_style_header)
            col_count = 0
            row_count += 2
            
        pass

 
aged_partner_balance_xls('report.aged.partner.balance.xls', 'account.move.line', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
