# -*- coding: utf-8 -*-
import datetime

import xlrd
from xlrd import xldate_as_tuple

from openerp.osv import fields, osv
from BNmssql import Lz_read_SQLCa, Lz_write_SQLCa

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class sale_plan(osv.osv):
    _name = 'sale.plan'
    _columns = {
        'code': fields.char(u'月计划编码'),
        'period_id': fields.many2one('account.period', u'账期',
                                     domain="['&',('company_id','=',company_id),('special','!=','True')]",required=True),
        'company_id': fields.many2one('res.company',u'公司',),
        'sale_weight':fields.float(u'销售权重(%)',digits=(16,4)),
        'profit_weight':fields.float(u'毛利权重(%)',digits=(16,4)),
        'plan_sale': fields.float(u'计划销售'),
        'plan_profit': fields.float(u'计划毛利'),
        'category_detail': fields.one2many('category.sale.plan', 'sale_plan_id', string=u'大类明细', ),
        'daily_detail': fields.one2many('sale.plan.daily', 'sale_plan_id', string=u'日明细', ),
        'state':fields.selection([('0','未抛转'),('1','已抛转'),],u'状态'),
    }
    _rec_name = 'code'
    _defaults = {
        'state':'0',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'sale.plan',
                                                                                                 context=c),
    }
    
    def create_plan(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False,
            'period_id':record.period_id.id,
        })
        return {
            'name': u'创建销售计划',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'create.sale.plan.detail',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }
        
    #创建计划日明细 
    def create_detail(self,cr,uid,ids,context=None):
#        #删除已有日明细
        sale_id=ids[0]
        unlink_ids=self.pool.get('sale.plan.daily').search(cr,uid,[('sale_plan_id','=',sale_id)])
        for unlink_id in unlink_ids:
            self.pool.get('sale.plan.daily').unlink(cr,uid,unlink_id)
        unlink_ids=self.pool.get('category.sale.plan.daily').search(cr,uid,[('category_sale_plan.sale_plan_id','=',sale_id)])
        for unlink_id in unlink_ids:
            self.pool.get('category.sale.plan.daily').unlink(cr,uid,unlink_id)
        unlink_ids=self.pool.get('brand.sale.plan.daily').search(cr,uid,[('brand_sale_plan.category_sale_plan.sale_plan_id','=',sale_id)])
        for unlink_id in unlink_ids:
            self.pool.get('brand.sale.plan.daily').unlink(cr,uid,unlink_id)
        #创建日明细
        record=self.browse(cr,uid,ids[0])
        start=record.period_id.date_start
        end=record.period_id.date_stop
        date=start
        while date<=end:
            self.pool.get('sale.plan.daily').create(cr,uid,{'date':date,'sale_plan_id':sale_id,})
            categ_ids=self.pool.get('category.sale.plan').search(cr,uid,[('sale_plan_id','=',sale_id)])
            for categ_id in categ_ids:
                self.pool.get('category.sale.plan.daily').create(cr,uid,{'date':date,'category_sale_plan':categ_id,})
            brand_ids=self.pool.get('brand.sale.plan').search(cr,uid,[('category_sale_plan.sale_plan_id','=',sale_id)])
            for brand_id in brand_ids:
                self.pool.get('brand.sale.plan.daily').create(cr,uid,{'date':date,'brand_sale_plan':brand_id,})
            date=datetime.datetime.strptime(date,"%Y-%m-%d").date()
            date = date + datetime.timedelta(days=1)
            date=datetime.datetime.strftime(date,"%Y-%m-%d")
        return
    
    #复制公司日明细到所有子模板
    def copy_detail(self,cr,uid,ids,context=None):
        sale_id=ids[0]
        #复制明细
        sale_plan=self.pool.get('sale.plan').browse(cr,uid,sale_id)
        daily_detail=sale_plan.daily_detail
        #计算公司明细
        for daily in daily_detail:
            val={
                 'plan_sale':daily.sale_plan_id.plan_sale*daily.sale_weight/100,
                 'plan_profit':daily.sale_plan_id.plan_profit*daily.profit_weight/100,
                 }
            self.pool.get('sale.plan.daily').write(cr,uid,daily.id,val)
        #复制明细
        for bigclass in daily_detail:
            date=bigclass.date
            sale_weight=bigclass.sale_weight
            profit_weight=bigclass.profit_weight
            records=self.pool.get('category.sale.plan.daily').search(cr,uid,[('date','=',date),
                                                                            ('category_sale_plan.sale_plan_id','=',sale_id)])
            for record in records:
                category=self.pool.get('category.sale.plan.daily').browse(cr,uid,record)
                plan_sale=category.category_sale_plan.plan_sale
                plan_profit=category.category_sale_plan.plan_profit
                self.pool.get('category.sale.plan.daily').write(cr,uid,record,{'sale_weight':sale_weight,
                                                                               'profit_weight':profit_weight,
                                                                               'plan_sale':plan_sale*sale_weight/100,
                                                                               'plan_profit':plan_profit*profit_weight/100,})
            records=self.pool.get('brand.sale.plan.daily').search(cr,uid,[('date','=',date),
                                                                            ('brand_sale_plan.category_sale_plan.sale_plan_id','=',sale_id)])
            for record in records:
                brand=self.pool.get('brand.sale.plan.daily').browse(cr,uid,record)
                plan_sale=brand.brand_sale_plan.plan_sale
                plan_profit=brand.brand_sale_plan.plan_profit
                self.pool.get('brand.sale.plan.daily').write(cr,uid,record,{'sale_weight':sale_weight,
                                                                            'profit_weight':profit_weight,
                                                                            'plan_sale':plan_sale*sale_weight/100,
                                                                            'plan_profit':plan_profit*profit_weight/100,})
        return
    
    def return_shangyi(self,cr,uid,ids,context=None):
        ms_write=Lz_write_SQLCa(self)
        record = self.browse(cr, uid, ids[0])
        daily_detail=record.daily_detail
        braid=record.company_id.code
        #抛转之前删除临时表的不是本账期的数据
        sql="delete from bn_temp_import_budget_dailly where braid='{0}'"
        sql=sql.format(braid)
        ms_write.ExecNonQuery(sql.encode('utf-8'))
        #抛转
        sql=""
        for daily in daily_detail:
            update_sql="""insert into bn_temp_import_budget_dailly
                        (braid,itemid,plansale,plantype,procdate,itemname,classid,planprofit)
                        select '{0}', '{1}', '{2}', 0, '{3}', '{4}', 0, {5}; """
            update_sql=update_sql.format(braid,
                                         braid,
                                         daily.plan_sale,
                                         daily.date,
                                         daily.sale_plan_id.company_id.name,
                                         daily.plan_profit)
            sql=sql+update_sql
        ms_write.ExecNonQuery(sql.encode('utf-8'))
        sql=""
        categ_daily=self.pool.get('category.sale.plan.daily').search(cr,uid,[('category_sale_plan.sale_plan_id','=',record.id)])
        for categ_daily_id in categ_daily:
            daily=self.pool.get('category.sale.plan.daily').browse(cr,uid,categ_daily_id)
            update_sql="""
                    insert into bn_temp_import_budget_dailly
                        (braid,itemid,plansale,plantype,procdate,itemname,classid,planprofit)
                    select '{0}', '{1}', '{2}', 2, '{3}', '{4}', '{5}', {6};
            """
            update_sql=update_sql.format(braid,
                                         daily.category_sale_plan.category.code,
                                         daily.plan_sale,
                                         daily.date,
                                         daily.category_sale_plan.category.name,
                                         daily.category_sale_plan.sale_plan_id.company_id.code,
                                         daily.plan_profit)
            sql=sql+update_sql
        ms_write.ExecNonQuery(sql.encode('utf-8'))
        sql=""
        brand_daily=self.pool.get('brand.sale.plan.daily').search(cr,uid,[('brand_sale_plan.category_sale_plan.sale_plan_id','=',record.id)])
        for brand_daily_id in brand_daily:
            daily=self.pool.get('brand.sale.plan.daily').browse(cr,uid,brand_daily_id)
            update_sql="""
                    insert into bn_temp_import_budget_dailly
                        (braid,itemid,plansale,plantype,procdate,itemname,classid,planprofit)
                    select '{0}', '{1}', '{2}', 1, '{3}', '{4}', '{5}', {6};
            """
            update_sql=update_sql.format(braid,
                                         daily.brand_sale_plan.brand.code,
                                         daily.plan_sale,
                                         daily.date,
                                         daily.brand_sale_plan.brand.name,
                                         daily.brand_sale_plan.category_sale_plan.category.code,
                                         daily.plan_profit)
            sql=sql+update_sql
        ms_write.ExecNonQuery(sql.encode('utf-8'))
        self.write(cr,uid,ids[0],{'state':'1',})
        return

    #重算
    def update(self,cr,uid,ids,context=None):
        record=self.pool.get('sale.plan').browse(cr,uid,ids[0])
        self.pool.get('sale.plan').update_daily(cr,uid,[record.id],context=None)
        self.pool.get('sale.plan').update_category_plan(cr,uid,[record.id],context=None)
        category_detail=record.category_detail
        for category in category_detail:
            self.pool.get('category.sale.plan').update_daily(cr,uid,[category.id],context=None)
            self.pool.get('category.sale.plan').update_brand_plan(cr,uid,[category.id],context=None)
            for brand in category.brand_detail:
                self.pool.get('brand.sale.plan').update_daily(cr,uid,[brand.id],context=None)
        return
       
    #重算日明细
    def update_daily(self,cr,uid,ids,context=None):
        record=self.pool.get('sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        daily_detail=record.daily_detail
        for daily in daily_detail:
            if daily.plan_sale!=plan_sale*daily.sale_weight/100:
                self.pool.get('sale.plan.daily').write(cr,uid,daily.id,{'plan_sale':plan_sale*daily.sale_weight/100})
            if daily.plan_profit!=plan_profit*daily.profit_weight/100:
                self.pool.get('sale.plan.daily').write(cr,uid,daily.id,{'plan_profit':plan_profit*daily.profit_weight/100})
        return
    
    #重算品牌明细,权重不变，修改改明细的值
    def update_category_plan(self,cr,uid,ids,context=None):
        record=self.pool.get('sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        category_detail=record.category_detail
        for category in category_detail:
            if category.plan_sale!=plan_sale*category.sale_weight/100:
                self.pool.get('category.sale.plan').write(cr,uid,category.id,{'plan_sale':plan_sale*category.sale_weight/100})
            if category.plan_profit!=plan_profit*category.profit_weight/100:
                self.pool.get('category.sale.plan').write(cr,uid,category.id,{'plan_profit':plan_profit*category.profit_weight/100})
        return
    
    #重算品牌明细,值不变，修改明细的权重
    def update_category_weight(self,cr,uid,ids,context=None):
        record=self.pool.get('sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        category_detail=record.category_detail
        for category in category_detail:
            val={}
            if plan_sale==0:
                val['sale_weight']=0
            elif category.sale_weight!=category.plan_sale/plan_sale*100:
                val['sale_weight']=category.plan_sale/plan_sale*100
            if plan_profit==0:
                val['profit_weight']=0
            elif category.profit_weight!=category.plan_profit/plan_profit*100:
                val['profit_weight']=category.plan_profit/plan_profit*100
            if val:
                self.pool.get('category.sale.plan').write(cr,uid,category.id,val)
        return 

class sale_plan_daily(osv.osv):
    _name = 'sale.plan.daily'
    _columns = {
        'date': fields.date(u'日期'),
        'sale_weight':fields.float(u'销售权重(%)',digits=(16,4)),
        'profit_weight':fields.float(u'毛利权重(%)',digits=(16,4)),
        'plan_sale': fields.float(u'计划销售'),
        'plan_profit': fields.float(u'计划毛利'),
        'sale_plan_id': fields.many2one('sale.plan', u'公司月计划', ondelete='cascade'),
    }


class category_sale_plan(osv.osv):
    _name = 'category.sale.plan'
    _columns = {
        'category': fields.many2one('product.category', u'大类', domain="[('parent_id.name','=','乐之产品分类')]",
                                    ondelete='cascade'),
        'sale_weight':fields.float(u'销售权重(%)',digits=(16,4)),
        'profit_weight':fields.float(u'毛利权重(%)',digits=(16,4)),
        'plan_sale': fields.float(u'计划销售'),
        'plan_profit': fields.float(u'计划毛利'),
        'sale_plan_id': fields.many2one('sale.plan', u'月计划', ondelete='cascade'),
        'state':fields.related('sale_plan_id','state',type='selection',
                               selection=[('0','未抛转'),('1','已抛转'),],string=u'状态'),
        'period_id': fields.related('sale_plan_id', 'period_id', type='many2one', relation='account.period',
                                    string=u'账期', readonly=True, store=True),
        'company_id': fields.related('sale_plan_id', 'company_id', type='many2one', relation='res.company',
                                     string=u'公司', readonly=True, store=True),
        'brand_detail': fields.one2many('brand.sale.plan', 'category_sale_plan', string=u'品牌明细'),
        'daily_detail': fields.one2many('category.sale.plan.daily', 'category_sale_plan', string=u'日明细'),
    }
    _sql_constraints = [
        ('category_uniq', 'unique(category, sale_plan_id)', u'一个计划不允许有两个相同的大类！！！')
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        if context is None:
            context = {}
        res=[]
        for r in self.browse(cr, uid, ids):
            res.append((r.id,r.sale_plan_id.code+r.category.name))
        return res
    
    #重算
    def update(self,cr,uid,ids,context=None):
        record=self.pool.get('category.sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        #大类日明细重算
        self.pool.get('category.sale.plan').update_daily(cr,uid,[record.id],context=None)
        #大类下的品牌和品牌日明细重算
        for detail in record.brand_detail:
            val={}
            if detail.plan_sale!=detail.sale_weight*plan_sale/100:
                val['plan_sale']=detail.sale_weight*plan_sale/100
            if detail.plan_profit!=detail.profit_weight*plan_profit/100:
                val['plan_profit']=detail.profit_weight*plan_profit/100
            if val:
                self.pool.get('brand.sale.plan').write(cr,uid,detail.id,val)
                self.pool.get('brand.sale.plan').update_daily(cr,uid,[detail.id],context=None)
        #公司计划的重算
        plan=record.sale_plan_id
        plan_sale_sum=0.0
        plan_profit_sum=0.0
        for detail in plan.category_detail:
            plan_sale_sum=plan_sale_sum+detail.plan_sale
            plan_profit_sum=plan_profit_sum+detail.plan_profit
        self.pool.get('sale.plan').write(cr,uid,plan.id,{
                                                         'plan_sale':plan_sale_sum,
                                                         'plan_profit':plan_profit_sum,
                                                         })
        self.pool.get('sale.plan').update_daily(cr,uid,[plan.id],context=None)
        self.pool.get('sale.plan').update_category_weight(cr,uid,[plan.id],context=None)
        return

    #重算日明细
    def update_daily(self,cr,uid,ids,context=None):
        record=self.pool.get('category.sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        daily_detail=record.daily_detail
        for daily in daily_detail:
            if daily.plan_sale!=plan_sale*daily.sale_weight/100:
                self.pool.get('category.sale.plan.daily').write(cr,uid,daily.id,{'plan_sale':plan_sale*daily.sale_weight/100})
            if daily.plan_profit!=plan_profit*daily.profit_weight/100:
                self.pool.get('category.sale.plan.daily').write(cr,uid,daily.id,{'plan_profit':plan_profit*daily.profit_weight/100})
        return
    
    #重算品牌明细,权重不变，修改改明细的值
    def update_brand_plan(self,cr,uid,ids,context=None):
        record=self.pool.get('category.sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        brand_detail=record.brand_detail
        for brand in brand_detail:
            brand_plan_sale=plan_sale*brand.sale_weight/100
            brand_plan_profit=plan_profit*brand.profit_weight/100
            if brand.plan_sale!=brand_plan_sale:
                self.pool.get('brand.sale.plan').write(cr,uid,brand.id,{'plan_sale':brand_plan_sale})
            if brand.plan_profit!=brand_plan_profit:
                self.pool.get('brand.sale.plan').write(cr,uid,brand.id,{'plan_profit':brand_plan_profit})
        return True
    
    #重算品牌明细,值不变，修改明细的权重
    def update_brand_weight(self,cr,uid,ids,context=None):
        record=self.pool.get('category.sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        brand_detail=record.brand_detail
        for brand in brand_detail:
            val={}
            if plan_sale==0:
                val['sale_weight']=0
            elif brand.sale_weight!=brand.plan_sale/plan_sale*100:
                val['sale_weight']=brand.plan_sale/plan_sale*100
            if plan_profit==0:
                val['profit_weight']=0
            elif brand.profit_weight!=brand.plan_profit/plan_profit*100:
                val['profit_weight']=brand.plan_profit/plan_profit*100
            if val:
                self.pool.get('brand.sale.plan').write(cr,uid,brand.id,val)
        return
    
class category_sale_plan_daily(osv.osv):
    _name = 'category.sale.plan.daily'
    _columns = {
        'date': fields.date(u'日期'),
        'sale_weight':fields.float(u'销售权重(%)',digits=(16,4)),
        'profit_weight':fields.float(u'毛利权重(%)',digits=(16,4)),
        'plan_sale': fields.float(u'计划销售'),
        'plan_profit': fields.float(u'计划毛利'),
        'category_sale_plan': fields.many2one('category.sale.plan', u'大类月计划', ondelete='cascade'),
    }


class brand_sale_plan(osv.osv):
    _name = 'brand.sale.plan'
    _columns = {
        'brand': fields.many2one('product.brand', u'品牌', ),
        'sale_weight':fields.float(u'销售权重(%)',digits=(16,4)),
        'profit_weight':fields.float(u'毛利权重(%)',digits=(16,4)),
        'plan_sale': fields.float(u'计划销售'),
        'plan_profit': fields.float(u'计划毛利'),
        'daily_detail': fields.one2many('brand.sale.plan.daily', 'brand_sale_plan', string=u'日明细'),
        'category_sale_plan': fields.many2one('category.sale.plan', u'大类计划', ondelete='cascade'),
        'sale_plan_id':fields.related('category_sale_plan','sale_plan_id',type='many2one',
                                       relation='sale.plan',string=u'公司计划',store=True),
        'state':fields.related('category_sale_plan','state',type='selection',
                               selection=[('0','未抛转'),('1','已抛转'),],string=u'状态'),
        'period_id': fields.related('category_sale_plan', 'period_id', type='many2one', relation='account.period',
                                    string=u'账期', readonly=True, store=True),
        'company_id': fields.related('category_sale_plan', 'company_id', type='many2one', relation='res.company',
                                     string=u'公司', readonly=True, store=True),
    }
    _sql_constraints = [
        ('brand_uniq', 'unique(brand,category_sale_plan)', u'一个大类不允许有两个相同的品牌！！！')
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        if context is None:
            context = {}
        res=[]
        for r in self.browse(cr, uid, ids):
            res.append((r.id,r.sale_plan_id.code+r.category_sale_plan.category.name+r.brand.name))
        return res
    
    #重算
    def update(self,cr,uid,ids,context=None):
        record=self.pool.get('brand.sale.plan').browse(cr,uid,ids[0])
        #重算日明细
        self.pool.get('brand.sale.plan').update_daily(cr,uid,[record.id],context=None)
        #重算大类
        category=record.category_sale_plan
        category_sale_sum=0.0
        category_profit_sum=0.0
        for detail in category.brand_detail:
            category_sale_sum=category_sale_sum+detail.plan_sale
            category_profit_sum=category_profit_sum+detail.plan_profit
        self.pool.get('category.sale.plan').write(cr,uid,category.id,{
                                                                      'plan_sale':category_sale_sum,
                                                                      'plan_profit':category_profit_sum,
                                                                      })
        self.pool.get('category.sale.plan').update_daily(cr,uid,[category.id],context=None)
        self.pool.get('category.sale.plan').update_brand_weight(cr,uid,[category.id],context=None)
        #重算公司
        plan=record.category_sale_plan.sale_plan_id
        plan_sale_sum=0.0
        plan_profit_sum=0.0
        for detail in plan.category_detail:
            plan_sale_sum=plan_sale_sum+detail.plan_sale
            plan_profit_sum=plan_profit_sum+detail.plan_profit
        self.pool.get('sale.plan').write(cr,uid,plan.id,{
                                                         'plan_sale':plan_sale_sum,
                                                         'plan_profit':plan_profit_sum,
                                                         })
        self.pool.get('sale.plan').update_daily(cr,uid,[plan.id],context=None)
        self.pool.get('sale.plan').update_category_weight(cr,uid,[plan.id],context=None)
        return

    #重算日明细
    def update_daily(self,cr,uid,ids,context=None):
        record=self.pool.get('brand.sale.plan').browse(cr,uid,ids[0])
        plan_sale=record.plan_sale
        plan_profit=record.plan_profit
        daily_detail=record.daily_detail
        for daily in daily_detail:
            if daily.plan_sale!=plan_sale*daily.sale_weight/100:
                self.pool.get('brand.sale.plan.daily').write(cr,uid,daily.id,{'plan_sale':plan_sale*daily.sale_weight/100})
            if daily.plan_profit!=plan_profit*daily.profit_weight/100:
                self.pool.get('brand.sale.plan.daily').write(cr,uid,daily.id,{'plan_profit':plan_profit*daily.profit_weight/100})
        return
    
class brand_sale_plan_daily(osv.osv):
    _name = 'brand.sale.plan.daily'
    _columns = {
        'date': fields.date(u'日期'),
        'sale_weight':fields.float(u'销售权重(%)',digits=(16,4)),
        'profit_weight':fields.float(u'毛利权重(%)',digits=(16,4)),
        'plan_sale': fields.float(u'计划销售'),
        'plan_profit': fields.float(u'计划毛利'),
        'brand_sale_plan': fields.many2one('brand.sale.plan', u'品牌月计划', ondelete='cascade'),
    }


class import_sale_plan(osv.osv_memory):
    _name = 'import.sale.plan'
    _columns = {
        'company_id': fields.many2one('res.company', u'门店'),
        'period_id': fields.many2one('account.period', u'账期', domain="[('company_id','=',company_id)]"),
    }

    def import_sale_plan(self, cr, uid, ids, context=None):
        import_sale_plan = self.browse(cr, uid, ids[0])
        period = import_sale_plan.period_id
        code = period.code
        begin = period.date_start
        begin = datetime.datetime.strptime(begin, "%Y-%m-%d").date()
        end = period.date_stop
        end = datetime.datetime.strptime(end, "%Y-%m-%d").date()
        yearmonth = code[3:7] + code[0:2]
        company_id = import_sale_plan.company_id
        braid = company_id.code
        # 检查是否有已导入数据，如果有，则删除
        delete_record = self.pool.get('sale.plan').search(cr, uid, [('period_id', '=', period.id),
                                                                    ('company_id', '=', company_id.id)])
        for delete_id in delete_record:
            self.pool.get('sale.plan').unlink(cr, uid, delete_id)
        # 导入销售计划
        sql = """SELECT isnull(PlanSale,0),isnull(PlanProfit,0) FROM sale_plan
            WHERE plantype='0' AND BraId='%s' AND YearMon='%s'""" % (braid, yearmonth)
        sql = sql.encode('utf-8')

        ms = Lz_read_SQLCa(self)
        plan_record = ms.ExecQuery(sql.encode('utf-8'))
        for (PlanSale, PlanProfit) in plan_record:
            plan_code = braid + '-' + yearmonth
            plan_id = self.pool.get('sale.plan').create(cr, uid, {
                'company_id': company_id.id,
                'period_id': period.id,
                'code': plan_code,
                'plan_sale': PlanSale,
                'plan_profit': PlanProfit,
            })
        sql = """SELECT itemid,isnull(PlanSale,0),isnull(PlanProfit,0) FROM sale_plan WHERE plantype='2' AND BraId='%s' AND YearMon='%s'""" % (
            braid, yearmonth)
        sql = sql.encode('utf-8')
        category_record = ms.ExecQuery(sql.encode('utf-8'))
        for (itemid, PlanSale, PlanProfit) in category_record:
            if itemid:
                categ_id = self.pool.get('product.category').search(cr, uid, [('code', '=', itemid)])[0]
                categ_code = self.pool.get('product.category').browse(cr, uid, categ_id).code
            else:
                categ_id = False
                categ_code = 'null'
            category_plan_sale = self.pool.get('category.sale.plan').create(cr, uid, {
                'sale_plan_id': plan_id,
                'period_id': period.id,
                'company_id': company_id.id,
                'category': categ_id,
                'plan_sale': PlanSale,
                'plan_profit': PlanProfit,
            })
            sql = "SELECT procdate,plansale,planprofit FROM bn_temp_import_budget_dailly WHERE plantype='2' and itemid='%s' and braid='%s'" % (
                categ_code, braid)
            sql = sql.encode('utf-8')
            category_detail_record = ms.ExecQuery(sql.encode('utf-8'))
            for (procdate, plansale, planprofit) in category_detail_record:
                self.pool.get('category.sale.plan.daily').create(cr, uid, {
                    'date': procdate,
                    'plan_sale': plansale,
                    'plan_profit': planprofit,
                    'category_sale_plan': category_plan_sale,
                })
            sql = "SELECT itemid,isnull(PlanSale,0),isnull(PlanProfit,0) FROM sale_plan WHERE plantype='1' AND BraId='%s' AND YearMon='%s' and classid='%s'" % (
                braid, yearmonth, categ_code)
            sql = sql.encode('utf-8')
            brand_record = ms.ExecQuery(sql.encode('utf-8'))
            for (itemid, PlanSale, PlanProfit) in brand_record:
                if itemid:
                    brand_id = self.pool.get('product.brand').search(cr, uid, [('code', '=', itemid)])
                    brand_id = brand_id and brand_id[0] or False
                else:
                    brand_id = False
                brand_plan_sale = self.pool.get('brand.sale.plan').create(cr, uid, {
                    'category_sale_plan': category_plan_sale,
                    'period_id': period.id,
                    'company_id': company_id.id,
                    'brand': brand_id,
                    'plan_sale': PlanSale,
                    'plan_profit': PlanProfit,
                })
                if brand_id:
                    brand = self.pool.get('product.brand').browse(cr, uid, brand_id)
                    brand_code = brand.code
                else:
                    brand_code = 'null'
                sql = "SELECT procdate,plansale,planprofit FROM bn_temp_import_budget_dailly WHERE plantype='1' and itemid='%s' and braid='%s' and classid='%s'" % (
                    brand_code, braid, categ_code)
                brand_detail_record = ms.ExecQuery(sql.encode('utf-8'))
                for (procdate, plansale, planprofit) in brand_detail_record:
                    self.pool.get('brand.sale.plan.daily').create(cr, uid, {
                        'date': procdate,
                        'plan_sale': plansale,
                        'plan_profit': planprofit,
                        'brand_sale_plan': brand_plan_sale,
                    })
        return


class import_file_sale_plan(osv.osv_memory):
    _name = 'import.file.sale.plan'
    _columns = {
        'company_id': fields.many2one('res.company', u'门店',required=True),
        'period_id': fields.many2one('account.period', u'账期', domain="[('company_id','=',company_id)]",required=True),
        'datas_fname': fields.char('File Name', size=256, ),
        'file': fields.binary('File', ),
    }

    def _excel_table_byname(self, files, table):
        try:
            # data = xlrd.open_workbook(path)读文件目录#sheet_by_name(u'Sheet 1')
            data = xlrd.open_workbook(file_contents=files)
            table = data.sheet_by_index(table)
        except:
            raise osv.except_osv(_('Error!'), _(u'该导入模板的工作表名有误，请更正为:Sheet 1'))
        return table

    def import_plan(self, cr, uid, ids, context=None):
        import_plan = self.browse(cr, uid, ids[0])
        files = import_plan.file
        company_id = import_plan.company_id
        period_id = import_plan.period_id
        #删除已导入的计划
        delete_records=self.pool.get('sale.plan').search(cr,uid,[('company_id','=',company_id.id),('period_id','=',period_id.id)])
        for delete_id in delete_records:
            self.pool.get('sale.plan').unlink(cr,uid,[delete_id])
        if not files:
            return False
        # 读取table1数据
        table_0 = self._excel_table_byname(files.decode('base64'), 0)
        table_1 = self._excel_table_byname(files.decode('base64'), 1)
        table_2 = self._excel_table_byname(files.decode('base64'), 2)
        #检查文件门店日期
        nrows = table_0.nrows
        for rownum in range(1, nrows):
            row = table_0.row_values(rownum)
            if row:
                row_date=datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d')
                if row_date[0:4]!=period_id.name[3:7] or row_date[5:7]!=period_id.name[0:2]:
                    raise osv.except_osv((u'错误'), (u'店目标有错误的日期！！'))
                row_company=row[0]
                if row_company!=company_id.code:
                    raise osv.except_osv((u'错误'), (u'店目标有错误的门店！！'))
        nrows = table_1.nrows
        for rownum in range(1, nrows):
            row = table_1.row_values(rownum)
            if row:
                row_date=datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d')
                if row_date[0:4]!=period_id.name[3:7] or row_date[5:7]!=period_id.name[0:2]:
                    raise osv.except_osv((u'错误'), (u'大类目标有错误的日期！！'))
                row_company=row[0]
                if row_company!=company_id.code:
                    raise osv.except_osv((u'错误'), (u'大类目标有错误的门店！！'))
        nrows = table_2.nrows
        for rownum in range(1, nrows):
            row = table_2.row_values(rownum)
            if row:
                row_date=datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d')
                if row_date[0:4]!=period_id.name[3:7] or row_date[5:7]!=period_id.name[0:2]:
                    raise osv.except_osv((u'错误'), (u'品牌目标有错误的日期！！'))
                row_company=row[0]
                if row_company!=company_id.code:
                    raise osv.except_osv((u'错误'), (u'品牌目标有错误的门店！！'))
        # 公司日计划，计算月计划的销售额和毛利
        nrows = table_0.nrows
        res = []
        sum_plan_sale = 0
        sum_plan_profit = 0
        for rownum in range(1, nrows):
            row = table_0.row_values(rownum)
            if row:
                braid_code = row[1]
                plan_sale = row[2]
                plan_profit = row[3]
                sum_plan_sale = sum_plan_sale + plan_sale
                sum_plan_profit = sum_plan_profit + plan_profit
                res.append((0, 0, {
                    'date': datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d'),
                    'plan_sale': plan_sale,
                    'plan_profit': plan_profit,
                }))
        sale_plan = self.pool.get('sale.plan').create(cr, uid, {
            'code': company_id.code + '-' + period_id.code[3:7] + period_id.code[0:2],
            'period_id': period_id.id,
            'company_id': company_id.id,
            'plan_sale': sum_plan_sale,
            'plan_profit': sum_plan_profit,
            'daily_detail': res,
        })
        # 导入table2的数据
        # 大类日计划，建立大类月计划，关联公司计划，计算大类月计划的销售额和毛利
        nrows = table_1.nrows
        categ_dict = {}
        for rownum in range(1, nrows):
            row = table_1.row_values(rownum)
            if row:
                categ_code = row[1]
                plan_sale = row[2]
                plan_profit = row[3]
                if categ_code in categ_dict.keys():
                    categ_id = categ_dict[categ_code]
                    self.pool.get('category.sale.plan.daily').create(cr, uid, {
                        'date': datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d'),
                        'plan_sale': plan_sale,
                        'plan_profit': plan_profit,
                        'category_sale_plan': categ_id,
                    })
                else:
                    category = self.pool.get('product.category').search(cr, uid, [('code', '=', categ_code)])
                    categ_id = self.pool.get('category.sale.plan').create(cr, uid, {
                        'period_id': period_id.id,
                        'company_id': company_id.id,
                        'sale_plan_id': sale_plan,
                        'category': category and category[0] or False,
                    })
                    categ_dict[categ_code] = categ_id
                    self.pool.get('category.sale.plan.daily').create(cr, uid, {
                        'date': datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d'),
                        'plan_sale': plan_sale,
                        'plan_profit': plan_profit,
                        'category_sale_plan': categ_id,
                    })
        for categ in categ_dict.keys():
            categ_id = categ_dict[categ]
            categ = self.pool.get('category.sale.plan').browse(cr, uid, categ_id)
            daily_detail = categ.daily_detail
            sum_plan_sale = 0
            sum_plan_profit = 0
            for detail in daily_detail:
                sum_plan_sale = sum_plan_sale + detail.plan_sale
                sum_plan_profit = sum_plan_profit + detail.plan_profit
            self.pool.get('category.sale.plan').write(cr, uid, categ_id, {
                'plan_sale': sum_plan_sale,
                'plan_profit': sum_plan_profit,
            })
        # 读取table3
        # 品牌日计划，建立品牌月计划，计算当月计划的销售额和毛利，并关联对应的大类月计划
        nrows = table_2.nrows
        brand_dict = {}
        for rownum in range(1, nrows):
            row = table_2.row_values(rownum)
            if row:
                brand_code = row[1]
                plan_sale = row[2]
                plan_profit = row[3]
                categ_code = row[6]
                categ_id = categ_dict[categ_code]
                if brand_code in brand_dict.keys():
                    brand_id = brand_dict[brand_code]
                    self.pool.get('brand.sale.plan.daily').create(cr, uid, {
                        'date': datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d'),
                        'plan_sale': plan_sale,
                        'plan_profit': plan_profit,
                        'brand_sale_plan': brand_id,
                    })
                else:
                    brand = self.pool.get('product.brand').search(cr, uid, [('code', '=', brand_code)])
                    brand_id = self.pool.get('brand.sale.plan').create(cr, uid, {
                        'period_id': period_id.id,
                        'company_id': company_id.id,
                        'category_sale_plan': categ_id,
                        'brand': brand and brand[0] or False,
                    })
                    brand_dict[brand_code] = brand_id
                    self.pool.get('brand.sale.plan.daily').create(cr, uid, {
                        'date': datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d'),
                        'plan_sale': plan_sale,
                        'plan_profit': plan_profit,
                        'brand_sale_plan': brand_id,
                    })
        for brand in brand_dict.keys():
            brand_id = brand_dict[brand]
            brand = self.pool.get('brand.sale.plan').browse(cr, uid, brand_id)
            daily_detail = brand.daily_detail
            sum_plan_sale = 0
            sum_plan_profit = 0
            for detail in daily_detail:
                sum_plan_sale = sum_plan_sale + detail.plan_sale
                sum_plan_profit = sum_plan_profit + detail.plan_profit
            self.pool.get('brand.sale.plan').write(cr, uid, brand_id, {
                'plan_sale': sum_plan_sale,
                'plan_profit': sum_plan_profit,
            })
        self.return_shangyi(cr,uid,ids,context)
        return

#文件数据抛转商益
    def return_shangyi(self,cr,uid,ids,context):
        import_plan = self.browse(cr, uid, ids[0])
        files = import_plan.file
        period = import_plan.period_id.name
        period_code=period[3:7]+period[0:2]
        year=int(period[3:7])
        mon=int(period[0:2])
        if not files:
            return False
        table_0 = self._excel_table_byname(files.decode('base64'), 0)
        table_1 = self._excel_table_byname(files.decode('base64'), 1)
        table_2 = self._excel_table_byname(files.decode('base64'), 2)
        #删除已有数据
        delete_sql="delete from bn_temp_import_budget_dailly"
        ms_write=Lz_write_SQLCa(self)
        ms_write.ExecNonQuery(delete_sql.encode('utf-8'))
        #拼接店目标sql
        nrows = table_0.nrows
        braid_add_sql=''
        ms_write=Lz_write_SQLCa(self)
        for rownum in range(1, nrows):
            row = table_0.row_values(rownum)
            if row:
                row_date=datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d')
                if braid_add_sql:
                    braid_add_sql=braid_add_sql+""",('%s','%s','%s','%s','%s','%s','%s','0')
                    """%(row[0],row[1],row[2],row[3],row_date,row[5],row[6])
                else:
                    braid_add_sql=braid_add_sql+"""('%s','%s','%s','%s','%s','%s','%s','0')
                    """%(row[0],row[1],row[2],row[3],row_date,row[5],row[6])
        if braid_add_sql:
            braid_sql="""insert into bn_temp_import_budget_dailly(braid,itemid,plansale,planprofit,procdate,itemname,classid,plantype)
                    values """+braid_add_sql
            braid_sql=ms_write.ExecNonQuery(braid_sql.encode('utf-8'))
        #拼接大类目标sql
        nrows = table_1.nrows
        categ_add_sql=''
        for rownum in range(1, nrows):
            row = table_1.row_values(rownum)
            if row:
                row_date=datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d')
                if categ_add_sql:
                    categ_add_sql=categ_add_sql+""",('%s','%s','%s','%s','%s','%s','%s','2')
                    """%(row[0],row[1],row[2],row[3],row_date,row[5],row[6])
                else:
                    categ_add_sql=categ_add_sql+"""('%s','%s','%s','%s','%s','%s','%s','2')
                    """%(row[0],row[1],row[2],row[3],row_date,row[5],row[6])
        if categ_add_sql:
            categ_sql="""insert into bn_temp_import_budget_dailly(braid,itemid,plansale,planprofit,procdate,itemname,classid,plantype)
                    values """+categ_add_sql
            braid_sql=ms_write.ExecNonQuery(categ_sql.encode('utf-8'))
        #拼接品牌目标sql
        #插入sql最多1000条记录,记录数r=1000
        r=1000
        nrows = table_2.nrows
        for rowc in range(0,int((nrows-1)/r)+1):
            brand_add_sql=''
            for rownum in range(1+rowc*r, min((rowc+1)*r+1,nrows)):
                row = table_2.row_values(rownum)
                if row:
                    row_date=datetime.datetime(*xldate_as_tuple(row[4], 0)).strftime('%Y-%m-%d')
                    if brand_add_sql:
                        brand_add_sql=brand_add_sql+""",('%s','%s','%s','%s','%s','%s','%s','1')
                        """%(row[0],row[1],row[2],row[3],row_date,row[5],row[6])
                    else:
                        brand_add_sql=brand_add_sql+"""('%s','%s','%s','%s','%s','%s','%s','1')
                        """%(row[0],row[1],row[2],row[3],row_date,row[5],row[6])
            if brand_add_sql:
                brand_sql="""insert into bn_temp_import_budget_dailly(braid,itemid,plansale,planprofit,procdate,itemname,classid,plantype)
                        values """+brand_add_sql
                braid_sql=ms_write.ExecNonQuery(brand_sql.encode('utf-8'))
        #执行存储过程
        exec_sql = "exec proc_bn_import_sale_plan '{0}','{1}','{2}'".format(period_code,year,mon)
        ms_write.ExecNonQuery(exec_sql.encode('utf-8'))
        return