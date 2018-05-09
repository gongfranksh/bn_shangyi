# -*- coding: utf-8 -*-
from openerp.osv import fields, osv


class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
        'code': fields.char('code'),
    }
    _order = 'code'
    
    def search_bycode(self,cr,uid,code):
        category_id=self.pool.get('product.category').search(cr,uid,[('code','=',code)])
        categ_id=False
        if category_id:
            categ_id=category_id[0]
        return categ_id
    
class product_template(osv.osv):
    _inherit = 'product.template'
    _columns = {
        'code': fields.char('产品编码'),
        'barcode': fields.char('产品条码'),
        'm_category': fields.many2one('product.category', '中类', ),
        'b_category': fields.many2one('product.category', '大类', ),
        'brand_id': fields.many2one('product.brand', '品牌'),
        'spec':fields.char(u'规格型号'),
    }
    
    def search_bycode(self,cr,uid,code):
        product=self.pool.get('product.template').search(cr,uid,[('code','=',code)])
        product_id=False
        if product:
            product_id=product[0]
        return product_id

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'code': fields.char('code'),
    }
    
    def search_bycode(self,cr,uid,code):
        res_partner=self.pool.get('res.partner').search(cr,uid,[('code','=',code)])
        partner_id=False
        if res_partner:
            partner_id=res_partner[0]
        return partner_id

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'code': fields.char('code'),
    }
    def search_bycode(self,cr,uid,code):
        company=self.pool.get('res.company').search(cr,uid,[('code','=',code)])
        company_id=False
        if company:
            company_id=company[0]
        return company_id

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _columns = {
        'code': fields.char('code'),
        'company_id': fields.related('resource_id', 'company_id', type='many2one', relation='res.company',
                                     string='Company', ),
    }
    def search_bycode(self,cr,uid,code):
        employee=self.pool.get('hr.employee').search(cr,uid,[('code','=',code)])
        employee_id=False
        if employee:
            employee_id=employee[0]
        return employee_id

class product_brand(osv.osv):
    _name = 'product.brand'
    _columns = {
        'code': fields.char('code'),
        'name': fields.char('name'),
    }

    def search_bycode(self,cr,uid,code):
        brand=self.pool.get('product.brand').search(cr,uid,[('code','=',code)])
        brand_id=False
        if brand:
            brand_id=brand[0]
        return brand_id