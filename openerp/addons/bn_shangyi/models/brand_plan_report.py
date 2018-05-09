# -*- coding: utf-8 -*-
from openerp.osv import fields,osv
from openerp import tools

class brand_plan_report(osv.osv):
    _name='brand.plan.report'
    _auto = False
    _columns = {
                'company_id':fields.many2one('res.company',u'门店'),
                'categ_id':fields.many2one('product.category',u'大类'),
                'brand_id':fields.many2one('product.brand',u'品牌'),
                'date':fields.date(u'日期'),
                'amount':fields.float(u'营业额'),
                'profit':fields.float(u'毛利',groups='bn_shangyi.group_profit'),
                'plan_sale_daily':fields.float(u'营业额目标'),
                'plan_profit_daily':fields.float(u'毛利目标',groups='bn_shangyi.group_profit'),
                }
    _order='date'
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'brand_plan_report')
        cr.execute("""
                        create or replace view brand_plan_report as (
                        select ROW_NUMBER() OVER (ORDER BY aa.date DESC)  as id,* from (
                        SELECT
                            sale.company_id,
                            sale.b_category AS categ_id,
                            sale.brand_id,
                            sale.sale_date AS DATE,
                            sale.amount,
                            sale.profit,
                            brand_plan.plan_sale AS plan_sale_daily,
                            brand_plan.plan_profit AS plan_profit_daily
                        FROM
                            (
                                SELECT
                                    spo.company_id,
                                    pt.brand_id,
                                    pt.b_category,
                                    CAST (spo.sale_date AS DATE),
                                    SUM (amount) AS amount,
                                    SUM (profit) AS profit
                                FROM
                                    sy_pos_order spo
                                    LEFT JOIN product_template pt
                                        ON   spo.product = pt.id
                                GROUP BY
                                    spo.company_id,
                                    pt.brand_id,
                                    pt.b_category,
                                    CAST (spo.sale_date AS DATE)
                            ) sale
                            LEFT JOIN (
                                     SELECT
                                         sp.company_id,
                                         csp.category,
                                         bsp.brand,
                                         bspd.date,
                                         bspd.plan_sale,
                                         bspd.plan_profit
                                     FROM
                                         brand_sale_plan_daily bspd
                                         LEFT JOIN brand_sale_plan bsp
                                             ON   bspd.brand_sale_plan = bsp.id
                                         LEFT JOIN category_sale_plan csp
                                             ON   csp.id = bsp.category_sale_plan
                                         LEFT JOIN sale_plan sp
                                             ON   csp.sale_plan_id = sp.id
                                 ) brand_plan
                                ON   sale.company_id = brand_plan.company_id
                                AND sale.b_category = brand_plan.category
                                AND sale.brand_id = brand_plan.brand
                                AND sale.sale_date = brand_plan.date
                        WHERE
                            sale.sale_date BETWEEN (
                                SELECT
                                    CAST (CAST (now() AS CHAR (7)) || '-01' AS DATE)
                            ) AND (
                                SELECT
                                    CAST(
                                        CAST(
                                            (
                                                SELECT
                                                    now() + INTERVAL '1 month'
                                            ) AS CHAR (7)
                                        ) || '-01' AS DATE
                                    ) - INTERVAL '1 Second'
                            )
                            ) aa
                            )
                    """)