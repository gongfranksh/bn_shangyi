# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import fields,osv

class sy_pos_order_report(osv.osv):
    _name ='sy.pos.order.report'
    _auto = False
    _columns = {
                'product':fields.many2one('product.template',u'产品'),
                'barcode':fields.char(u'条码'),
                'category_id':fields.many2one('product.category',u'产品类别'),
                'm_category_id':fields.many2one('product.category',u'产品中类'),
                'b_category_id':fields.many2one('product.category',u'产品大类'),
                'brand_id':fields.many2one('product.brand',u'品牌'),
                'sale_date':fields.date(u'销售日期'),
                'sale_man':fields.many2one('hr.employee',u'营业员'),
                'qty':fields.integer('数量'),
                'amount':fields.float('金额 '),
                'profit':fields.float('毛利',groups='bn_shangyi.group_profit'),
                'company_id':fields.many2one('res.company','公司'),
                }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sy_pos_order_report')
        cr.execute("""
                        create or replace view sy_pos_order_report as (
                            select ROW_NUMBER() OVER (ORDER BY aa.product)  as id,* from (
                            SELECT spo.product AS product,
                                pt.barcode,
                                pt.categ_id AS category_id,
                                pt.m_category AS m_category_id,
                                pt.b_category AS b_category_id,
                                pt.brand_id AS brand_id,
                                cast(spo.sale_date AS date) AS sale_date,
                                sum(spo.qty) AS qty,
                                sum(spo.amount) AS amount,
                                sum(spo.profit) AS profit,
                                spo.sale_man AS sale_man,
                                spo.company_id AS company_id
                                FROM sy_pos_order spo
                                LEFT JOIN product_template pt ON spo.product=pt.id
                                GROUP BY spo.product,cast(spo.sale_date AS date),spo.sale_man,spo.company_id,pt.id,pt.barcode
                            ) aa
                            )
                    """)