# -*- coding: utf-8 -*-
from datetime import datetime

from openerp.osv import fields, osv
from BNmssql import Lz_read_SQLCa, Lz_write_SQLCa
from update_date import import_check_account_one

# 扣款修改
class deduct_fund_change(osv.osv):
    _name = 'deduct.fund.change'
    _inherit = ['mail.thread']
    # 计算对账单金额
    def _get_price(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x, 0), ids))
        for record in self.browse(cr, uid, ids, context):
            price = 0.00
            detail_ids = record.detail_ids
            for detail_id in detail_ids:
                if detail_id.operate == '0':
                    price = price + detail_id.sum
                if detail_id.operate == '1':
                    price = price + detail_id.sum
                if detail_id.operate == '3':
                    price = price + detail_id.c_sum
            res[record.id] = price
        return res

    _columns = {
        'code': fields.char(u'变更单号', readonly=True, ),
        'checkid': fields.char(u'对账单号'),
        'contactid': fields.char(u'合同号'),
        'detail_ids': fields.one2many('defuct.fund.detail', 'change_id', string=u'扣款明细'),
        'state': fields.selection([('0', u'初始'), ('1', u'已修改'), ('2', u'已审核')], u'状态'),
        'company_id': fields.many2one('res.company', u'门店',readonly=True),
        'create_uid': fields.many2one('res.users', string=u'创建人', readonly=True),
        'create_date': fields.datetime(string=u'创建时间', readonly=True),
        'supplier': fields.many2one('res.partner', u'供应商', domain=[('supplier', '=', True)],required=True),
        'peiod_id': fields.many2one('account.period', u'支付年月', domain="[('company_id','=',company_id),('state','=','draft'),('special','=',False)]",required=True),
        'lngyear': fields.char(u'支付年月'),
        'operate_id': fields.many2one('res.users', u'审核人', readonly=True),
        'operate_date': fields.datetime(u'审核时间', readonly=True),
        'price': fields.function(_get_price, string=u'扣款金额', type='float'),
        'note': fields.text(u'备注'),
    }
    _rec_name = 'code'
    _order = 'peiod_id desc,code desc'
    _defaults = {
        'state': '0',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid,'defuct.fund.change',context=c),
        'peiod_id':lambda self,cr,uid,c:self.pool.get('account.period').search(cr,uid,[('company_id','=',self.pool.get('res.company')._company_default_get(cr, uid,'defuct.fund.change',context=c)),
                                                                                       ('state','=','draft'),('special','=',False)],order='date_start')[0]
    }

    # 创建时若有未抛转的对账单，报错
    def create(self, cr, uid, vals, context=None):
        if 'checkid' in vals.keys():
            orther_ids = self.pool.get('deduct.fund.change').search(cr, uid, [('checkid', '=', vals['checkid']),
                                                                              ('state', '!=', '2')])
            if orther_ids:
                raise osv.except_osv((u'错误'), (u'该对账单存在未抛转的变更单！！请先抛转！！'))
        vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'deduct.fund.change') or '/'
        return super(deduct_fund_change, self).create(cr, uid, vals, context=context)

    # 若修改明细状态，则修改单子状态
    def write(self, cr, uid, ids, vals, context=None):
        if 'detail_ids' in vals.keys():
            detail_ids = vals['detail_ids']
            detail_ids = self.resolve_2many_commands(cr, uid, 'detail_ids', detail_ids, ['operate', 'c_sum'], context)
            line_id = 0
            for line in detail_ids:
                c_sum = line.get('c_sum')
                if c_sum:
                    c_amount = c_sum / 1.17
                    c_tax = c_sum - c_amount
                    if c_amount and type(c_amount) == float:
                        if vals['detail_ids'][line_id][2]:
                            vals['detail_ids'][line_id][2]['c_amount'] = c_amount
                    if c_tax and type(c_tax) == float:
                        if vals['detail_ids'][line_id][2]:
                            vals['detail_ids'][line_id][2]['c_tax'] = c_tax
                line_id = line_id + 1
            vals['state'] = '1'
        return super(deduct_fund_change, self).write(cr, uid, ids, vals, context=context)

    # 不能删除已抛转状态下的记录
    def unlink(self, cr, uid, ids, context=None):
        change = self.browse(cr, uid, ids[0])
        if change.state == '2':
            raise osv.except_osv((u'错误'), (u'已抛转的记录不能删除！！'))
        return super(deduct_fund_change, self).unlink(cr, uid, ids, context=context)

    # 输入门店、供应商、账期，产生对账单
    def onchange_checkid(self, cr, uid, ids, company_id, supplier, lngyear, context=None):
        if company_id and supplier and lngyear:
            company = self.pool.get('res.company').browse(cr, uid, company_id)
            if company:
                company_code = company.code
            supplier = self.pool.get('res.partner').browse(cr, uid, supplier)
            if supplier:
                supplier_code = supplier.code
            if company_code and supplier_code and lngyear:
                checkid = supplier_code + lngyear + company_code
                orther_ids = self.pool.get('deduct.fund.change').search(cr, uid, [('checkid', '=', checkid),
                                                                                  ('state', '!=', '2')])
                if orther_ids:
                    raise osv.except_osv((u'错误'), (u'该对账单存在未抛转的变更单！！请先抛转！！'))
                return {'value': {'checkid': checkid}}
        return

    #选择账期带出lngyear
    def onchange_period(self, cr, uid, ids, period_id, context=None):
        if period_id:
            period=self.pool.get('account.period').browse(cr,uid,period_id)
            period_code=period.name
            lngyear=period_code[3:7]+period_code[0:2]
            return {'value':{'lngyear':lngyear}}
        return
    
    # 读取明细
    def load_detail(self, cr, uid, ids, context=None):
        ms = Lz_read_SQLCa(self)
        change = self.browse(cr, uid, ids[0])
        code = change.checkid
        braid = change.company_id.code
        # 查找对账单是否存在
        check_sql = "SELECT supid,checkid FROM check_account WHERE checkid='%s' AND braid='%s'" % (code, braid)
        check_record = ms.ExecQuery(check_sql.encode('utf-8'))
        if len(check_record) == 0:
            raise osv.except_osv((u'错误'), (u'该门店没有该对账单！！'))
        for (supid, checkid) in check_record:
            s_id = self.pool.get('res.partner').search_bycode(cr,uid,supid)
            if checkid:
                lngyear = checkid[8:14]
            else:
                lngyear = False
        # 查找合同号
        contact_sql = "select top 1 contactid from sup_sponse_year where supid='%s'" % (code[0:8])
        contact_record = ms.ExecQuery(contact_sql.encode('utf-8'))
        if len(contact_record):
            for (contactid) in contact_record:
                if contactid:
                    contact_code = contactid[0]
        else:
            get_contact_max_sql = "select top 1 cast(SUBSTRING(contactid,3,9) AS INT) from sup_sponse_year ORDER BY UpdateDate DESC"
            contact_max_record = ms.ExecQuery(get_contact_max_sql.encode('utf-8'))
            for (contactid) in contact_max_record:
                contact_max_code = int(contactid[0]) + 1
            contact_max_code = str(contact_max_code)
            contact_max_code = contact_max_code.zfill(10 - len(contact_max_code))
            contact_code = 'AC' + contact_max_code
            create_sql = """insert into sup_sponse_year(ContactId,SupId,YearNo,yeartype,taxtype,CreateDate,UpdateDate,OperatorId)
                VALUES
                ('%s','%s',Datename(year,GetDate()),'3','1',getdate(),getdate(),'odoo')
            """ % (contact_code, supid)
            ms_write=Lz_write_SQLCa(self)
            create_sql = ms_write.ExecNonQuery(create_sql.encode('utf-8'))
        detail_sql = """SELECT fundtype,cast(CONTENT as nvarchar(100)) as CONTENT,yearmon,braid,amount,tax,paymode,operatorid,supid
                        FROM deduct_fund 
                        where checkid='%s' and Braid='%s'""" % (code, braid)
        detail_record = ms.ExecQuery(detail_sql.encode('utf-8'))
        val = []
        for (fundtype, CONTENT, yearmon, braid, amount, tax, paymode, operatorid, supid) in detail_record:
            company_id = self.pool.get('res.company').search_bycode(cr,uid,braid)
            employee_id = self.pool.get('hr.employee').search_bycode(cr, uid, operatorid)
            sup_id = self.pool.get('res.partner').search_bycode(cr, uid, supid)
            item_id = self.pool.get('sup.sponse.items').search_bycode(cr, uid, CONTENT)
            val.append((0, 0, {
                'fundtype': fundtype,
                'content': CONTENT,
                'itemid': item_id,
                'contactid': contact_code,
                'lngyear': yearmon,
                'company_id': company_id,
                'amount': amount,
                'tax': tax,
                'sum': amount + tax,
                'paymode': paymode,
                'employee_id': employee_id,
                'supplier': sup_id,
                'operate': '0',
            }))
        #删除已有明细
        detail_ids=change.detail_ids
        for detail_id in detail_ids:
            self.pool.get('defuct.fund.detail').unlink(cr,uid,detail_id.id)
        self.pool.get('deduct.fund.change').write(cr, uid, ids[0], {
            'supplier': s_id,
            'lngyear': lngyear,
            'contactid': contact_code,
            'detail_ids': val})
        return

    # 增加扣款明细
    def add_detail(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        contactid=record.contactid
        if contactid==False:
            raise osv.except_osv((u'错误'), (u'该表单没有设置合同号！！请先点取读取明细按钮！！'))
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False,
            'company_id': record.company_id and record.company_id.id
        })
        return {
            'name': u'增加明细',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'defuct.fund.detail.add',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    # 扣款明细修改sql
    def get_detail_sql(self, detail, checkid, braid):
        operate = detail.operate
        detail_sql = ""
        # 删除操作
        if operate == '2':
            detail_sql = "delete from deduct_fund where checkid='" + checkid + "' and content='" + detail.content + "' and amount=" + str(
                detail.amount) + " and tax=" + str(detail.tax) + ";"
        # 修改操作
        if operate == '3':
            detail_sql = "update deduct_fund set amount=" + str(detail.c_amount) + ",tax=" + str(
                detail.c_tax) + " where checkid='" + checkid + "' and content='" + str(
                detail.content) + "' and amount=" + str(detail.amount) + " and tax=" + str(detail.tax) + ";"
        # 新增操作
        if operate == '1':
            detail_sql = """INSERT INTO deduct_fund(yearmon,supid,fundtype,ContactId,content,amount,tax,paymode,status,createdate,operatorid,billflag,checkid,braid)
                VALUES
                ('%s','%s','%s','%s','%s','%s','%s','3','0',getdate(),'odoo','0','%s','%s') ;
                """ % (
            detail.lngyear, detail.supplier.code, detail.fundtype, detail.contactid, detail.itemid.name, detail.amount,
            detail.tax, checkid, braid)
        return detail_sql

    # 主表平衡sql
    def get_ph_sql(self, checkid):
        balance_sql = "exec BN_Proc_check_account '{0}'".format(checkid)
        return balance_sql

    # 抛转商益,若对账单odoo已经导入，则更新这份对账单信息
    def return_shangyi(self, cr, uid, ids, context=None):
        change = self.browse(cr, uid, ids[0])
        checkid = change.checkid
        braid = change.company_id.code
        details = change.detail_ids
        lngyear = change.lngyear
        lngyear = lngyear[0:4] + '-' + lngyear[4:6] + '-01'
        resource_resource = self.pool.get('resource.resource').search(cr, uid, [('user_id', '=', uid)])
        hr_employee = self.pool.get('hr.employee').search(cr, uid, [('resource_id', '=', resource_resource[0])])
        hr_employee = self.pool.get('hr.employee').browse(cr, uid, hr_employee[0])
        employee_code = hr_employee.code[0:4]
        sql = ""
        ms = Lz_write_SQLCa(self)
        # 扣款调整单明细逐条拼接sql并执行
        for detail in details:
            sql = sql + self.get_detail_sql(detail, checkid, braid)
        ms.ExecNonQuery(sql.encode('utf-8'))
        # 增加行增加供应商费用管理
        add_sql = "DECLARE @num AS INT;DECLARE @numc AS CHAR(4);"
        for detail in details:
            if detail.operate == '1':
                add_sql = add_sql + """
                SELECT @num=max(CAST(flowid AS INT))+1 FROM sup_sponse_detail WHERE ContactId='%s';
                SELECT @numc=REPLICATE(0,4-LEN(cast(@num AS CHAR)))+cast(@num AS CHAR);
                INSERT INTO sup_sponse_detail(ContactId, flowid, SponseItemId, Amount, PayDate, PayMode, DeductType, STATUS, inputdate, OperatorId, Braid, ManagerId)
                VALUES
                ('%s', isnull(@numc,'0001'), '%s', '%s', cast(('%s') AS DATETIME), '%s', '1', '1', getdate(), 'odoo', '%s', '%s') ;
                """ % (
                detail.change_id.contactid, detail.change_id.contactid, detail.itemid.sponseitemid, detail.sum, lngyear,
                detail.paymode, braid, employee_code)
        ms.ExecNonQuery(add_sql.encode('utf-8'))
        # 对账单主表平衡
        if details:
            balance_sql = self.get_ph_sql(checkid)
            ms.ExecNonQuery(balance_sql.encode('utf-8'))
        # 同步odoo对账单信息
        check_account_ids=self.pool.get('check.account').search(cr,uid,[('checkid','=',checkid)])
        if check_account_ids and sql:
            import_check_account_one(self,cr,uid,checkid)
                
        #修改扣款调整单状态  
        self.write(cr, uid, ids[0], {'state': '2',
                                     'operate_id': uid,
                                     'operate_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                     })
        return


class defuct_fund_detail(osv.osv):
    _name = 'defuct.fund.detail'
    _columns = {
        'fundtype': fields.selection([('1', u'固定月扣'), ('2', u'配送月扣'), ('3', u'销售奖励'), ('4', u'赞助项')
                                      , ('5', u'其他扣款'),('6', u'账务扣款')],u'赞助款项'),
        'contactid': fields.char(u'合同号'),
        'itemid': fields.many2one('sup.sponse.items', u'赞助款项',),
        'content': fields.char(u'赞助款项内容'),
        'lngyear': fields.char(u'支付年月'),
        'company_id': fields.many2one('res.company', u'门店'),
        'amount': fields.float(u'无税金额'),
        'tax': fields.float(u'税额'),
        'sum': fields.float(u'价税合计', required=True),
        'paymode': fields.selection([('1', u'现金'), ('2', u'支票'), ('3', u'抵扣货款')], u'付款方式', required=True),
        'employee_id': fields.many2one('hr.employee', u'操作员'),
        'supplier': fields.many2one('res.partner', u'供应商'),
        'change_id': fields.many2one('deduct.fund.change', '变更单'),
        'operate': fields.selection([('0', u'无操作'), ('1', u'增加'), ('2', u'删除'), ('3', u'修改')], u'操作类型'),
        'c_amount': fields.float(u'无税金额(修改)'),
        'c_tax': fields.float(u'税额(修改)'),
        'c_sum': fields.float(u'价税合计(修改)'),
    }
    _defaults = {
        'operate': '1',
    }


class defuct_fund_detail_add(osv.osv_memory):
    _inherit = 'defuct.fund.detail'
    _name = 'defuct.fund.detail.add'
    _columns = {
                'itemid': fields.many2one('sup.sponse.items', u'赞助款项', required=True),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        active_id = context.get('active_id', False)
        company_id = context.get('company_id', False)
        change = self.pool.get('deduct.fund.change').browse(cr, uid, active_id)
        supplier = change.supplier.id
        lngyear = change.checkid[8:14]
        return {
            'change_id': active_id,
            'company_id': company_id,
            'operate': '1',
            'lngyear': lngyear,
            'supplier': supplier,
            'contactid': change.contactid,
            'paymode': '3',
        }
        return super(defuct_fund_detail_add, self).default_get(cr, uid, fields, context=context)

    def add_detail(self, cr, uid, ids, context=None):
        add = self.browse(cr, uid, ids[0])
        if add.itemid.fundtype==False:
            raise osv.except_osv((u'错误'), (u'该赞助款项未正确设置！！'))
        if add.contactid==False:
            raise osv.except_osv((u'错误'), (u'主表未读取合同号！！'))
        self.pool.get('defuct.fund.detail').create(cr, uid, {
            'fundtype': add.itemid.fundtype,
            'contactid': add.contactid,
            'itemid': add.itemid.id,
            'content': add.itemid.name,
            'lngyear': add.lngyear,
            'company_id': add.company_id and add.company_id.id or False,
            'amount': add.amount,
            'tax': add.tax,
            'sum': add.sum,
            'paymode': add.paymode,
            'employee_id': add.employee_id and add.employee_id.id or False,
            'supplier': add.supplier and add.supplier.id or False,
            'change_id': add.change_id.id,
            'operate': '1',
        })
        return

    def onchange_sum(self, cr, uid, ids, sum, context=None):
        amount = sum / 1.17
        tax = sum - amount
        return {'value': {'amount': amount,
                          'tax': tax,
                          }
                }


class sup_sponse_items(osv.osv):
    _name = 'sup.sponse.items'
    _columns = {
        'sponseitemid': fields.char('赞助项目编号'),
        'name': fields.char('项目名称'),
        'fundtype': fields.selection([('1', u'固定月扣'), ('2', u'配送月扣'), ('3', u'销售奖励'), ('4', u'赞助项'), ('5', u'其他扣款'),('6',u'账务调整')],
                                     u'赞助款项'),
    }

    def update_date(self, cr, uid, ids, context=None):
        sql = "SELECT SponseItemId,cast(SponseItemName as nvarchar(100)) FROM sup_sponse_items"
        ms = Lz_read_SQLCa(self)
        record = ms.ExecQuery(sql.encode('utf-8'))
        for (SponseItemId, SponseItemName) in record:
            item_ids = self.pool.get('sup.sponse.items').search(cr, uid, [('sponseitemid', '=', SponseItemId)])
            if item_ids:
                item = self.pool.get('sup.sponse.items').browse(cr, uid, item_ids[0])
                if item.name != SponseItemName:
                    self.pool.get('sup.sponse.items').write(cr, uid, item_ids[0], {'name': SponseItemName})
            else:
                self.pool.get('sup.sponse.items').create(cr, uid, {
                    'sponseitemid': SponseItemId,
                    'name': SponseItemName,
                })
        return
    
    def search_bycode(self,cr,uid,sponseitemid):
        items=self.pool.get('sup.sponse.items').search(cr,uid,[('sponseitemid','=',sponseitemid)])
        item_id=False
        if items:
            item_id=items[0]
        return item_id