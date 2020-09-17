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


class piutang_valas_xls(report_xls):
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        ws = wb.add_sheet(('Laporan Piutang (Valas)'))
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1   
        ws.set_horz_split_pos(7)    
        ws.set_vert_split_pos(9)    
        
        columns = [
            ['CUSTOMER', 20],
            ['COA', 20],
            ['TGL. INVOICE', 10],
            ['NO. INVOICE', 20],
            # SALDO AWAL
            ['KURS', 10],
            [data['valas'], 10],
            ['IDR', 20],
            # PENJUALAN
            [data['valas'], 10],
            ['IDR', 20],
            # PEMBAYARAN BANK/CASH
            [data['valas'], 10],
            ['IDR', 20],
            # RETUR
            [data['valas'], 10],
            ['IDR', 20],
            # KLAIM
            [data['valas'], 10],
            ['IDR', 20],
            # BANK CHARGES
            [data['valas'], 10],
            ['IDR', 20],
            # KOMISI
            [data['valas'], 10],
            ['IDR', 20],
            # POTONGAN
            [data['valas'], 10],
            ['IDR', 20],
            # OTHERS
            [data['valas'], 10],
            ['IDR', 20],
            # PEMBULATAN
            [data['valas'], 10],
            ['IDR', 20],
            # TOTAL
            [data['valas'], 10],
            ['IDR', 20],
            # SELISIH IDR
            ['IDR', 20],
            # SALDO AHIR
            [data['valas'], 10],
            ['IDR', 20],
            ['KURS', 10],
        ]
        
        title_style = xlwt.easyxf(_xs['xls_title'])
        ws.write_merge(0, 0, 0, 14, 'LAPORAN PIUTANG (VALAS) - ' + data['company_name'], title_style)
        
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
        c_cell_style_bold = xlwt.easyxf(_xs['borders_all'] + _xs['bold'],
            num_format_str=report_xls.decimal_format)
        
        row_count = 6
        col_count = 0    
        
        ws.write_merge(row_count - 1, row_count - 1, 4, 6, 'SALDO AWAL', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 7, 8, 'PENJUALAN', cell_style_center)

        ws.write_merge(row_count - 2, row_count - 2, 9, 26, 'PELUNASAN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 9, 10, 'PEMBAYARAN BANK', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 11, 12, 'RETUR', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 13, 14, 'KLAIM', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 15, 16, 'BANK CHARGE', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 17, 18, 'KOMISI', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 19, 20, 'POTONGAN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 21, 22, 'LAIN-LAIN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 23, 24, 'PEMBULATAN', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 25, 26, 'TOTAL', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 27, 27, 'SELISIH KURS', cell_style_center)
        ws.write_merge(row_count - 1, row_count - 1, 28, 29, 'SALDO AHIR', cell_style_center)

        for column in columns:
            ws.col(col_count).width = 256 * column[1]
            ws.write(row_count, col_count, column[0], cell_style_center)
            col_count += 1
        has_payment = False
        for partner in sorted(data['csv'].items(), key=operator.itemgetter(0)):
            row_count += 1
            ws.write_merge(row_count, row_count, 0, 33, partner[0], c_hdr_cell_style)
            row_start = row_count
            for invoice in partner[1]['invoices']:
                col_count = 0
                for data_invoice in partner[1]['invoices'][invoice]['invoice_info']:
                    row_count += 1
                    for line in data_invoice:
                        ws.write(row_count, col_count, line, c_cell_style)
                        col_count += 1
                ws.write(row_count, 25, partner[1]['invoices'][invoice]['total_pelunasan_valas'], c_cell_style_bold)
                ws.write(row_count, 26, partner[1]['invoices'][invoice]['total_pelunasan_idr'], c_cell_style_bold)
                
                ws.write(row_count, 27, partner[1]['invoices'][invoice]['total_selisih_idr'], c_cell_style_bold)
                
                ws.write(row_count, 28, partner[1]['invoices'][invoice]['saldo_ahir_valas'], c_cell_style_bold)
                ws.write(row_count, 29, partner[1]['invoices'][invoice]['saldo_ahir_idr'], c_cell_style_bold)
                ws.write(row_count, 30, data['kurs_ahir'], c_cell_style_bold)
                
                # BANK
                total_bank_valas = total_bank_idr = 0
                for bank in partner[1]['invoices'][invoice]['payments'][0][0]:
                    total_bank_valas += bank[-2]
                    total_bank_idr += bank[-1]
                # RETUR
                total_retur_valas = total_retur_idr = 0
                for retur in partner[1]['invoices'][invoice]['payments'][0][1]:
                    total_retur_valas += retur[-2]
                    total_retur_idr += retur[-1]
                # KLAIM
                total_klaim_valas = total_klaim_idr = 0
                for klaim in partner[1]['invoices'][invoice]['payments'][0][2]:
                    total_klaim_valas += klaim[-2]
                    total_klaim_idr += klaim[-1]
                # BANK CHARGE
                total_charge_valas = total_charge_idr = 0
                for charge in partner[1]['invoices'][invoice]['payments'][0][3]:
                    total_charge_valas += charge[-2]
                    total_charge_idr += charge[-1]
                # KOMISI
                total_komisi_valas = total_komisi_idr = 0
                for komisi in partner[1]['invoices'][invoice]['payments'][0][4]:
                    total_komisi_valas += komisi[-2]
                    total_komisi_idr += komisi[-1]
                # POTONGAN
                total_potongan_valas = total_potongan_idr = 0
                for potongan in partner[1]['invoices'][invoice]['payments'][0][5]:
                    total_potongan += potongan[-2]
                    total_potongan_valas += potongan[-1]
                # LAIN2
                total_lain_valas = total_lain_idr = 0
                for lain in partner[1]['invoices'][invoice]['payments'][0][6]:
                    total_lain_valas += lain[-2]
                    total_lain_idr += lain[-1]
                # PEMBULATAN
                total_pembulatan_valas = total_pembulatan_idr = 0
                for pembulatan in partner[1]['invoices'][invoice]['payments'][0][7]:
                    total_pembulatan_valas += pembulatan[-2]
                    total_pembulatan_idr += pembulatan[-1]
                
                payments = [total_bank_valas, total_bank_idr, total_retur_valas, total_retur_idr, total_klaim_valas, total_klaim_idr, total_charge_valas, total_charge_idr, \
                            total_komisi_valas, total_komisi_idr, total_potongan_valas, total_potongan_idr, total_lain_valas, total_lain_idr, total_pembulatan_valas, total_pembulatan_idr]
                for amount in payments:
                    ws.write(row_count, col_count, amount, c_cell_style)
                    col_count += 1
            
            # TOTAL SALDO AWAL S/D TOTAL PELUNASAN
            row_count += 1
            col_count = 5
            ws.write_merge(row_count, row_count, 0, 4, 'TOTAL %s' % (partner[0]), c_hdr_cell_style_grey)
            while col_count <= 29:
                sum_cell_start = xlwt.Utils.rowcol_to_cell(row_start + 1, col_count)
                sum_cell_end = xlwt.Utils.rowcol_to_cell(row_count - 1, col_count)
                ws.write(row_count, col_count, xlwt.Formula('sum(' + sum_cell_start + ':' + sum_cell_end + ')'), c_hdr_cell_style_grey)
                col_count += 1    
                 
        # GRAND TOTAL
        row_count += 2
        ws.write_merge(row_count, row_count, 0, 3, 'GRAND TOTAL', c_hdr_cell_style_grey)
        col_count = 4
        for line in data['grand_total'][:5]:
            ws.write(row_count, col_count, line, c_hdr_cell_style_grey)
            col_count += 1
        for line in data['grand_total'][-22:]:
            ws.write(row_count, col_count, line, c_hdr_cell_style_grey)
            col_count += 1 
            
        pass

 
piutang_valas_xls('report.piutang.valas.xls', 'account.invoice', 'addons/accounting_report_xls/report/report_excel.mako', parser=ReportStatus, header=False)
