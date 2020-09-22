{
    "name": "Accounting Report XLS",
    "version": "1.0",
    "depends": ['account_accountant'],
    "author":"PT Pan Asia jaya Abadi",
    "website": "http://www.pasajaya.com",
    "category":"Reports",
    "description" : """Modul Print XLS for 
        Accounting Report (GL, TB, Partner Ledger, Partner Balance, Aged Partner Balance)""",
    'data': [   
#         'account_entries_report_view.xml',
#         'security/ir.model.access.csv',
        'wizard/general_ledger_wizard_view.xml',
        'wizard/trial_balance_wizard_view.xml',
        'wizard/partner_ledger_wizard_view.xml',
        'wizard/partner_balance_wizard_view.xml',
        'wizard/aged_partner_balance_wizard_view.xml',
        'wizard/mutasi_persediaan_wizard_view.xml',
        'wizard/piutang_detail_wizard_view.xml',
        'wizard/hutang_wizard_view.xml',
        'wizard/bill_wizard_view.xml',
    ],
    'demo':[
            # files containing demo data            
    ],
    'test':[
            # files containing tests
    ],
    'installable' : True,
    'auto_install' : False,
    'application': False,
}
