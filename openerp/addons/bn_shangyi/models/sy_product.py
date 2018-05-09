# -*- coding: utf-8 -*-
import datetime
import types
import webbrowser
from openerp.osv import fields, osv
from BNmssql import Lz_read_SQLCa

class sy_product(osv.osv):
    _name = 'sy.product'
    _columns = {
        'code': fields.char(u'编码', required=True),
        'name': fields.char(u'名称'),
        'date': fields.date(u'日期'),
        'text': fields.text(u'备注'),
    }
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code must be unique!'),
    ]

    def synch_product_data(self, cr, uid, ids, context=None):
        ms = Lz_read_SQLCa(self)
        # 导入产品类别
        product_class_list = ms.ExecQuery(
            "select ClassId,cast(ClassName as nvarchar(100)) as name from product_class".encode('utf-8'))
        for (ClassId, name,) in product_class_list:
            code = ClassId
            p_ids = self.pool.get('product.category').search_bycode(cr, uid, code)
            if p_ids:
                category = self.pool.get('product.category').browse(cr, uid, p_ids)
                old_name = category.name
                val={}
                if old_name != name:
                    val['name']=name
                if val:
                    self.pool.get('product.category').write(cr, uid, p_ids, val)
            else:
                self.pool.get('product.category').create(cr, uid, {
                    'code': ClassId,
                    'name': name,
                })
        # 导入品牌
        product_brand_list = ms.ExecQuery(
            "SELECT pb.BrandId,cast(pb.BrandName as nvarchar(100)) as name FROM product_brand pb".encode('utf-8'))
        for (BrandId, name,) in product_brand_list:
            brand_id = self.pool.get('product.brand').search_bycode(cr, uid, BrandId)
            if brand_id:
                brand = self.pool.get('product.brand').browse(cr, uid, brand_id)
                old_name = brand.name
                val={}
                if old_name != name:
                    val['name']=name
                if val:
                    self.pool.get('product.brand').write(cr, uid, brand_id, val)
            else:
                self.pool.get('product.brand').create(cr, uid, {
                    'code': BrandId,
                    'name': name,
                })
        # 导入供应商
        supplier_class_list = ms.ExecQuery(
            "select SupId,cast(SupName as nvarchar(100)) as name,cast(Addr as nvarchar(100)) as addr,Tel,Fax,Zip,Email  from supplier".encode(
                'utf-8'))
        for (SupId, name, addr, Tel, Fax, Zip, Email,) in supplier_class_list:
            code = SupId
            p_ids = self.pool.get('res.partner').search_bycode(cr, uid, code)
            if p_ids:
                partner = self.pool.get('res.partner').browse(cr, uid, p_ids)
                val={}
                if partner.name != name:
                    val['name']=name
                if partner.street != addr:
                    val['street']=addr
                if partner.phone != Tel:
                    val['phone']=Tel
                if partner.fax != Fax:
                    val['fax']=Fax
                if partner.zip != Zip:
                    val['zip']=Zip
                if partner.email != Email:
                    val['email']=Email
                if val:
#                    partner.write(val)
                    self.pool.get('res.partner').write(cr, uid, p_ids, val)
            else:
                self.pool.get('res.partner').create(cr, uid, {
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
                })

        # 导入产品
        product_list = ms.ExecQuery(
            "select ProId,Barcode,cast(ProName as nvarchar(100)) as name,cast(spec as nvarchar(100)) as spec,ClassId,SupId,isnull(NormalPrice,0),BrandId from product".encode('utf-8'))
        for (ProId, Barcode, name, spec, ClassId, SupId, NormalPrice, BrandId,) in product_list:
            code = ProId
            p_id = self.pool.get('product.template').search_bycode(cr,uid,ProId)
            categ_id = self.pool.get('product.category').search_bycode(cr,uid,ClassId)
            m_categ_id = self.pool.get('product.category').search_bycode(cr,uid,ClassId[0:6])
            b_categ_id = self.pool.get('product.category').search_bycode(cr,uid,ClassId[0:4])
            sup_id = self.pool.get('res.partner').search_bycode(cr,uid,SupId)
            brand_id = self.pool.get('product.brand').search_bycode(cr,uid,BrandId)
            if p_id:
                product = self.pool.get('product.template').browse(cr, uid, p_id)
                val={}
                if product.name != name:
                    val['name']=name
                if product.barcode != Barcode:
                    val['barcode']=Barcode
                if product.categ_id.id != categ_id:
                    val['categ_id']=categ_id
                if product.b_category.id != b_categ_id:
                    val['b_category']=b_categ_id
                if product.m_category.id != m_categ_id:
                    val['m_category']=m_categ_id
                if product.list_price != float(NormalPrice):
                    val['list_price']=NormalPrice
                if product.brand_id.id != brand_id:
                    val['brand_id']=brand_id
                if product.spec != spec:
                    val['spec']=spec
                if val:
                    self.pool.get('product.template').write(cr,uid,p_id,val)
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
                product_tmpl_id = self.pool.get('product.template').create(cr, uid, {
                    'code': ProId,
                    'barcode': Barcode,
                    'name': name,
                    'spec':spec,
                    'list_price': NormalPrice,
                    'sale_ok': True,
                    'type': 'product',
                    'active': True,
                    'categ_id': categ_id,
                    'm_category': m_categ_id,
                    'b_category': b_categ_id,
                    'brand_id': brand_id,
                    'company_id': False,
                })
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

    def synch_pos_order(self, cr, uid, ids, sy_product_date, context=None):
        if type(sy_product_date) is types.DictType:
            if self.browse(cr, uid, ids[0]) and self.browse(cr, uid, ids[0]).date:
                date = self.browse(cr, uid, ids[0]).date
            else:
                date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date = sy_product_date
        ms = Lz_read_SQLCa(self)
        # 导入员工
        employee_list = ms.ExecQuery(
            "SELECT be.BraId,be.EmpId,cast(be.EmpName as nvarchar(100)) as name FROM branch_employee be".encode(
                'utf-8'))
        for (BraId, EmpId, name) in employee_list:
            e_id = self.pool.get('hr.employee').search_bycode(cr,uid,EmpId)
            company_id = self.pool.get('res.company').search_bycode(cr,uid,BraId)
            if e_id:
                hr_employee = self.pool.get('hr.employee').browse(cr, uid, e_id)
                val={}
                if hr_employee.company_id and hr_employee.company_id.id != company_id:
                    val['company_id']=company_id
                if hr_employee.company_id==False and company_id:
                    val['company_id']=company_id
                if hr_employee.name != name:
                    val['name']=name
                if val:
                    self.pool.get('resource.resource').write(cr, uid, hr_employee.resource_id.id, val)
            else:
                self.pool.get('hr.employee').create(cr, uid, {
                    'code': EmpId,
                    'name': name,
                })
        # 删除当天数据
        del_ids = self.pool.get('sy.pos.order').search(cr, uid, [('sale_date', 'like', date + '%')])
        for del_id in del_ids:
            self.pool.get('sy.pos.order').unlink(cr, uid, del_id)
        del_ids = self.pool.get('sy.pos.payment').search(cr, uid, [('date', 'like', date + '%')])
        for del_id in del_ids:
            self.pool.get('sy.pos.payment').unlink(cr, uid, del_id)
        # 导入当天pos订单和pos支付
        pos_order_list = ms.ExecQuery(
            "SELECT bs.BraId,DATEADD(hour,-8,bs.SaleDate) AS SaleDate,bs.proid,bs.SaleQty,bs.NormalPrice,bs.amount,bs.SaleId,bs.SaleMan,bs.SaleType,bs.PosNo,bs.profit FROM v_bn_saledetail bs WHERE convert(VARCHAR(10),bs.SaleDate,126) = '%s'" % (
                date).encode('utf-8'))
        for (BraId, SaleDate, proid, SaleQty, NormalPrice, amount, SaleId, SaleMan, SaleType, PosNo,profit) in pos_order_list:
            product_id = self.pool.get('product.template').search_bycode(cr,uid,proid)
            company_id = self.pool.get('res.company').search_bycode(cr,uid,BraId)
            employee_id = self.pool.get('hr.employee').search_bycode(cr,uid,SaleMan)
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
        pos_order_pay_list = ms.ExecQuery(
            "SELECT spa.SaleId,spa.PaymodeId,DATEADD(hour,-8,spa.SaleDate) as SaleDate,spa.PayMoney,spa.BraId FROM sale_paymode_all spa WHERE convert(VARCHAR(10),spa.SaleDate,126) = '%s'" % (
                date).encode('utf-8'))
        for (SaleId, PaymodeId, SaleDate, PayMoney,BraId) in pos_order_pay_list:
            company_id = self.pool.get('res.company').search_bycode(cr,uid,BraId)
            self.pool.get('sy.pos.payment').create(cr, uid, {
                'code': SaleId,
                'date': SaleDate,
                'paymodel': PaymodeId,
                'paymoney': PayMoney,
                'company_id':company_id,
            })
        return

    def auto_update(self, cr, uid, ids, context=None):
        # 导入前一天销售数据
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.synch_product_data(cr, uid, ids, context=None)
        self.synch_product_category_parent(cr, uid, ids, context=None)
        self.synch_pos_order(cr, uid, ids, date, context=None)
        # 检查前5天的销售数据是否正确
        day = 5
        start_date = (datetime.datetime.now() - datetime.timedelta(days=1 + day)).strftime("%Y-%m-%d")
        end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        check_sql = """
            SELECT braid,date,SUM(amount),SUM(profit)
            FROM v_bn_saledetail
            WHERE saledate BETWEEN '%s' AND '%s'
            GROUP BY braid,date
        """ % (start_date, end_date)

        ms = Lz_read_SQLCa(self)

        record = ms.ExecQuery(check_sql.encode('utf-8'))
        for (braid, date, amount, profit) in record:
            company_id = self.pool.get('res.company').search_bycode(cr,uid,braid)
            s_date = date + " 00:00:00"
            e_date = date + " 23:59:59"
            pos_order_ids = self.pool.get('sy.pos.order').search(cr, uid, [('company_id', '=', company_id),
                                                                           ('sale_date', '>=', s_date),
                                                                           ('sale_date', '<=', e_date)])
            sum_amount = 0
            sum_profit = 0
            for pos_id in pos_order_ids:
                pos_order = self.pool.get('sy.pos.order').browse(cr, uid, pos_id)
                sum_amount = sum_amount + pos_order.amount
                sum_profit = sum_profit + pos_order.profit
            if int(amount) != int(sum_amount) or int(profit) != int(sum_profit):
                self.synch_pos_order(cr, uid, ids, date, context=None)
        return True

    # 检查历史pos单是否一致
    def check_pos_order(self, cr, uid, ids, context=None):
        check_sql = """
                SELECT braid,date,SUM(amount),SUM(profit)
                FROM v_bn_saledetail
                WHERE date IS NOT NULL
                GROUP BY braid,date
                ORDER BY date
        """

        ms = Lz_read_SQLCa(self)
        record = ms.ExecQuery(check_sql.encode('utf-8'))
        for (braid, date, amount, profit) in record:
            company_id = self.pool.get('res.company').search_bycode(cr,uid,braid)
            s_date = date + " 00:00:00"
            e_date = date + " 23:59:59"
            pos_order_ids = self.pool.get('sy.pos.order').search(cr, uid, [('company_id', '=', company_id),
                                                                           ('sale_date', '>=', s_date),
                                                                           ('sale_date', '<=', e_date)])
            sum_amount = 0
            sum_profit = 0
            for pos_id in pos_order_ids:
                pos_order = self.pool.get('sy.pos.order').browse(cr, uid, pos_id)
                sum_amount = sum_amount + pos_order.amount
                sum_profit = sum_profit + pos_order.profit
            if int(amount) != int(sum_amount) or int(profit) != int(sum_profit):
                self.synch_pos_order(cr, uid, ids, date, context=None)
        return