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

class piutang_detail_valas_summary_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Laporan Piutang Rekap (Valas)'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(7)    
        ws.set_vert_split_pos(3)  
        
        columns = [
            ['CUSTOMER', 20],
            ['TGL. INVOICE', 10],
            ['NO. INVOICE', 10],
            #SALDO AWAL
            ['KURS', 10],
            [data['valas'], 10],
            ['IDR', 20],
            #PENJUALAN
            [data['valas'], 10],
            ['IDR', 20],
            #REFERENCE PENGURANGAN
            ['NO BK/JOURNAL', 20],
            ['REFERENCE', 20],
            ['TGL', 20],
            #PEMBAYARAN
            [data['valas'], 10],
            ['IDR', 20],
            #TOTAL
            [data['valas'], 10],
            ['IDR', 20],
            #SELISIH IDR
            ['IDR', 20],
            #SALDO AHIR
            [data['valas'], 10],
            ['IDR', 20],
            ['KURS', 10],
        ]
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'LAPORAN PIUTANG REKAP (Valas) - ' + data['company_name'], title_style)
        
        cell_style_header = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'], num_format_str=report_xls.decimal_format)
        cell_style_center = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])               
        ws.write_merge(2, 2, 0, 2, 'Transaksi berjalan', cell_style_center)
        ws.write_merge(2, 2, 3, 5, 'Partner Filter', cell_style_center)
        ws.write_merge(2, 2, 6, 6, 'Kurs Awal', cell_style_center)
        ws.write_merge(2, 2, 7, 7, 'Kurs Ahir', cell_style_center)

        cell_style_param = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['top'] + _xs['center'], num_format_str=report_xls.decimal_format)  
        ws.row(3).height_mismatch = True
        ws.row(3).height = 20 * 28
        ws.write_merge(3, 3, 0, 2, data['date_from'] + ' - ' + data['date_to'], cell_style_param)
        ws.write_merge(3, 3, 3, 5, data['partner_ids'], cell_style_param)
        ws.write_merge(3, 3, 6, 6, data['kurs_awal'], cell_style_param)
        ws.write_merge(3, 3, 7, 7, data['kurs_ahir'], cell_style_param)

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
        
        ws.write_merge(row_count-1, row_count-1, 3, 5, 'SALDO AWAL', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 6, 7, 'PENJUALAN', cell_style_center)

        ws.write_merge(row_count-2, row_count-2, 8, 14, 'PELUNASAN', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 8, 10, 'INFO PEMBAYARAN', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 11, 12, 'NOMINAL', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 13, 14, 'TOTAL', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 15, 15, 'SELISIH KURS', cell_style_center)
        ws.write_merge(row_count-1, row_count-1, 16, 18, 'SALDO AHIR', cell_style_center)

        for column in columns:
            ws.col(col_count).width = 256 * column[1]
            ws.write(row_count, col_count, column[0], cell_style_center)
            col_count += 1
        has_payment = False
        for partner in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            row_count += 1
            ws.write_merge(row_count, row_count, 0, 18, partner[0], c_hdr_cell_style)
            row_start = row_count
            for invoice in partner[1]['invoices']:
                col_count = 0
                for data_invoice in partner[1]['invoices'][invoice]['invoice_info']:
                    row_count += 1
                    
                    ws.write(row_count, col_count, data_invoice[0], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, data_invoice[2], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, data_invoice[3], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, data_invoice[4], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, data_invoice[5], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, data_invoice[6], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, data_invoice[7], c_cell_style)
                    col_count += 1
                    ws.write(row_count, col_count, data_invoice[8], c_cell_style)
                    col_count += 1
                    
                ws.write(row_count, 13, partner[1]['invoices'][invoice]['total_pelunasan_valas'], c_cell_style_bold)
                ws.write(row_count, 14, partner[1]['invoices'][invoice]['total_pelunasan_idr'], c_cell_style_bold)
                
                ws.write(row_count, 15, partner[1]['invoices'][invoice]['total_selisih_idr'], c_cell_style_bold)
                
                ws.write(row_count, 16, partner[1]['invoices'][invoice]['saldo_ahir_valas'], c_cell_style_bold)
                ws.write(row_count, 17, partner[1]['invoices'][invoice]['saldo_ahir_idr'], c_cell_style_bold)
                ws.write(row_count, 18, data['kurs_ahir'], c_cell_style_bold)
                has_payment = False
                for payments in partner[1]['invoices'][invoice]['payments']:
                    for payment in payments:
                        for pay in payment:
                            if pay != []:
                                has_payment = True
                        if not has_payment:
                            continue
                        for lines in payment:
                            col_count = 8
                            ws.write(row_count, col_count, lines[0], c_cell_style)
                            col_count += 1
                            ws.write(row_count, col_count, lines[1], c_cell_style)
                            col_count += 1
                            ws.write(row_count, col_count, lines[2], c_cell_style)
                            col_count += 1
                            ws.write(row_count, col_count, lines[-2], c_cell_style)
                            col_count += 1
                            ws.write(row_count, col_count, lines[-1], c_cell_style)
                            col_count += 1
                                
                            row_count += 1
                if has_payment:
                    row_count -= 1
                col_count = 0
            
            #TOTAL SALDO AWAL S/D TOTAL PELUNASAN
            row_count += 1
            col_count = 4
            ws.write_merge(row_count, row_count, 0, 3, 'TOTAL %s' %(partner[0]), c_hdr_cell_style_grey)
            while col_count <= 7:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1                
            while col_count <= 13:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
                col_count += 1
            while col_count <= 17:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1 

        #GRAND TOTAL
        row_count += 2
        ws.write_merge(row_count, row_count, 0, 2, 'GRAND TOTAL', c_hdr_cell_style_grey)
        col_count = 3
        
        ws.write(row_count, col_count, data['grand_total'][0], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][1], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][2], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][3], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][4], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, '', c_hdr_cell_style_grey)
        col_count += 1 
        #TOTAL 
        ws.write(row_count, col_count, data['grand_total'][-6], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][-5], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][-4], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][-3], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][-2], c_hdr_cell_style_grey)
        col_count += 1 
        ws.write(row_count, col_count, data['grand_total'][-1], c_hdr_cell_style_grey)
        col_count += 1 
        
            
        pass
 
piutang_detail_valas_summary_xls('report.piutang.detail.valas.summary.xls', 'account.invoice', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)