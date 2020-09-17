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
        ['CUSTOMER', 20],
        ['COA', 20],
        ['TGL. INVOICE', 10],
        ['NO. INVOICE', 20],
        # SALDO AWAL + PENJUALAN
        ['IDR', 20],
        ['IDR', 20],
        # PEMBAYARAN BANK/CASH
        ['IDR', 20],
        # RETUR
        ['IDR', 20],
        # KLAIM
        ['IDR', 20],
        # BANK CHARGE
        ['IDR', 20],
        # KOMISI
        ['IDR', 20],
        # POTONGAN
        ['IDR', 20],
        # LAIN2
        ['IDR', 20],
        # PEMBULATAN
        ['IDR', 20],
        # SALDO AHIR
        ['IDR', 20],
    ]

    
class piutang_idr_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Laporan Piutang'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(7)    
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'LAPORAN PIUTANG - ' + data['company_name'], title_style)
        
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
        c_cell_style_bold = xlwt.easyxf(_xs['borders_all'] + _xs['bold'],
            num_format_str=report_xls.decimal_format)
        
        row_count = 6
        col_count = 0    
        
        ws.write_merge(row_count - 1, row_count - 1, 4, 4, 'SALDO AWAL', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 5, 5, 'PENJUALAN', cell_style_center)

        ws.write_merge(row_count - 2, row_count - 2, 6, 13, 'PELUNASAN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 6, 6, 'PEMBAYARAN BANK/CASH', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 7, 7, 'RETUR', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 8, 8, 'KLAIM', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 9, 9, 'BANK CHARGES', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 10, 10, 'KOMISI', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 11, 11, 'POTONGAN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 12, 12, 'LAIN-LAIN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 13, 13, 'PEMBULATAN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 14, 14, 'SALDO AHIR', cell_style_center)

        for column in columns:
            ws.col(col_count).width = 256 * column[1]
            ws.write(row_count, col_count, column[0], cell_style_center)
            col_count += 1
        has_payment = False
        for partner in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            row_count += 1
            ws.write_merge(row_count, row_count, 0, 14, partner[0], c_hdr_cell_style)
            row_start = row_count
            for invoice in partner[1]['invoices']:
                col_count = 0
                for data_invoice in partner[1]['invoices'][invoice]['invoice_info']:
                    row_count += 1
                    for line in data_invoice:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                ws.write(row_count, 14, partner[1]['invoices'][invoice]['saldo_ahir'], c_cell_style_bold)
                # BANK
                total_bank = 0
                for bank in partner[1]['invoices'][invoice]['payments'][0][0]:
                    total_bank += bank[-1]
                # RETUR
                total_retur = 0
                for retur in partner[1]['invoices'][invoice]['payments'][0][1]:
                    total_retur += retur[-1]
                # KLAIM
                total_klaim = 0
                for klaim in partner[1]['invoices'][invoice]['payments'][0][2]:
                    total_klaim += klaim[-1]
                # BANK CHARGE
                total_charge = 0
                for charge in partner[1]['invoices'][invoice]['payments'][0][3]:
                    total_charge += charge[-1]
                # KOMISI
                total_komisi = 0
                for komisi in partner[1]['invoices'][invoice]['payments'][0][4]:
                    total_komisi += komisi[-1]
                # POTONGAN
                total_potongan = 0
                for potongan in partner[1]['invoices'][invoice]['payments'][0][5]:
                    total_potongan += potongan[-1]
                # LAIN2
                total_lain = 0
                for lain in partner[1]['invoices'][invoice]['payments'][0][6]:
                    total_lain += lain[-1]
                # PEMBULATAN
                total_pembulatan = 0
                for pembulatan in partner[1]['invoices'][invoice]['payments'][0][7]:
                    total_pembulatan += pembulatan[-1]
                
                payments = [total_bank, total_retur, total_klaim, total_charge, total_komisi, total_potongan, total_lain, total_pembulatan]
                for amount in payments:
                    ws.write(row_count, col_count, amount, c_cell_style)
                    col_count += 1
                    
            # TOTAL SALDO AWAL DAN PENJUALAN
            row_count += 1
            col_count = 4
            ws.write_merge(row_count, row_count, 0, 3, 'TOTAL %s' % (partner[0]), c_hdr_cell_style_grey)
            while col_count <= 14:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1 
        
        # GRAND TOTAL
        row_count += 2
        ws.write_merge(row_count, row_count, 0, 3, 'GRAND TOTAL', c_hdr_cell_style_grey)
        col_count = 4
        for line in data['grand_total'][:2]:
            ws.write(row_count, col_count, line, c_hdr_cell_style_grey)
            col_count += 1 
        for line in data['grand_total'][-9:]:
            ws.write(row_count, col_count, line, c_hdr_cell_style_grey)
            col_count += 1 
        pass

 
piutang_idr_xls('report.piutang.idr.xls', 'account.invoice', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
