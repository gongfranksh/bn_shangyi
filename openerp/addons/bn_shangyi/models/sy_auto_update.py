# -*- coding: utf-8 -*-
import datetime
import types
import webbrowser
from openerp.osv import fields, osv
from BNmssql import Lz_read_SQLCa


class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
        'stamp': fields.integer(u'时间戳')
    }


class product_template(osv.osv):
    _inherit = 'product.template'
    _columns = {
        'stamp': fields.integer(u'时间戳')
    }


class product_brand(osv.osv):
    _name = 'product.brand'
    _columns = {
        'stamp': fields.integer(u'时间戳')
    }


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'stamp': fields.integer(u'时间戳')
    }


class sy_product_new(osv.osv):
    _name = 'sy.product.new'
    _columns = {
        'code': fields.char(u'编码', required=True),
        'name': fields.char(u'名称'),
        'date': fields.date(u'日期'),
        'text': fields.text(u'备注'),
    }
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code must be unique!'),
    ]
