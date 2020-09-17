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
        ['VENDOR', 20],
        ['COA', 20],
        ['TGL. BILL', 10],
        ['NO. BILL', 10],
        ['NO KB', 10],
        ['VENDOR REF', 10],
        #SALDO AWAL + PENAMBAHAN
        ['IDR', 20],
        ['IDR', 20],
        #REFERENCE PENGURANGAN
        ['NO BK/JOURNAL', 20],
        ['REFERENCE', 20],
        ['TGL', 20],
        #PEMBAYARAN BANK/CASH
        ['IDR', 20],
        #KOMPENSASI
        ['IDR', 20],
        #PERANTARA
        ['IDR', 20],
        #RECLAS UM
        ['IDR', 20],
        #RETUR
        ['IDR', 20],
        #LAIN2
        ['IDR', 20],
        #SALDO AHIR
        ['IDR', 20],
    ]
    
class hutang_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Laporan Hutang'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(7)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'LAPORAN HUTANG - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 2, 'Transaksi berjalan', cell_style_center)
        ws.write_merge(2, 2, 3, 5, 'Partner Filter', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'])  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 2, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 3, 5, data['partner_ids'], cell_style_param)

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
        
        ws.write_merge(row_count-1, row_count-1, 6, 6, 'SALDO AWAL', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 7, 7, 'PENAMBAHAN', cell_style_center)

        ws.write_merge(row_count-2, row_count-2, 8, 16, 'PENGURANGAN', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 8, 10, 'INFO PEMBAYARAN', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 11, 11, 'PEMBAYARAN BANK/CASH', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 12, 12, 'KOMPENSASI', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 13, 13, 'PERANTARA (TR/ LC)', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 14, 14, 'RECLASS UM', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 15, 15, 'RETUR', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 16, 16, 'LAIN-LAIN', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 17, 17, 'SALDO AHIR', cell_style_center)

        for column in columns:
            ws.col(col_count).width = 256 * column[1]
            ws.write(row_count, col_count, column[0], cell_style_center)
            col_count += 1
        has_payment = False
        for partner in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            row_count += 1
            ws.write_merge(row_count, row_count, 0, 17, partner[0], c_hdr_cell_style)
            row_start = row_count
            for bill in partner[1]['bills']:
                col_count = 0
                for data_bill in partner[1]['bills'][bill]['bill_info']:
                    row_count += 1
                    for line in data_bill:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                ws.write(row_count, 17, partner[1]['bills'][bill]['saldo_ahir'], c_cell_style_bold)
                has_payment = False
                for payments in partner[1]['bills'][bill]['payments']:
                    for payment in payments:
                        for pay in payment:
                            if pay != []:
                                has_payment = True
                        if not has_payment:
                            continue
                        for lines in payment:
                            col_count = 8
                            for line in lines:
                                ws.write(row_count, col_count, line, c_cell_style)
                                col_count += 1
                            row_count += 1
                if has_payment:
                    row_count -= 1
                col_count = 0
            
            #TOTAL SALDO AWAL DAN PENAMBAHAN
            row_count += 1
            col_count = 6
            ws.write_merge(row_count, row_count, 0, 5, 'TOTAL %s' %(partner[0]), c_hdr_cell_style_grey)
            while col_count < 8:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1                
            while col_count < 11:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
                col_count += 1
            while col_count < 18:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1 
        
        #GRAND TOTAL
        row_count += 2
        ws.write_merge(row_count, row_count, 0, 5, 'GRAND TOTAL', c_hdr_cell_style_grey)
        col_count = 6
        for line in data['grand_total']:
            ws.write(row_count, col_count, line, c_hdr_cell_style_grey)
            col_count += 1 
        pass
 
hutang_xls('report.hutang.idr.xls', 'account.invoice', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)