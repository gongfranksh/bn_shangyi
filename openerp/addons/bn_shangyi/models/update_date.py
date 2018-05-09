# -*- coding: UTF-8 -*-
from BNmssql import Lz_read_SQLCa
from BNmssql import decimal_2

#更新单个对账单
def import_check_account_one(self,cr,uid,checkid):
    #删除已有对账单信息
    check_account_ids=self.pool.get('check.account').search(cr,uid,[('checkid','=',checkid)])
    for check_account_id in check_account_ids:
        self.pool.get('check.account').unlink(cr,uid,[check_account_id],context=None)
    #同步最新对账单信息
    ms = Lz_read_SQLCa(self)
    account_sql="""SELECT ca.checkid,ca.checkdate,ca.supid,isnull(ca.SaleMethod,0),s.CounterFlag,ca.checkamt,ca.receiptamt,
                        ca.returnamt,ca.rentamt,ca.disamt,ca.adjustamt,ca.saleamt,ca.SaleCostAmt,s.SettleMethod,s.PayMethod,
                        s.SettleDays,ca.begindate,ca.enddate,ca.Remark,ca.braid,ca.operatorid,spr.PurGroupId
                        FROM check_account ca
                        LEFT JOIN supplier s ON ca.supid=s.SupId
                        LEFT JOIN supplier_purgroup_rel spr ON spr.supid=s.SupId
                        where ca.checkid='%s'
                        ORDER BY ca.checkid"""%(checkid)
    check_account_record= ms.ExecQuery(account_sql.encode('utf-8'))
    if check_account_record:
        self.pool.get('check.account').create_byrecord(cr,uid,check_account_record)
    #联营销售明细
    saledetail_sql="""select checkid,Braid,SaleDate,Proid,SaleQty,SaleAmt,ReturnRat,Supid,flag
                        FROM counter_check_saledetail
                        WHERE checkid= '%s'
                        ORDER BY Proid,SaleDate"""%(checkid)
    counter_check_saledetail_record= ms.ExecQuery(saledetail_sql.encode('utf-8'))
    self.pool.get('counter.check.saledetail').create_byrecord(cr,uid,counter_check_saledetail_record)
    #寄售明细
    saledetail_sql="""SELECT checkid,supid,inputdate,proid,intax,BraId,receiptid,receiptdate,ReceiptQty,ReturnQty,ReceiptPrice,
                            CheckQty,CheckAmt,NocheckQty,NocheckAmt,OperatorId,isnull(sourceflag,9),status
                        FROM payable_dx pd
                        WHERE checkid= '%s'
                        ORDER BY pd.proid,pd.receiptid"""%(checkid)
    payable_dx_record= ms.ExecQuery(saledetail_sql.encode('utf-8'))
    self.pool.get('payable.dx').create_byrecord(cr,uid,payable_dx_record)
    #买断验收单
    payable_head_sql="""SELECT checkid,OrderId,DmId,Ordertype,ReceiptId,ReceiptDate,SupId,AccountDate,PayDate,
                                isnull(OrderAmt,0),isnull(OrderTax,0),invoiceamt,payAmt,standard,Status,
                                checkflag,braid,isnull(needinvoice,0)
                        FROM payable_head
                        WHERE checkid= '%s'
                        ORDER BY OrderId"""%(checkid)
    payable_head_record= ms.ExecQuery(payable_head_sql.encode('utf-8'))
    self.pool.get('payable.head').create_byrecord(cr,uid,payable_head_record)
    #合同扣款明细
    deduct_fund_sql="""SELECT checkid,fundtype,cast(ContactId as nvarchar(100)),cast(content as nvarchar(100)) as content,yearmon,braid,amount,
                                tax,paymode,status,billflag,operatorid,supid 
                        FROM deduct_fund
                        WHERE checkid= '%s'"""%(checkid)
    deduct_fund_record= ms.ExecQuery(deduct_fund_sql.encode('utf-8'))
    self.pool.get('deduct.fund').create_byrecord(cr,uid,deduct_fund_record)
    return