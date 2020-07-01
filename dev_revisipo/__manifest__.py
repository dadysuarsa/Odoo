# -*- coding: utf-8 -*-
{
    'name': "dev_revisipo",
    'version': '1.2',
    # 'category': 'Revisi Purchases',
    # 'sequence': 60,
    'summary': 'Revisi Purchase Orders',
    'description': """
Form revisi Purchase Order
Dashboard / Reports for Revisi Purchase will include:
---------------------------------------------------------
* Form Revisi Order
    """,
    'author': "Dazca",
    'website': "http://pasajaya.com",

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','account','dev_others','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/revisipo_security.xml',
        'views/revisi_purchase_views.xml',

    ],

}