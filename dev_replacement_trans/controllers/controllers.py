# -*- coding: utf-8 -*-
from odoo import http

# class DevReplacementTrans(http.Controller):
#     @http.route('/dev_replacement_trans/dev_replacement_trans/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dev_replacement_trans/dev_replacement_trans/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dev_replacement_trans.listing', {
#             'root': '/dev_replacement_trans/dev_replacement_trans',
#             'objects': http.request.env['dev_replacement_trans.dev_replacement_trans'].search([]),
#         })

#     @http.route('/dev_replacement_trans/dev_replacement_trans/objects/<model("dev_replacement_trans.dev_replacement_trans"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dev_replacement_trans.object', {
#             'object': obj
#         })