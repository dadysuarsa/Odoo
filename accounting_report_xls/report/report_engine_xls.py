from odoo.report import report_sxw
from odoo import tools, models, fields
import xlwt, cStringIO
from odoo.api import Environment
import xlsxwriter

class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report.xml'

    report_type = fields.Selection(selection_add=[('xls', 'XLS'), ('xlsx', 'XLSX')])
    
class report_xls(report_sxw.report_sxw):
 
    xls_types = {
        'bool': xlwt.Row.set_cell_boolean,
        'date': xlwt.Row.set_cell_date,
        'text': xlwt.Row.set_cell_text,
        'number': xlwt.Row.set_cell_number,
    }
    xls_types_default = {
        'bool': False,
        'date': None,
        'text': '',
        'number': 0,
    }
    _pfc = '26'  # default pattern fore_color
    _bc = '22'  # borders color
    decimal_format = '#,##0.00'
    percentage_format = '0.00%'
    date_format = 'DD/MM/YYYY'
    xls_styles = {
        'xls_title': 'font: bold true, height 240;',
        'bold': 'font: bold true;',
        'underline': 'font: underline true;',
        'italic': 'font: italic true;',
        'fill': 'pattern: pattern solid, fore_color %s;' % _pfc,
        'fill_blue': 'pattern: pattern solid, fore_color 27;',
        'fill_grey': 'pattern: pattern solid, fore_color 22;',
        'fill_red': 'pattern: pattern solid, fore_color red;',
        'borders_all':
            'borders: '
            'left thin, right thin, top thin, bottom thin, '
            'left_colour %s, right_colour %s, '
            'top_colour %s, bottom_colour %s;'
            % (_bc, _bc, _bc, _bc),
        'left': 'align: horz left;',
        'center': 'align: horz center;align: vert center;',
        'right': 'align: horz right;',
        'wrap': 'align: wrap true;',
        'top': 'align: vert top;',
        'bottom': 'align: vert bottom;',
    }
    
    def create(self, cr, uid, ids, data, context=None):
        uid = 1
        self.env = Environment(cr, uid, context)
        ir_obj = self.env['ir.actions.report.xml']
        report_xml = ir_obj.search([('report_name', '=', self.name[7:])])
        if not report_xml:
            title = ''
            rml = tools.file_open(self.tmpl, subdir=None).read()
            class a(object):
                def __init__(self, *args, **argv):
                    for key, arg in argv.items():
                        setattr(self, key, arg)
            report_xml = a(title=title, report_type='xls', report_rml_content=rml, name=title, attachment=False, header=self.header)
        
        result = self.create_source_xls(cr, uid, ids, data, report_xml, context)
        if not result:
            return (False, False)
        return result
 
    def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
        context = {} if not context else context.copy()
        
        rml_parser = self.parser(cr, uid, self.name2, context=context)
        objs = self.getObjects(cr, uid, ids, context=context)
        rml_parser.set_context(objs, data, ids, 'xls')
        n = cStringIO.StringIO()
        wb = xlwt.Workbook(encoding='utf-8')
        for i, obj in enumerate(rml_parser.localcontext['objects']):
            self.generate_xls_report(rml_parser, self.xls_styles, data, obj, wb)
        wb.save(n)
        n.seek(0)
        return (n.read(), 'xls')
 
    def generate_xls_report(self, parser, _xs, data, obj, wb):
        raise NotImplementedError()


class report_xlsx(report_sxw.report_sxw):
 
    def xlsx_style(self, wb):
        return {
            'title' : wb.add_format({'bold': True, 'border': True}),
            'blue' : wb.add_format({'bg_color' : 'cyan', 'bold': True, 'border': True}),
            'blue_center' : wb.add_format({'bg_color': 'cyan', 'align': 'center', 'bold': True, 'border': True}),
            'yellow' : wb.add_format({'bg_color': 'yellow', 'bold': True, 'border': True}),
            'yellow_center' : wb.add_format({'bg_color': 'yellow', 'align': 'center', 'bold': True, 'border': True}),
            'yellow_right' : wb.add_format({'bg_color': 'yellow', 'align': 'right', 'bold': True, 'border': True}),
            'yellow_percent' : wb.add_format({'bold': True, 'border': True, 'num_format': '0.00%'}),
            'normal' : wb.add_format({'border': True, 'num_format': '#,##0'}),
            'normal_bold' : wb.add_format({'bold': True, 'border': True, 'num_format': '#,##0'}),
            'normal_date' : wb.add_format({'bold': True}),
            'normal_center' : wb.add_format({'align': 'center', 'border': True}),
            'normal_italic' : wb.add_format({'italic': True, 'border': True}),
            'normal_percent' : wb.add_format({'num_format': '0.00%', 'border': True}),
            'normal_percent_bold' : wb.add_format({'num_format': '0.00%', 'bold': True, 'border': True}),
        }
        
    def create(self, cr, uid, ids, data, context=None):
        uid = 1
        self.env = Environment(cr, uid, context)
        ir_obj = self.env['ir.actions.report.xml']
        report_xml = ir_obj.search([('report_name', '=', self.name[7:])])
        if not report_xml:
            title = ''
            rml = tools.file_open(self.tmpl, subdir=None).read()
            class a(object):
                def __init__(self, *args, **argv):
                    for key, arg in argv.items():
                        setattr(self, key, arg)
            report_xml = a(title=title, report_type='xls', report_rml_content=rml, name=title, attachment=False, header=self.header)
        
        result = self.create_source_xls(cr, uid, ids, data, report_xml, context)
        if not result:
            return (False, False)
        return result
 
    def create_source_xlsx(self, cr, uid, ids, data, report_xml, context=None):
        context = {} if not context else context.copy()
        
        rml_parser = self.parser(cr, uid, self.name2, context=context)
        objs = self.getObjects(cr, uid, ids, context=context)
        rml_parser.set_context(objs, data, ids, 'xlsx')
        n = cStringIO.StringIO()
        wb = xlsxwriter.Workbook(n)
        for i, obj in enumerate(rml_parser.localcontext['objects']):
            self.generate_xlsx_report(rml_parser, self.xlsx_style(wb), data, obj, wb)
        wb.close()
        n.seek(0)
        return (n.read(), 'xlsx')
 
    def generate_xlsx_report(self, parser, style, data, obj, wb):
        raise NotImplementedError()
