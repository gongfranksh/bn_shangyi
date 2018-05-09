# -*- coding: utf-8 -*-
from openerp.osv import fields,osv
import csv
from BNmssql import Lz_read_SQLCa
from update_date import import_check_account_one
from BNmssql import decimal_2

#对账单主表
class check_account(osv.osv):
    _name='check.account'
    _inherit = ['mail.thread']
    _columns={
           'checkid':fields.char(u'对账号'),
           'date':fields.date(u'对账日期'),
           'supplier':fields.many2one('res.partner','供应商'),
           'code':fields.related('supplier','code',type='char',string=u'供应商编码'),
           'type':fields.selection([('1',u'买断'),('2','寄售'),('a','联营'),],u'经营方式'),
           'sup_type':fields.selection([('0',u'自营'),('1','联营'),],u'供应商类型'),
           'pay_amount':fields.float(u'应付金额'),
           'income_amount':fields.float(u'进货金额'),
           'return_amount':fields.float(u'退货金额/抽成金额'),
           'rent_amount':fields.float(u'租金'),
           'sub_amount':fields.float(u'扣款金额'),
           'adjust_amount':fields.float(u'调价金额'),
           'sale_amount':fields.float(u'销售金额'),
           'sale_cost':fields.float(u'货款金额'),
           'amount_type':fields.selection([('0',u'现结'),('1','日结'),('2','月结'),('3','代销结算'),],u'结算方式'),
           'pay_type':fields.selection([('0',u'现金'),('1','支票'),('2','转账'),('3','汇票'),('4','电汇'),
                                        ('5',u'银行承兑天'),('6',u'银行承兑30天'),('7',u'银行承兑45天'),('8',u'银行承兑60天'),('9',u'银行承兑90天'),('A',u'银行承兑120天'),('B',u'银行承兑150天'),],u'付款方式'),
           'days':fields.integer(u'结算天数'),
           'start_date':fields.date(u'开始日期'),
           'end_date':fields.date(u'结束日期'),
           'note':fields.text(u'备注'),
           'company_id':fields.many2one('res.company',u'店别'),
           'employee_id':fields.many2one('hr.employee',u'结算员'),
           'group_code':fields.many2one('purchase.group',u'采购组'),
           
           'saledetail':fields.one2many('counter.check.saledetail','check_id',string=u'销售明细',),
           'payable':fields.one2many('payable.dx','check_id',string=u'寄售明细',),
           'payable_head':fields.one2many('payable.head','checkid',string=u'验收单',),
           'prepay_head':fields.one2many('prepay.head','checkid',string=u'预付款',),
           'deduct_fund':fields.one2many('deduct.fund','checkid',string=u'扣款项目',),
           'state':fields.selection([('0',u'草稿'),('1',u'已确认')],u'状态'),
           }
    _rec_name='checkid'
    
    def import_excel(self,cr,uid,ids,context=None):
        check_ids=self.pool.get('check.account').search(cr,uid,[('checkid','like',self.browse(cr,uid,ids[0]).checkid[0:7]+'%')])
        for check_id in check_ids:
            check_account=self.pool.get('check.account').browse(cr,uid,check_id)
            saledetail=check_account.saledetail
            date=[]
            for record in saledetail:
                proid=int(record.product_id.code)
                barcode=int(record.product_id.barcode)
                name=record.product_id.name
                date.append((proid,barcode,name))
        csvfile = file(r'saledetail.csv', 'wb')
        writer = csv.writer(csvfile)
        writer.writerow([u'商品编码', u'商品条码',u'商品名称'])
        writer.writerows(date)
        csvfile.close()
        return
    
    #更新对账单
    def update(self,cr,uid,ids,context=None):
        check_account_record=self.browse(cr,uid,ids[0])
        checkid=check_account_record.checkid
        import_check_account_one(self,cr,uid,checkid)
        return True
    
    def create_byrecord(self,cr,uid,records):
        for (checkid,checkdate,supid,SaleMethod,CounterFlag,checkamt,receiptamt,returnamt,rentamt,disamt,adjustamt,saleamt,SaleCostAmt,SettleMethod,PayMethod,SettleDays,begindate,enddate,Remark,braid,operatorid,PurGroupId) in records:
            sup_id=self.pool.get('res.partner').search_bycode(cr,uid,supid)
            company_id=self.pool.get('res.company').search_bycode(cr,uid,braid)
            employee_id=self.pool.get('hr.employee').search_bycode(cr,uid,operatorid)
            group_id=self.pool.get('purchase.group').search_bycode(cr,uid,PurGroupId)
            val={
                 'checkid':checkid,
                 'date':checkdate,
                 'supplier':sup_id,
                 'type':SaleMethod,
                 'sup_type':CounterFlag,
                 'pay_amount':checkamt,
                 'income_amount':receiptamt,
                 'return_amount':returnamt,
                 'rent_amount':rentamt,
                 'sub_amount':disamt,
                 'adjust_amount':adjustamt,
                 'sale_amount':saleamt,
                 'sale_cost':SaleCostAmt,
                 'amount_type':SettleMethod,
                 'pay_type':PayMethod,
                 'days':SettleDays,
                 'start_date':begindate,
                 'end_date':enddate,
                 'note':Remark,
                 'company_id':company_id,
                 'employee_id':employee_id,
                 'group_code':group_id,
                 }
            self.pool.get('check.account').create(cr,uid,val)
        return
    
    def search_bycode(self,cr,uid,checkid):
        check_account=self.pool.get('check.account').search(cr,uid,[('checkid','=',checkid)])
        check_id=False
        if check_account:
            check_id=check_account[0]
        return check_id
    
#联营销售明细
class counter_check_saledetail(osv.osv):
    _name='counter.check.saledetail'
    _columns={
              'company_id':fields.many2one('res.company',u'门店'),
              'date':fields.date(u'销售日期'),
              'product_id':fields.many2one('product.template',u'商品'),
              'product_code':fields.related('product_id','code',type='char',string='商品编码'),
              'product_barcode':fields.related('product_id','barcode',type='char',string='商品条码'),
              'product_spec':fields.related('product_id','spec',type='char',string='规格型号'),
              'product_brand':fields.related('product_id','brand_id',type='many2one',relation='product.brand',string='品牌'),
              'qty':fields.integer(u'销售数量'),
              'saleamt':fields.float(u'销售金额'),
              'returnrat':fields.float(u'扣点'),
              'costamt':fields.float(u'货款金额'),
              'supplier':fields.many2one('res.partner',u'供应商'),
              'check_id':fields.many2one('check.account',u'对账单',ondelete='cascade',),
              'flag':fields.selection([('0','POS'),('1','WG')],u'销售方式'),
              }
    
    def create_byrecord(self,cr,uid,records):
        for (checkid,Braid,SaleDate,Proid,SaleQty,SaleAmt,ReturnRat,Supid,flag) in records:
            check_account=self.pool.get('check.account').search_bycode(cr,uid,checkid)
            company_id=self.pool.get('res.company').search_bycode(cr,uid,Braid)
            product_id=self.pool.get('product.template').search_bycode(cr,uid,Proid)
            sup_id=self.pool.get('res.partner').search_bycode(cr,uid,Supid)
            if SaleAmt and ReturnRat:
                    returnamt=decimal_2(SaleAmt*ReturnRat)
                    costamt=float(str(float(SaleAmt)-float(returnamt)))
            else:
                costamt=0
            val={
                    'company_id':company_id,
                    'date':SaleDate,
                    'product_id':product_id,
                    'qty':SaleQty,
                    'saleamt':SaleAmt,
                    'returnrat':ReturnRat,
                    'costamt':costamt,
                    'supplier':sup_id,
                    'check_id':check_account,
                    'flag':flag,
                 }
            self.pool.get('counter.check.saledetail').create(cr,uid,val)
        return

#寄售明细
class payable_dx(osv.osv):
    _name='payable.dx'
    _columns={
              'supplier':fields.many2one('res.partner','供应商'),
              'check_id':fields.many2one('check.account',u'对账单',ondelete='cascade',),
              'date':fields.datetime(u'销售日期'),
              'product_id':fields.many2one('product.template',u'商品'),
              'product_code':fields.related('product_id','code',type='char',string='商品编码'),
              'product_barcode':fields.related('product_id','barcode',type='char',string='商品条码'),
              'product_spec':fields.related('product_id','spec',type='char',string='规格型号'),
              'product_brand':fields.related('product_id','brand_id',type='many2one',relation='product.brand',string='品牌'),
              'intax':fields.float(u'税率'),
              'company_id':fields.many2one('res.company',u'门店'),
              'receiptid':fields.char(u'标志号'),
              'receipt_date':fields.datetime(u'验单时间'),
              'receipt_qty':fields.integer(u'销售数量'),
              'return_qty':fields.integer(u'未对数量'),
              'receipt_amt':fields.float(u'对账单价'),
              'check_qty':fields.integer(u'对账数量'),
              'check_amt':fields.float(u'货款小计'),
              'nocheck_qty':fields.integer(u'未对数量'),
              'nocheck_amt':fields.float(u'未对金额'),
              'employee_id':fields.many2one('hr.employee',u'操作员'),
#add 2018-4-10 add sourceflag
#              'sourceflag':fields.selection([('0',u'POS'),('1',u'领用'),('2',u'网购'),('3',u'上月遗留'),('9',u'')],u'来源'),
              'sourceflag':fields.selection([('0',u'POS'),('1',u'领用'),('2',u'网购'),('3',u'上月遗留'),('9',u''),('4',u'微信'),('5',u'团购'),('6',u'天猫'),('7',u'电子渠道'),('B',u'企客'),('C',u'门店团购'),('S',u'员购'),('T',u'淘宝'),('J',u'京东')],u'来源'),

              'status':fields.selection([('1','1')],u'状态'),
              }
    
    def create_byrecord(self,cr,uid,records):
        for (checkid,supid,inputdate,proid,intax,BraId,receiptid,receiptdate,ReceiptQty,ReturnQty,ReceiptPrice,CheckQty,
            CheckAmt,NocheckQty,NocheckAmt,OperatorId,sourceflag,status) in records:
            check_account=self.pool.get('check.account').search_bycode(cr,uid,checkid)
            sup_id=self.pool.get('res.partner').search_bycode(cr,uid,supid)
            product_id=self.pool.get('product.template').search_bycode(cr,uid,proid)
            company_id=self.pool.get('res.company').search_bycode(cr,uid,BraId)
            employee_id=self.pool.get('hr.employee').search_bycode(cr,uid,OperatorId)
            val={
                    'supplier':sup_id,
                    'check_id':check_account,
                    'date':inputdate,
                    'product_id':product_id,
                    'intax':intax,
                    'company_id':company_id,
                    'receiptid':receiptid,
                    'receipt_date':receiptdate,
                    'receipt_qty':ReceiptQty,
                    'return_qty':ReturnQty,
                    'receipt_amt':ReceiptPrice,
                    'check_qty':CheckQty,
                    'check_amt':CheckAmt,
                    'nocheck_qty':NocheckQty,
                    'nocheck_amt':NocheckAmt,
                    'employee_id':employee_id,
                    'sourceflag':sourceflag,
                    'status':status,
                 }
            #未知原因财务组 无法导，对于无法导的数据用admin导入
            try:
                self.pool.get('payable.dx').create(cr,uid,val)
            except:
                self.pool.get('payable.dx').create(cr,1,val)
        return
    
#买断验收单
class payable_head(osv.osv):
    _name='payable.head'
    _columns={
              'orderid':fields.char(u'订单号'),
              'dm':fields.char('DM'),
              'ordertype':fields.selection([('0','进货'),('1','退货'),('2','调整 '),('4','进货更正 '),('5','退货更正 '),],u'业务类型'),
              'receiptid':fields.char(u'验收单号'),
              'receiptdate':fields.datetime(u'验收日期'),
              'supplier':fields.many2one('res.partner','供应商'),
              'accountdate':fields.datetime(u'到账日期'),
              'paydate':fields.datetime('paydate'),
              'orderamt':fields.float(u'无税金额'),
              'ordertax':fields.float(u'税额'),
              'amout':fields.float(u'含税金额'),
              'invoiceamt':fields.float('invoiceamt'),
              'payamt':fields.float('payamt'),
              'stardard':fields.integer('stardard'),
              'status':fields.selection([('1','11'),('2','22'),('a','aa'),
                                         ('4','部分核销'),('5','已核销'),],u'status'),
              'checkflag':fields.selection([('0','00'),('1','11'),('2','22'),],u'checkflag'),
              'company_id':fields.many2one('res.company',u'门店'),
              'checkid':fields.many2one('check.account',u'对账单',ondelete='cascade'),
              'needinvoice':fields.selection([('0','否'),('1','是')],u'是否开票'),
              }
    
    def create_byrecord(self,cr,uid,records):
        for (checkid,OrderId,DmId,Ordertype,ReceiptId,ReceiptDate,SupId,AccountDate,PayDate,OrderAmt,OrderTax,invoiceamt,payAmt,standard,Status,checkflag,braid,needinvoice) in records:
            check_account=self.pool.get('check.account').search_bycode(cr,uid,checkid)
            sup_id=self.pool.get('res.partner').search_bycode(cr,uid,SupId)
            company_id=self.pool.get('res.company').search_bycode(cr,uid,braid)
            val={
                    'orderid':OrderId,
                    'dm':DmId,
                    'ordertype':Ordertype,
                    'receiptid':ReceiptId,
                    'receiptdate':ReceiptDate,
                    'supplier':sup_id,
                    'accountdate':AccountDate,
                    'paydate':PayDate,
                    'orderamt':OrderAmt,
                    'ordertax':OrderTax,
                    'amout':OrderAmt+OrderTax,
                    'invoiceamt':invoiceamt,
                    'payamt':payAmt,
                    'stardard':standard,
                    'status':Status,
                    'checkflag':checkflag,
                    'company_id':company_id,
                    'checkid':check_account,
                    'needinvoice':needinvoice,
                 }
            self.pool.get('payable.head').create(cr,uid,val)
        return
    
#合同扣款明细
class deduct_fund(osv.osv):
    _name='deduct.fund'
    _columns={
              'fundtype':fields.selection([('1',u'固定月扣'),('2',u'配送月扣'),('3',u'销售奖励'),('4',u'赞助项'),('5',u'其他扣款'),('6',u'账务扣款')],u'赞助款项'),
              'contactid':fields.char(u'合同号'),
              'content':fields.char(u'赞助款项'),
              'lngyear':fields.char(u'支付年月'),
              'company_id':fields.many2one('res.company',u'门店'),
              'amount':fields.float(u'无税金额'),
              'tax':fields.float(u'税额'),
              'sum':fields.float(u'价税合计'),
              'checkid':fields.many2one('check.account',u'对账单',ondelete='cascade'),
              'paymode':fields.selection([('1',u'现金'),('2',u'支票'),('3',u'抵扣货款')],u'付款方式'),
              'status':fields.selection([('0',u'00'),('1',u'11'),],u'转账标志'),
              'billflag':fields.selection([('0',u'未对账'),('1',u'已对账'),],u'对账标志'),
              'employee_id':fields.many2one('hr.employee',u'操作员'),
              'supplier':fields.many2one('res.partner',u'供应商'),
              }
    def create_byrecord(self,cr,uid,records):
        for (checkid,fundtype,ContactId,content,yearmon,braid,amount,tax,paymode,status,billflag,operatorid,supid) in records:
            check_account=self.pool.get('check.account').search_bycode(cr,uid,checkid)
            sup_id=self.pool.get('res.partner').search_bycode(cr,uid,supid)
            company_id=self.pool.get('res.company').search_bycode(cr,uid,braid)
            employee_id=self.pool.get('hr.employee').search_bycode(cr,uid,operatorid)
            val={
                    'fundtype':fundtype,
                    'contactid':ContactId,
                    'content':content,
                    'lngyear':yearmon,
                    'company_id':company_id,
                    'amount':amount,
                    'tax':tax,
                    'sum':amount+tax,
                    'checkid':check_account,
                    'paymode':paymode,
                    'status':status,
                    'billflag':billflag,
                    'employee_id':employee_id,
                    'supplier':sup_id,
                 }
            self.pool.get('deduct.fund').create(cr,uid,val)
        return
    
#其他扣款输入
class otherdetain(osv.osv):
    _name='otherdetain'
    _columns={
              'billid':fields.char(u'流水号'),
              'code':fields.char(u'扣款单号'),
              'supplier':fields.many2one('res.partner',u'供应商'),
              'amount':fields.float(u'无税金额'),
              'tax':fields.float(u'税率'),
              'amt_tax':fields.float(u'含税金额'),
              'remark':fields.char(u'扣款原因'),
              'paydate':fields.date(u'付款年月'),
              'paymode':fields.selection([('1',u'现金'),('2',u'支票'),('3',u'抵扣货款')],u'付款方式'),
              'status':fields.selection([('0',u'未转账'),('1',u'已转账'),],u'状态'),
              'employee_id':fields.many2one('hr.employee',u'操作员'),
              'company_id':fields.many2one('res.company',u'门店'),
              }
    
    def create_byrecord(self,cr,uid,records):
        for (billid,code,SupId,amount,tax,amt_tax,Remark,PayDate,PayMode,Status,OperatorId,Braid) in records:
            sup_id=self.pool.get('res.partner').search_bycode(cr,uid,SupId)
            company_id=self.pool.get('res.company').search_bycode(cr,uid,Braid)
            employee_id=self.pool.get('hr.employee').search_bycode(cr,uid,OperatorId)
            val={
                    'billid':billid,
                    'code':code,
                    'supplier':sup_id,
                    'amount':amount,
                    'tax':tax,
                    'amt_tax':amt_tax,
                    'remark':Remark,
                    'paydate':PayDate,
                    'paymode':PayMode,
                    'status':Status,
                    'employee_id':employee_id,
                    'company_id':company_id,
                 }
            self.pool.get('otherdetain').create(cr,uid,val)
            
#预付款
class prepay_head(osv.osv):
    _name='prepay.head'
    _columns={
              'prepayid':fields.char(u'预付款单号'),
              'orderid':fields.char(u'订单单号'),
              'supplier':fields.many2one('res.partner',u'供应商'),
              'orderamt':fields.float(u'订单金额'),
              'prepayamt':fields.float(u'预付款金额'),
              'lostamt':fields.float(u'lostamt'),
              'status':fields.selection([('0',u'0'),('1',u'1'),('9',u'9'),],u'状态'),
              'operatorid':fields.many2one('hr.employee',u'操作员'),
              'auditman1':fields.many2one('hr.employee',u'auditman1'),
              'auditman2':fields.many2one('hr.employee',u'auditman2'),
              'auditman3':fields.many2one('hr.employee',u'auditman3'),
              'payman':fields.many2one('hr.employee',u'payman'),
              'checkid':fields.many2one('check.account',u'对账单',ondelete='cascade'),
              'checkedprepayamt':fields.float(u'checkedprepayamt'),
              'uncheckprepayamt':fields.float(u'uncheckprepayamt'),
              'currencytype':fields.char('currencytype'),
              'createdate':fields.datetime(u'创建时间'),
              'updatedate':fields.datetime(u'更新时间'),
              'remark':fields.char(u'备注'),
              'braid':fields.many2one('res.company',u'门店'),
              'paymentid':fields.char('paymentid'),
              'checkedprepayamt1':fields.float(u'checkedprepayamt1'),
              'uncheckprepayamt1':fields.float(u'uncheckprepayamt1'),
              'status1':fields.selection([('0',u'0'),('1',u'1'),('9',u'9'),],u'status1'),
              'begindate':fields.date('begindate'),
              'enddate':fields.date('enddate'),
              'salecostamt':fields.float(u'salecostamt'),
              'saleamt':fields.float(u'saleamt'),
              }
    
#行销费用输入
class sup_sponse(osv.osv):
    _name='sup.sponse'
    _columns={
              'contractid':fields.char(u'合约号'),
              'supplier':fields.many2one('res.partner',u'供应商'),
              'year':fields.integer(u'年度'),
              'yeartype':fields.selection([('0',u'00'),('1',u'11'),('2','22'),('3','每月扣')],u'扣款时间'),
              'taxtype':fields.selection([('0',u'未转账'),('1',u'含税'),],u'金额标准'),
              'date':fields.date(u'创建时间'),
              'company_id':fields.many2one('res.company',u'门店'),
              }
    
class sup_sponse_detail(osv.osv):
    _name='sup.sponse.detail'
    _columns={
              'item_id':fields.char(u'项目编码'),
              'item_name':fields.char(u'缴款项目'),
              'sponse_id':fields.many2one('sup.sponse',u'行销费用'),
              'amount':fields.float(u'金额'),
              'paydate':fields.date(u'年月'),
              'paymode':fields.selection([('1',u'现金'),('2',u'支票'),('3',u'抵扣货款')],u'支付方式'),
              'deduct_type':fields.selection([('1',u'一次'),('2',u'每月')],u'计提方式'),
              'begindate':fields.date(u'开始时间'),
              'enddate':fields.date(u'结束时间'),
              'status':fields.selection([('0',u'待转'),('A',u'待审核'),],u'状态'),
              'inputdate':fields.datetime(u'录入时间'),
              'employee_id':fields.many2one('hr.employee',u'操作员'),
              'supplier':fields.many2one('res.partner',u'供应商'),
              'company_id':fields.many2one('res.company',u'门店'),
              }
    
class check_account_import(osv.osv_memory):
    _name='check.account.import'
    _columns={
              'account':fields.many2one('account.period',u'账期',domain="[('company_id','=',company_id),('state','=','draft'),('special','=',False)]",required=True),
              'company_id':fields.many2one('res.company',u'门店',required=True,readonly=True),
              }
    _defaults={
               'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'begin.check', context=c),
               'account':lambda self,cr,uid,c:self.pool.get('account.period').search(cr,uid,[('company_id','=',self.pool.get('res.company')._company_default_get(cr, uid,'defuct.fund.change',context=c)),
                                                                                       ('state','=','draft'),('special','=',False)],order='date_start')[0]
               }
    
    def import_account(self,cr,uid,ids,context=None):
        ms = Lz_read_SQLCa(self)
        imp=self.pool.get('check.account.import').browse(cr,uid,ids[0])
        account=imp.account
        braid=imp.company_id.code
        start=account.date_start
        end=account.date_stop+' 23:59:59'
        #删除本账期已经导入的对账单
        check_account=self.pool.get('check.account').search(cr,uid,[('company_id','=',imp.company_id.id),
                                                                    ('date','>=',imp.account.date_start),
                                                                    ('date','<=',imp.account.date_stop)])
        self.pool.get('check.account').unlink(cr,uid,check_account)
        #导入对账单
        account_sql="""SELECT ca.checkid,ca.checkdate,ca.supid,isnull(ca.SaleMethod,0),s.CounterFlag,ca.checkamt,ca.receiptamt,
                        ca.returnamt,ca.rentamt,ca.disamt,ca.adjustamt,ca.saleamt,ca.SaleCostAmt,
                        s.SettleMethod,s.PayMethod,s.SettleDays,
                        ca.begindate,ca.enddate,ca.Remark,ca.braid,ca.operatorid,spr.PurGroupId
                        FROM check_account ca 
                        LEFT JOIN supplier s ON ca.supid=s.SupId
                        LEFT JOIN supplier_purgroup_rel spr ON spr.supid=s.SupId
                        where checkdate between '%s' and '%s' and ca.braid='%s'
                        ORDER BY ca.checkid
                        """%(start,end,braid)
        check_account_record= ms.ExecQuery(account_sql.encode('utf-8'))
        self.pool.get('check.account').create_byrecord(cr,uid,check_account_record)
        #联营销售明细
        saledetail_sql="""select c.checkid,c.Braid,c.SaleDate,c.Proid,c.SaleQty,c.SaleAmt,c.ReturnRat,c.Supid,c.flag
                            FROM counter_check_saledetail c
                            LEFT JOIN check_account ca ON c.checkid=ca.checkid
                            WHERE ca.checkdate between '%s' and '%s' and ca.Braid='%s'
                            ORDER BY c.Proid,c.SaleDate
                            """%(start,end,braid)
        counter_check_saledetail_record= ms.ExecQuery(saledetail_sql.encode('utf-8'))
        self.pool.get('counter.check.saledetail').create_byrecord(cr,uid,counter_check_saledetail_record)
        #寄售明细
        saledetail_sql="""SELECT pd.checkid,pd.supid,pd.inputdate,pd.proid,pd.intax,pd.BraId,pd.receiptid,pd.receiptdate,
                                pd.ReceiptQty,pd.ReturnQty,pd.ReceiptPrice,pd.CheckQty,pd.CheckAmt,pd.NocheckQty,
                                pd.NocheckAmt,pd.OperatorId,isnull(pd.sourceflag,9),pd.status
                            FROM payable_dx pd
                            LEFT JOIN check_account ca ON pd.checkid=ca.checkid
                            WHERE ca.checkdate between '%s' and '%s' and ca.Braid='%s'
                            ORDER BY pd.proid,pd.receiptid
                            """%(start,end,braid)
        payable_dx_record= ms.ExecQuery(saledetail_sql.encode('utf-8'))
        self.pool.get('payable.dx').create_byrecord(cr,uid,payable_dx_record)
        #买断验收单
        payable_head_sql="""SELECT ph.checkid,ph.OrderId,ph.DmId,ph.Ordertype,ph.ReceiptId,ph.ReceiptDate,ph.SupId,ph.AccountDate,ph.PayDate,
                                    isnull(ph.OrderAmt,0),isnull(ph.OrderTax,0),ph.invoiceamt,ph.payAmt,ph.standard,ph.Status,
                                    ph.checkflag,ph.braid,isnull(ph.needinvoice,0)
                            FROM payable_head ph
                            LEFT JOIN check_account ca ON ph.checkid=ca.checkid
                            WHERE ca.checkdate between '%s' and '%s' and ca.Braid='%s'
                            ORDER BY ph.OrderId
                            """%(start,end,braid)
        payable_head_record= ms.ExecQuery(payable_head_sql.encode('utf-8'))
        self.pool.get('payable.head').create_byrecord(cr,uid,payable_head_record)
        #合同扣款明细
        deduct_fund_sql="""SELECT df.checkid,df.fundtype,df.ContactId,cast(df.content as nvarchar(100)) as content,df.yearmon,df.braid,df.amount,
                                    df.tax,df.paymode,df.status,df.billflag,df.operatorid,df.supid 
                            FROM deduct_fund df
                            LEFT JOIN check_account ca ON df.checkid=ca.checkid
                            WHERE ca.checkdate between '%s' and '%s' and ca.Braid='%s' """%(start,end,braid)
        deduct_fund_record= ms.ExecQuery(deduct_fund_sql.encode('utf-8'))
        self.pool.get('deduct.fund').create_byrecord(cr,uid,deduct_fund_record)      
        #其他扣款输入
        otherdetain_sql="SELECT billid,code,SupId,amount,tax,amt_tax,cast(Remark as nvarchar(100)) as Remark,PayDate,PayMode,Status,OperatorId,Braid FROM OtherDetain where InputDate between '%s' and '%s'"%(start,end)
        otherdetain_record= ms.ExecQuery(otherdetain_sql.encode('utf-8'))
        self.pool.get('otherdetain').create_byrecord(cr,uid,otherdetain_record)      
        return
    
    #导入行销费用
    def import_sponse(self,cr,uid,ids,context=None):
        ms = Lz_read_SQLCa(self)
        imp=self.pool.get('check.account.import').browse(cr,uid,ids[0])
        account=imp.account
        braid=imp.company_id.code
        start=account.date_start
        end=account.date_stop+' 23:59:59'
        sup_sponse_sql="SELECT ContactId,SupId,YearNo,yeartype,taxtype,CreateDate FROM sup_sponse_year where CreateDate between '%s' and '%s' and Braid='%s'"%(start,end,braid)
        sup_sponse_record= ms.ExecQuery(sup_sponse_sql.encode('utf-8'))
        for (ContactId,SupId,YearNo,yeartype,taxtype,CreateDate) in sup_sponse_record:
            sup_id=self.pool.get('res.partner').search_bycode(cr,uid,SupId)
            val={
                    'contractid':ContactId,
                    'supplier':sup_id,
                    'year':YearNo,
                    'yeartype':yeartype,
                    'taxtype':taxtype,
                    'date':CreateDate,
                 }
            self.pool.get('sup.sponse').create(cr,uid,val)
#        sup_sponse_detail_sql="SELECT ContactId,SupId,YearNo,yeartype,taxtype,CreateDate FROM sup_sponse_year where CreateDate between '%s' and '%s' and Braid='%s'"%(start,end,braid)
#        sup_sponse_detail_record= ms.ExecQuery(sup_sponse_detail_sql.encode('utf-8'))
#        for () in sup_sponse_detail_record:
#            val={
#                 }
#            self.pool.get('sup.sponse.detail').create(cr,uid,val)
        return
    
class purchase_group(osv.osv):
    _name='purchase.group'
    _columns={
              'purgroupid':fields.char(u'采购组ID'),
              'purname':fields.char(u'采购组名称'),
              }
    _rec_name='purname'
    
    def update_date(self, cr, uid, ids, context=None):
        sql = "SELECT PurGroupId,cast(PurName as nvarchar(100)) FROM purchase_group"
        ms = Lz_read_SQLCa(self)
        record = ms.ExecQuery(sql.encode('utf-8'))
        for (PurGroupId, PurName) in record:
            item_ids = self.pool.get('purchase.group').search(cr, uid, [('purgroupid', '=', PurGroupId)])
            if item_ids:
                item = self.pool.get('purchase.group').browse(cr, uid, item_ids[0])
                if item.purname != PurName:
                    self.pool.get('purchase.group').write(cr, uid, item_ids[0], {'purname': PurName})
            else:
                self.pool.get('purchase.group').create(cr, uid, {
                    'purgroupid': PurGroupId,
                    'purname': PurName,
                })
        return
    
    def search_bycode(self,cr,uid,code):
        purchase_group=self.pool.get('purchase.group').search(cr,uid,[('purgroupid','=',code)])
        group_id=False
        if purchase_group:
            group_id=purchase_group[0]
        return group_id