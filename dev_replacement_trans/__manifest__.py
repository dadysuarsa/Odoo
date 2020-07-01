# -*- coding: utf-8 -*-
{
    'name': "dev_replacment_trans",

    'summary': """
       Replacement Transfer return""",

    'description': """
         Replacement Transfer return
    """,

    'author': "MIS",
    'website': "http://www.pasajaya.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','stock','dev_others'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/replacement_trans_view.xml',
        'report/config_report.xml',
        'report/replacement_trans.xml',
    ],

}