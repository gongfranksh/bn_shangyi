# -*- coding: utf-8 -*-
import datetime
import types
import webbrowser
from openerp.osv import fields, osv
from BNmssql import Lz_read_SQLCa
import logging
import threading
from openerp import SUPERUSER_ID
from openerp import tools

from openerp.osv import osv
from openerp.api import Environment

_logger = logging.getLogger(__name__)


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


class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _columns = {
        'stamp': fields.integer(u'时间戳')
    }


class product_brand(osv.osv):
    _inherit = 'product.brand'
    _columns = {
        'stamp': fields.integer(u'时间戳')
    }


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'stamp': fields.integer(u'时间戳')
    }


class sync_shangyi_data(osv.osv_memory):
    _name = 'sync.shangyi.data'

    # _columns = {
    #     'code': fields.char(u'编码', required=True),
    #     'name': fields.char(u'名称'),
    #     'date': fields.date(u'日期'),
    #     'text': fields.text(u'备注'),
    # }

    def sync_product_class(self, cr, uid, ids, context=None):
        ms = Lz_read_SQLCa(self)
        # 导入产品类别
        # 获取更新记录范围，本地库的时间戳和服务端时间戳
        local_sql = """ 
                    select max(stamp) AS timestamp from product_category 
                  """
        remote_sql = "SELECT CONVERT(INT,max(timestamp)) AS timestamp from product_class "
        btw = self.query_period(local_sql, remote_sql)

        sql = """
                select ClassId,cast(ClassName as nvarchar(100)) as name,CAST (TIMESTAMP AS INT ) AS stamps
                from product_class
                where  CAST (TIMESTAMP AS INT ) between {0} and {1}
                  """
        sql = sql.format(btw['start_stamp'], btw['end_stamp'])

        product_class_list = ms.ExecQuery(sql.encode('utf-8'))
        _logger.info("product_class_list  have %d records need to update" % len(product_class_list))
        for (ClassId, name, stamp) in product_class_list:
            val = {
                'code': ClassId,
                'name': name,
                'stamp': stamp,
            }
            code = ClassId
            p_ids = self.pool.get('product.category').search_bycode(cr, uid, code)
            if p_ids:
                if val:
                    self.pool.get('product.category').write(cr, uid, p_ids, val)
            else:
                self.pool.get('product.category').create(cr, uid, val)

    def sync_product_brand(self, cr, uid, ids, context=None):
        ms = Lz_read_SQLCa(self)
        # 导入品牌
        local_sql = """ 
                    select max(stamp) AS timestamp from product_brand 
                  """
        remote_sql = "SELECT CONVERT(INT,max(timestamp)) AS timestamp from product_brand "
        btw = self.query_period(local_sql, remote_sql)
        sql = """
                SELECT pb.BrandId,cast(pb.BrandName as nvarchar(100)) as name,CAST (TIMESTAMP AS INT ) AS stamps 
                FROM product_brand pb
                where  CAST (TIMESTAMP AS INT ) between {0} and {1}
                  """
        sql = sql.format(btw['start_stamp'], btw['end_stamp'])
        product_brand_list = ms.ExecQuery(sql.encode('utf-8'))
        _logger.info("product_brand_list  have %d records need to update" % len(product_brand_list))
        for (BrandId, name, stamp) in product_brand_list:
            val={
                'code': BrandId,
                'name': name,
                'stamp': stamp,
                }
            brand_id = self.pool.get('product.brand').search_bycode(cr, uid, BrandId)
            if brand_id:
                    self.pool.get('product.brand').write(cr, uid, brand_id, val)
            else:
                self.pool.get('product.brand').create(cr, uid, {
                    'code': BrandId,
                    'name': name,
                    'stamp': stamp,
                })

    def sync_supplier(self, cr, uid, ids, context=None):
        ms = Lz_read_SQLCa(self)
        # 导入供应商
        local_sql = """ 
                    select max(stamp) AS timestamp from res_partner where supplier is true
                  """
        remote_sql = "SELECT CONVERT(INT,max(timestamp)) AS timestamp from supplier "
        btw = self.query_period(local_sql, remote_sql)
        sql = """
              select SupId,cast(SupName as nvarchar(100)) as name,cast(Addr as nvarchar(100)) as addr,
              Tel,Fax,Zip,Email,CAST (TIMESTAMP AS INT ) AS stamps  
              from supplier
               where  CAST (TIMESTAMP AS INT ) between {0} and {1}
                  """
        sql = sql.format(btw['start_stamp'], btw['end_stamp'])
        supplier_list = ms.ExecQuery(sql.encode('utf-8'))
        _logger.info("supplier_list  have %d records need to update" % len(supplier_list))
        for (SupId, name, addr, Tel, Fax, Zip, Email, stamp) in supplier_list:
            val={
                    'code': SupId,
                    'name': name,
                    'street': addr,
                    'phone': Tel,
                    'fax': Fax,
                    'zip': Zip,
                    'email': Email,
                    'is_company': True,
                    'supplier': True,
                    'customer': False,
                    'company_id': False,
                    'stamp': stamp
                }
            code = SupId
            p_ids = self.pool.get('res.partner').search_bycode(cr, uid, code)
            if p_ids:
                if val:
                    self.pool.get('res.partner').write(cr, uid, p_ids, val)
            else:
                self.pool.get('res.partner').create(cr, uid, val)

    def sync_product(self, cr, uid, ids, context=None):
        ms = Lz_read_SQLCa(self)
        # 导入产品
        local_sql = """ 
                    select max(stamp) AS timestamp from product_template 
                  """
        remote_sql = "SELECT CONVERT(INT,max(timestamp)) AS timestamp from product "
        btw = self.query_period(local_sql, remote_sql)
        sql = """
                select  ProId,Barcode,cast(ProName as nvarchar(100)) as name,cast(spec as nvarchar(100)) as spec,
                ClassId,SupId,isnull(NormalPrice,0),BrandId ,CAST (TIMESTAMP AS INT ) AS stamps 
                from product
                where  CAST (TIMESTAMP AS INT ) between {0} and {1}
                order by CAST (TIMESTAMP AS INT )
                  """
        sql = sql.format(btw['start_stamp'], btw['end_stamp'])
        product_list = ms.ExecQuery(sql.encode('utf-8'))
        _logger.info("product_list  have %d records need to update" % len(product_list))
        for (ProId, Barcode, name, spec, ClassId, SupId, NormalPrice, BrandId, stamp) in product_list:

            code = ProId
            p_id = self.pool.get('product.template').search_bycode(cr, uid, ProId)
            categ_id = self.pool.get('product.category').search_bycode(cr, uid, ClassId)
            m_categ_id = self.pool.get('product.category').search_bycode(cr, uid, ClassId[0:6])
            b_categ_id = self.pool.get('product.category').search_bycode(cr, uid, ClassId[0:4])
            sup_id = self.pool.get('res.partner').search_bycode(cr, uid, SupId)
            brand_id = self.pool.get('product.brand').search_bycode(cr, uid, BrandId)
            product = self.pool.get('product.template').browse(cr, uid, p_id)
            val={
                    'code': ProId,
                    'barcode': Barcode,
                    'name': name,
                    'spec': spec,
                    'list_price': NormalPrice,
                    'sale_ok': True,
                    'type': 'product',
                    'active': True,
                    'categ_id': categ_id,
                    'm_category': m_categ_id,
                    'b_category': b_categ_id,
                    'brand_id': brand_id,
                    'company_id': False,
                    'stamp': stamp,
                }

            if p_id:
                product = self.pool.get('product.template').browse(cr, uid, p_id)
                if val:
                    self.pool.get('product.template').write(cr, uid, p_id, val)
                seller_ids = product.seller_ids
                s_ids = []
                for seller_id in seller_ids:
                    s_ids.append(seller_id.name.id)
                if sup_id and sup_id not in s_ids:
                    unlink_ids = self.pool.get('product.supplierinfo').search(cr, uid,
                                                                              [('product_tmpl_id', '=', p_id)])
                    self.pool.get('product.supplierinfo').unlink(cr, uid, unlink_ids)
                    self.pool.get('product.supplierinfo').create(cr, uid, {
                        'product_tmpl_id': p_id,
                        'name': sup_id,
                    })
            else:
                product_tmpl_id = self.pool.get('product.template').create(cr, uid, val)
                if sup_id:
                    self.pool.get('product.supplierinfo').create(cr, uid, {
                        'product_tmpl_id': product_tmpl_id,
                        'name': sup_id,
                    })
        return

    def synch_product_category_parent(self, cr, uid, ids, context=None):
        # 产品分类分级
        c_ids = self.pool.get('product.category').search(cr, uid, [('code', '!=', False)])
        b_list = []
        m_list = []
        for c_id in c_ids:
            category = self.pool.get('product.category').browse(cr, uid, c_id)
            code = category.code
            if len(code) == 4:
                b_list.append({
                    'value': category.code,
                    'id': category.id,
                })
            elif len(code) == 6:
                m_list.append({
                    'value': category.code,
                    'id': category.id,
                })
        for c_id in c_ids:
            category = self.pool.get('product.category').browse(cr, uid, c_id)
            code = category.code
            if len(code) == 4:
                parent_id = False
                categ_id = self.pool.get('product.category').search(cr, uid, [('name', '=', u'乐之产品分类')])
                if categ_id:
                    parent_id = categ_id[0]
                if category.parent_id != parent_id:
                    self.pool.get('product.category').write(cr, uid, c_id, {'parent_id': parent_id})
            elif len(code) == 6:
                parent_id = False
                for b in b_list:
                    if category.code[0:4] == b.get('value'):
                        parent_id = b.get('id')
                if category.parent_id != parent_id:
                    self.pool.get('product.category').write(cr, uid, c_id, {'parent_id': parent_id})
            elif len(code) == 8:
                parent_id = False
                for m in m_list:
                    if category.code[0:6] == m.get('value'):
                        parent_id = m.get('id')
                if category.parent_id != parent_id:
                    self.pool.get('product.category').write(cr, uid, c_id, {'parent_id': parent_id})
        return

    def set_product_category_parent(self, cr, uid, ids, context=None):
        # 产品分类分级
        root_categ_id = self.pool.get('product.category').search(cr, uid, [('name', '=', u'乐之产品分类')])
        if root_categ_id:
            top_categ_id = self.pool.get('product.category').search(cr, uid, [('code', '=like', '____')])
            for top in top_categ_id:
                self.pool.get('product.category').write(cr, uid, top, {'parent_id': root_categ_id[0]})
                topcategory = self.pool.get('product.category').browse(cr, uid, top)
                mid_categ_id = self.pool.get('product.category').search(cr, uid,
                                                                        [('code', '=like', topcategory['code'] + '__')])
                for mid in mid_categ_id:
                    midcategory = self.pool.get('product.category').browse(cr, uid, mid)
                    self.pool.get('product.category').write(cr, uid, mid, {'parent_id': topcategory.id})
                    min_categ_id = self.pool.get('product.category').search(cr, uid,  [('code','=like', midcategory['code'] + '__')])
                    for min in min_categ_id:
                        mincategory = self.pool.get('product.category').browse(cr, uid, min)
                        self.pool.get('product.category').write(cr, uid, min, {'parent_id': midcategory.id})
        else:
                        val = {
                            'name': u'乐之产品分类',
                        }
                        self.pool.get('product.category').create(cr, uid, val)
        return


    def sync_employee(self, cr, uid, ids, context=None):
        # 导入员工
        ms = Lz_read_SQLCa(self)
        local_sql = """ 
                    select max(stamp) AS timestamp from hr_employee 
                  """
        remote_sql = "SELECT CONVERT(INT,max(timestamp)) AS timestamp from branch_employee"
        btw = self.query_period(local_sql, remote_sql)
        exec_sql="""
            SELECT be.BraId,be.EmpId,cast(be.EmpName as nvarchar(100)) as name,CAST (TIMESTAMP AS INT ) AS stamp 
            FROM branch_employee be
            where  CAST (TIMESTAMP AS INT ) between {0} and {1}            
        """
        exec_sql = exec_sql.format(btw['start_stamp'], btw['end_stamp'])
        employee_list = ms.ExecQuery(exec_sql.encode('utf-8'))
        _logger.info("employee_list  have %d records need to update" % len(employee_list))
        for (BraId, EmpId, name,stamp) in employee_list:
            e_id = self.pool.get('hr.employee').search_bycode(cr, uid, EmpId)
            company_id = self.pool.get('res.company').search_bycode(cr, uid, BraId)
            val={
                'company_id':company_id,
                'name':name,
                'stamp':stamp,
                'code':EmpId
            }
            if e_id:
                hr_employee = self.pool.get('hr.employee').browse(cr, uid, e_id)
                if hr_employee.company_id and hr_employee.company_id.id != company_id:
                    val['company_id'] = company_id
                if hr_employee.company_id == False and company_id:
                    val['company_id'] = company_id
                if hr_employee.name != name:
                    val['name'] = name
                if val:
                    self.pool.get('resource.resource').write(cr, uid, hr_employee.resource_id.id, val)
            else:
                self.pool.get('hr.employee').create(cr, uid, val)
        return


    def sync_pos(self, cr, uid, ids, context=None):
        day = 7
        proc_task=self.check_pos_data_daily(cr, uid, ids, day, context=None)
        for proc in proc_task:
            if proc['local_records_count']<>proc['remote_records_count']:
                _logger.info(" check_pos_data_daily ==>%s==>local have===> %s  remote  have===> %s " %
                             (proc['proc_date'], str(proc['local_records_count']), str(proc['remote_records_count'])))
                self.sync_pos_order(cr, uid, ids, proc['proc_date'], context=None)
            else:
                _logger.info(" %s=>alread done  " % proc['proc_date'])
        return

    def sync_pos_order(self, cr, uid, ids, sy_product_date, context=None):
        ms = Lz_read_SQLCa(self)
        date = sy_product_date

        # 删除当天数据
        del_ids = self.pool.get('sy.pos.order').search(cr, uid, [('sale_date', 'like', date + '%')])
        for del_id in del_ids:
            self.pool.get('sy.pos.order').unlink(cr, uid, del_id)
        del_ids = self.pool.get('sy.pos.payment').search(cr, uid, [('date', 'like', date + '%')])
        for del_id in del_ids:
            self.pool.get('sy.pos.payment').unlink(cr, uid, del_id)
        # 导入当天pos订单和pos支付

        exec_sql = """
            SELECT bs.BraId,DATEADD(hour,-8,bs.SaleDate) AS SaleDate,
            bs.proid,bs.SaleQty,bs.NormalPrice,bs.amount,bs.SaleId,
            bs.SaleMan,bs.SaleType,bs.PosNo,bs.profit 
            FROM v_bn_saledetail bs 
            WHERE convert(VARCHAR(10),bs.SaleDate,126)= '{0}'
                    """
        exec_sql = exec_sql.format(date)
        pos_order_list = ms.ExecQuery(exec_sql.encode('utf-8'))
        for (BraId, SaleDate, proid, SaleQty, NormalPrice, amount, SaleId, SaleMan, SaleType, PosNo,
             profit) in pos_order_list:
            product_id = self.pool.get('product.template').search_bycode(cr, uid, proid)
            company_id = self.pool.get('res.company').search_bycode(cr, uid, BraId)
            employee_id = self.pool.get('hr.employee').search_bycode(cr, uid, SaleMan)
            self.pool.get('sy.pos.order').create(cr, uid, {
                'code': SaleId,
                'product': product_id,
                'sale_date': SaleDate,
                'qty': SaleQty,
                'normal_price': NormalPrice,
                'amount': amount,
                'company_id': company_id,
                'sale_man': employee_id,
                'sale_type': SaleType,
                'PosNo': PosNo,
                'profit': profit,
            })

        sub_sql = """
            SELECT spa.SaleId,spa.PaymodeId,DATEADD(hour,-8,spa.SaleDate) as SaleDate,spa.PayMoney,spa.BraId 
            FROM sale_paymode_all spa 
             WHERE convert(VARCHAR(10),spa.SaleDate,126) = '{0}'
        """
        sub_sql = sub_sql.format(date)
        pos_order_pay_list = ms.ExecQuery(sub_sql.encode('utf-8'))
        for (SaleId, PaymodeId, SaleDate, PayMoney, BraId) in pos_order_pay_list:
            company_id = self.pool.get('res.company').search_bycode(cr, uid, BraId)
            self.pool.get('sy.pos.payment').create(cr, uid, {
                'code': SaleId,
                'date': SaleDate,
                'paymodel': PaymodeId,
                'paymoney': PayMoney,
                'company_id': company_id,
            })
        return

    def auto_update(self, cr, uid, ids, context=None):
        # 导入前一天销售数据
#        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.sync_product_class(cr, uid, ids, context=None)
        self.sync_product_brand(cr, uid, ids, context=None)
        self.sync_employee(cr, uid, ids, context=None)
        self.sync_supplier(cr, uid, ids, context=None)
        self.sync_product(cr, uid, ids, context=None)
        self.set_product_category_parent(cr, uid, ids, context=None)
        self.sync_pos(cr, uid, ids, context=None)

        return True

    # 检查历史pos单是否一致
    def check_pos_data_daily(self, cr, uid, ids, para_interval,context=None):
            vals = []
            end_date = datetime.datetime.now()
            for i in range(1, para_interval + 1):
                servercnt = 0
                localcnt = 0
                day = end_date - datetime.timedelta(days=i)
                print day
                exec_sql = """
                             select count(*) from 
                             (
                                 select company_id,code,count(*) 
                                 from sy_pos_order 
                           		 where to_char(sale_date,'yyyy-mm-dd')='{0}' 
 	                             group by company_id,code ) a                       
 	                              """
                exec_sql = exec_sql.format(day.strftime('%Y-%m-%d'))
                cr = self.pool.cursor()
                cr.execute(exec_sql)

                remote_exec_sql = """ 
                        select count(*)  from (
                        SELECT  bs.BraId,bs.saleid,bs.memb_id ,salerid,saleflag,min(DATEADD(hour,-8,bs.SaleDate)) as saledate 
                                    FROM v_bn_saledetail  bs
                                    where datediff(day,saledate,'{0}')=0 
                                    group by  bs.BraId,bs.saleid,bs.memb_id ,salerid,saleflag   
                                     ) a
                        """
                remote_exec_sql = remote_exec_sql.format(day)
                ms = Lz_read_SQLCa(self)
                remote_cnt = ms.ExecQuery(remote_exec_sql.encode('utf-8'))

                for rcnt in remote_cnt:
                    servercnt = remote_cnt[0]

                for local_count in cr.fetchall():
                    localcnt = local_count[0]

                # _logger.info(" shangyi =>jspot  check_pos_data_daily local using  %s  " % exec_sql)
                # _logger.info(" shangyi =>jspot  check_pos_data_daily remote using  %s  " % remote_exec_sql)
                vals.append({'proc_date': day.strftime('%Y-%m-%d'), 'local_records_count': localcnt,
                             'remote_records_count': servercnt[0]})

            return vals

    def query_period(self, local, remote):
        start_stamp = 0
        end_stamp = 0
        query_local = local
        query_remote = remote
        cr = self.pool.cursor()
        cr.execute(query_local)
        for local_max_num in cr.fetchall():
            start_stamp = local_max_num[0]
            if local_max_num[0] is None:
                start_stamp = 0
        return_start = start_stamp
        ms = Lz_read_SQLCa(self)
        remote_stamp = ms.ExecQuery(query_remote.encode('utf-8'))
        for end_stamp in remote_stamp:
            if remote_stamp[0] is None:
                end_stamp = 0
        return_end = end_stamp[0]

        res = {
            'start_stamp': return_start,
            'end_stamp': return_end,
        }
        return res
