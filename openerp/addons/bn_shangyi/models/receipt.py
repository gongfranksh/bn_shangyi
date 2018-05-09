# -*- coding: utf-8 -*-
from openerp import models, api, fields
from BNmssql import Lz_read_SQLCa, Lz_write_SQLCa


class receipt_head(models.Model):
    _name = 'receipt.head'

    receiptid = fields.Char(string=u'验收单号')
    receiptdate = fields.Datetime(string=u'验收日期')
    orderid = fields.Char(string=u'订单号')
    company = fields.Many2one('res.company', string=u'门店')
    sup = fields.Many2one('res.partner', string=u'供应商')
    operatorid = fields.Many2one('hr.employee', string=u'投单人')
    r_id = fields.Many2one('hr.employee', string=u'接收人')
    status = fields.Selection([
        ('0', u'未验收'),
        ('1', u'已验收'),
        ('pable_dx', u'寄售'),
    ], u'状态', )
    remark = fields.Text(u'备注')
    detail_ids = fields.One2many('receipt.detail', 'receiptid', string=u'商品明细')


class receipt_detail(models.Model):
    _name = 'receipt.detail'
    receiptid = fields.Many2one('receipt.head', string=u'验收单', ondelete='cascade')
    proid = fields.Many2one('product.template', string=u'商品')
    procode = fields.Char(string=u'商品编码', related='proid.code', )
    probar = fields.Char(string=u'商品条码', related='proid.barcode', )
    orderqty = fields.Integer(u'订单数量')
    orderprice = fields.Float(u'订单金额')
    gifqty = fields.Integer(u'实收搭赠数')
    receiptqty = fields.Integer(u'实收数量')
    receiptprice = fields.Float(u'实收金额')
    receipttax = fields.Float(u'税率')


# 导入对账销售成本差异表和验收单表
class import_check_list(models.TransientModel):
    _name = 'import.check.list'
    company = fields.Many2one('res.company', u'门店', required=True,default=lambda rec:rec._default_company())
    period = fields.Many2one('account.period', u'账期', domain="[('company_id','=',company),('state','=','draft'),('special','=',False)]",
                             default=lambda rec:rec._default_period(),required=True)
    start_date = fields.Date(u'开始日期', required=True)
    end_date = fields.Date(u'结束日期', required=True)

    @api.multi
    def _default_company(self):
        uid=self._uid
        company=self.env['res.users'].browse(uid).company_id.id
        return company
        
    @api.multi
    def _default_period(self):
        uid=self._uid
        company=self.env['res.users'].browse(uid).company_id.id
        period=self.env['account.period'].search([('company_id','=',company),('state','=','draft'),('special','=',False)],order='date_start')
        return period and period[0] or False
    
    @api.onchange('period')
    def _onchange_messages(self):
        period_id = self.period
        start_date = period_id.date_start
        end_date = period_id.date_stop
        self.start_date = start_date
        self.end_date = end_date

    @api.one
    def import_receipt_data(self):
        start_date = self.start_date
        end_date = self.end_date
        unlink_record = self.env['receipt.head'].search(
            [('receiptdate', '>=', start_date), ('receiptdate', '<=', end_date)])
        for unlink in unlink_record:
            self.env['receipt.head'].browse(unlink.id).unlink()

        ms = Lz_read_SQLCa(self)

        head_sql = """SELECT ReceiptId,ReceiptDate,OrderId,BraId,SupId,OperatorId,ReceiptMan,status,cast(Remark as nvarchar(100))
                FROM receipt_head
                where ReceiptDate between '%s' and '%s'""" % (start_date, end_date)
        head_record = ms.ExecQuery(head_sql.encode('utf-8'))
        for (ReceiptId, ReceiptDate, OrderId, BraId, SupId, OperatorId, ReceiptMan, status, Remark) in head_record:
            if BraId:
                BraId = self.env['res.company'].search([('code', '=', BraId)], limit=1)
                if BraId:
                    BraId = BraId.id
                else:
                    BraId = False
            else:
                BraId = False
            if SupId:
                SupId = self.env['res.partner'].search([('code', '=', SupId)], limit=1)
                if SupId:
                    SupId = SupId.id
                else:
                    SupId = False
            else:
                SupId = False
            if OperatorId:
                OperatorId = self.env['hr.employee'].search([('code', '=', OperatorId)], limit=1)
                if OperatorId:
                    OperatorId = OperatorId.id
                else:
                    OperatorId = False
            else:
                OperatorId = False
            if ReceiptMan:
                ReceiptMan = self.env['hr.employee'].search([('code', '=', ReceiptMan)], limit=1)
                if ReceiptMan:
                    ReceiptMan = ReceiptMan.id
                else:
                    ReceiptMan = False
            else:
                ReceiptMan = False
            self.env['receipt.head'].create({
                'receiptid': ReceiptId,
                'receiptdate': ReceiptDate,
                'orderid': OrderId,
                'company': BraId,
                'sup': SupId,
                'operatorid': OperatorId,
                'r_id': ReceiptMan,
                'status': status,
                'remark': Remark,
            })
        detail_sql = """SELECT rd.ReceiptId,rd.ProId,rd.OrderQty,rd.OrderPrice,rd.GifQty,rd.ReceiptQty,rd.ReceiptPrice,rd.ReceiptTax FROM receipt_detail rd
                    LEFT JOIN receipt_head rh ON rd.ReceiptId=rh.ReceiptId
                    WHERE rh.ReceiptDate BETWEEN '%s' AND '%s'""" % (start_date, end_date)
        detail_record = ms.ExecQuery(detail_sql.encode('utf-8'))
        for (ReceiptId, ProId, OrderQty, OrderPrice, GifQty, ReceiptQty, ReceiptPrice, ReceiptTax) in detail_record:
            if ReceiptId:
                ReceiptId = self.env['receipt.head'].search([('receiptid', '=', ReceiptId)], limit=1)
                if ReceiptId:
                    ReceiptId = ReceiptId.id
                else:
                    ReceiptId = False
            else:
                ReceiptId = False
            if ProId:
                ProId = self.env['product.template'].search([('code', '=', ProId)], limit=1)
                if ProId:
                    ProId = ProId.id
                else:
                    ProId = False
            else:
                ProId = False
            self.env['receipt.detail'].create({
                'receiptid': ReceiptId,
                'proid': ProId,
                'orderqty': OrderQty,
                'orderprice': OrderPrice,
                'gifqty': GifQty,
                'receiptqty': ReceiptQty,
                'receiptprice': ReceiptPrice,
                'receipttax': ReceiptTax,
            })
        # 寄售总部订单
        order_sql = """
            SELECT Inputdate,OrderId,BraId,SupId,OperatorId,ReceiptMan,cast(Remark as nvarchar(100)) FROM order_head
            where Inputdate between '%s' and '%s' and OrderMode not in ('0','1','2')
        """ % (start_date, end_date)
        order_record = ms.ExecQuery(order_sql.encode('utf-8'))
        for (Inputdate, OrderId, BraId, SupId, OperatorId, ReceiptMan, Remark) in order_record:
            if BraId:
                BraId = self.env['res.company'].search([('code', '=', BraId)], limit=1)
                if BraId:
                    BraId = BraId.id
                else:
                    BraId = False
            else:
                BraId = False
            if SupId:
                SupId = self.env['res.partner'].search([('code', '=', SupId)], limit=1)
                if SupId:
                    SupId = SupId.id
                else:
                    SupId = False
            else:
                SupId = False
            if OperatorId:
                OperatorId = self.env['hr.employee'].search([('code', '=', OperatorId)], limit=1)
                if OperatorId:
                    OperatorId = OperatorId.id
                else:
                    OperatorId = False
            else:
                OperatorId = False
            if ReceiptMan:
                ReceiptMan = self.env['hr.employee'].search([('code', '=', ReceiptMan)], limit=1)
                if ReceiptMan:
                    ReceiptMan = ReceiptMan.id
                else:
                    ReceiptMan = False
            else:
                ReceiptMan = False
            self.env['receipt.head'].create({
                'receiptid': OrderId,
                'receiptdate': Inputdate,
                'orderid': OrderId,
                'company': BraId,
                'sup': SupId,
                'operatorid': OperatorId,
                'r_id': ReceiptMan,
                'status': 'pable_dx',
                'remark': Remark,
            })
        order_detail_sql = """
            SELECT od.OrderID,od.ProId,od.OrderQty,od.OrderPrice,od.GifQty,od.ReceiptQty,od.ReceiptPrice,od.ReceiptTax FROM order_detail od
                LEFT JOIN order_head oh ON od.OrderID=oh.OrderID
                where oh.Inputdate between '%s' and '%s' and 
                oh.OrderMode not in ('0','1','2')
        """ % (start_date, end_date)
        order_detail_record = ms.ExecQuery(order_detail_sql.encode('utf-8'))
        for (OrderID, ProId, OrderQty, OrderPrice, GifQty, ReceiptQty, ReceiptPrice, ReceiptTax) in order_detail_record:
            if OrderID:
                ReceiptId = self.env['receipt.head'].search([('receiptid', '=', OrderID)], limit=1)
                if ReceiptId:
                    ReceiptId = ReceiptId.id
                else:
                    ReceiptId = False
            else:
                ReceiptId = False
            if ProId:
                ProId = self.env['product.template'].search([('code', '=', ProId)], limit=1)
                if ProId:
                    ProId = ProId.id
                else:
                    ProId = False
            else:
                ProId = False
            self.env['receipt.detail'].create({
                'receiptid': ReceiptId,
                'proid': ProId,
                'orderqty': OrderQty,
                'orderprice': OrderPrice,
                'gifqty': GifQty,
                'receiptqty': ReceiptQty,
                'receiptprice': ReceiptPrice,
                'receipttax': ReceiptTax,
            })

    @api.one
    def import_check_list_product(self):
        start_date = self.start_date
        end_date = self.end_date
        period_code = self.period.code
        unlink_record = self.env['check.list.product'].search([('date', '>=', start_date), ('date', '<=', end_date)])
        for unlink in unlink_record:
            self.env['check.list.product'].browse(unlink.id).unlink()
        ms = Lz_write_SQLCa(self)
        year = period_code[3:7]
        month = period_code[0:2]
        pro_sql = "EXEC proc_bn_check_account_list '%s','%s';" % (year, month)
        ms.ExecNonQuery(pro_sql.encode('utf-8'))
        sql = """SELECT t.checkt,t.braid,t.supid,proid,checkid,checkdate,amount,receiptid,checkamt,checkqty,isnull(s.SaleMethod,0)
                    FROM tmp_bn_check_account_list_pro t
                    LEFT JOIN supplier s ON t.supid=s.SupId
                    where t.checkdate between '%s' AND '%s' """ % (start_date, end_date)
        record = ms.ExecQuery(sql.encode('utf-8'))
        for (checkt, braid, supid, proid, checkid, checkdate, amount, receiptid, checkamt, checkqty,SaleMethod) in record:
            if checkt:
                if checkt == 'sales':
                    checkt = '0'
                if checkt == 'payable_dx':
                    checkt = '1'
            else:
                checkt = False
            if braid:
                company_id = self.env['res.company'].search([('code', '=', braid)], limit=1)
                if company_id:
                    company_id = company_id.id
                else:
                    company_id = False
            else:
                company_id = False
            if supid:
                sup_id = self.env['res.partner'].search([('code', '=', supid)], limit=1)
                if sup_id:
                    sup_id = sup_id.id
                else:
                    sup_id = False
            else:
                sup_id = False
            if proid:
                proid = self.env['product.template'].search([('code', '=', proid)], limit=1)
                if proid:
                    proid = proid.id
                else:
                    proid = False
            else:
                proid = False
            self.env['check.list.product'].create({
                'checkt': checkt,
                'braid': company_id,
                'supid': sup_id,
                'proid': proid,
                'date': checkdate,
                'checkid': checkid,
                'amount': amount,
                'receiptid': receiptid,
                'cost': checkamt,
                'saleqty': checkqty,
                'type':SaleMethod,
            })
