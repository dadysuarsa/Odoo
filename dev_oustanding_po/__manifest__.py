# -*- coding: utf-8 -*-
{
    'name': "dev_outstanding_po",

    'summary': """
        Outstanding PO
        """,

    'description': """
        Oustanding Purchase Order
    """,

    'author': "dazca02",
    'website': "http://www.pasajaya.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','purchase'],

    # always loaded
    'data': [
        'wizard/outstanding_po_view.xml',
    ],

}