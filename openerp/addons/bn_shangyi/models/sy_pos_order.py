# -*- coding: utf-8 -*-
from openerp.osv import fields,osv

class sy_pos_order(osv.osv):
    _name='sy.pos.order'
    _columns={
              'code':fields.char(u'pos单号'),
              'product':fields.many2one('product.template',u'产品'),
              'b_category':fields.related('product','b_category',type='many2one',relation='product.category',string=u'大类'),
              'PosNo':fields.char('POS机号'),
              'sale_man':fields.many2one('hr.employee',u'营业员'),
              'sale_date':fields.datetime(u'销售时间'),#销售时间
              'sale_type':fields.selection([('0',u'正常销售'),('1',u'退货'),('2',u'更正'),('4',u'满额换购'),('5',u'逢双促销'),('6',u'积分换购'),('7',u'买就送（折）'),('8',u'捆绑销售'),('9',u'时段促销'),('A',u'满减'),('C',u'减角商品'),('D','优惠券'),('wg',u'网购')],u'销售类型'),
              'qty':fields.integer(u'数量'),
              'normal_price':fields.float(u'正常价'),
              'amount':fields.float(u'销售价'),
              'profit':fields.float(u'毛利',digit=(16,8),groups='bn_shangyi.group_profit'),
              'company_id':fields.many2one('res.company',u'门店'),
              }
    _sql_constraints= [
#        ('product_uniq', 'unique(code, product,amount)',"The same POS Order can't have the same product!"),
    ]
    _order='sale_date desc'
    
class sy_pos_payment(osv.osv):
    _name='sy.pos.payment'
    _columns={
              'code':fields.char(u'pos单号'),
              'date':fields.datetime(u'销售日期'),
              'paymodel':fields.selection([('0',u'让零'),  ('1',u'现金') ,('2',u'信用卡'),
                                           ('3',u'储值卡'),('4',u'购物券'),('5',u'其他'),
                                           ('6', u'让零'), ('7',u'支付宝'),('8',u'春天卡'),('w',u'微信')],
                                            u'支付类型'),
              'paymoney':fields.float(u'支付金额'),
              'company_id':fields.many2one('res.company',u'门店'),
              }
    _sql_constraints= [
#        ('model_uniq', 'unique(code, paymodel)',"The same POS Order can't have the same paymodel!"),
    ]
    _order='date desc'