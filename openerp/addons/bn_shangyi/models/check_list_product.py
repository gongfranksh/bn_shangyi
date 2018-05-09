# -*- coding: utf-8 -*-
import calendar
import datetime
from openerp import tools
from openerp.osv import fields, osv
from BNmssql import Lz_read_SQLCa

class check_list_product(osv.osv):
    _name = 'check.list.product'
    _columns = {
        'checkt': fields.selection([('0', '销售'), ('1', '对账')], u'类型'),
        'braid': fields.many2one('res.company', u'门店'),
        'supid': fields.many2one('res.partner', u'供应商'),
        'type':fields.selection([('1',u'买断'),('2','寄售'),('0','联营'),],u'经营方式'),
        'supcode': fields.related('supid', 'code', type='char', string=u'供应商编码'),
        'proid': fields.many2one('product.template', u'商品'),
        'procode': fields.related('proid', 'code', type='char', string=u'商品编码'),
        'probar': fields.related('proid', 'barcode', type='char', string=u'商品条码'),
        'date': fields.date(u'对账日期'),
        'checkid': fields.char(u'对账单号'),
        'amount': fields.float(u'金额'),
        'receiptid': fields.char(u'进货单号'),
        'cost': fields.float(u'成本'),
        'saleqty': fields.integer(u'数量'),
    }

    def view_receipt(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0], context=context)
        receiptid = record.receiptid
        if receiptid:
            return {
                'name': ('验收单明细'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'receipt.head',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('receiptid', '=', receiptid)],
            }
        else:
            company_id = record.braid.id
            date = record.date
            proid = record.proid.id
            period_ids = self.pool.get('account.period').search(cr, uid, [('company_id', '=', company_id),
                                                                          ('date_start', '<=', date),
                                                                          ('date_stop', '>=', date)])
            if period_ids:
                period = self.pool.get('account.period').browse(cr, uid, period_ids[0])
                date_start = period.date_start
                date_stop = period.date_stop
                return {
                    'name': ('POS明细'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'sy.pos.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'domain': [('sale_date', '>=', date_start), ('sale_date', '<=', date_stop),
                               ('company_id', '=', company_id), ('product', '=', proid)],
                }
            else:
                raise osv.except_osv((u'错误'), (u'该门店的账期设置不正确！！'))


class check_list_product_report(osv.osv):
    _name = 'check.list.product.report'
    _auto = False
    _columns = {
        'braid': fields.many2one('res.company', u'门店'),
        'supid': fields.many2one('res.partner', u'供应商'),
        'sup_code': fields.char(u'供应商编码'),
        'type':fields.selection([('1',u'买断'),('2','寄售'),('0','联营'),],u'经营方式'),
        'proid': fields.many2one('product.template', u'商品'),
        'pro_code': fields.char(u'商品编码'),
        'p_qty': fields.integer(u'对账数量'),
        's_qty': fields.integer(u'销售数量'),
        'd_qty': fields.integer(u'差异数量'),
        'p_cost': fields.float(u'对账成本'),
        's_cost': fields.float(u'销售成本'),
        'd_cost': fields.float(u'差异成本'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'check_list_product_report')
        cr.execute("""
                        create or replace view check_list_product_report as (
                            select ROW_NUMBER() OVER (ORDER BY aa.braid,aa.supid,aa.proid)  as id,* from (
                                SELECT
                                    braid AS braid,
                                    supid AS supid,
                                    check_list_product.type as type,
                                    rp.code AS sup_code,
                                    proid AS proid,
                                    pt.code AS pro_code,
                                    SUM (CASE WHEN checkt = '1' THEN saleqty ELSE 0.00 END) AS p_qty,
                                    SUM (CASE WHEN checkt = '0' THEN saleqty ELSE 0.00 END) AS s_qty,
                                    SUM (CASE WHEN checkt = '1' THEN saleqty ELSE 0.00 END) -SUM (CASE WHEN checkt = '0' THEN saleqty ELSE 0.00 END) AS d_qty,
                                    SUM (CASE WHEN checkt = '1' THEN COST ELSE 0.00 END) AS p_cost,
                                    SUM (CASE WHEN checkt = '0' THEN COST ELSE 0.00 END) AS s_cost,
                                    SUM (CASE WHEN checkt = '1' THEN COST ELSE 0.00 END) -SUM (CASE WHEN checkt = '0' THEN COST ELSE 0.00 END) AS d_cost
                                FROM
                                    check_list_product
                                    LEFT JOIN res_partner rp
                                        ON   check_list_product.supid = rp.id
                                    LEFT JOIN product_template pt
                                        ON   check_list_product.proid = pt.id
                                WHERE
                                    check_list_product.date BETWEEN (
                                        SELECT
                                            MIN (date_start)
                                        FROM
                                            account_period
                                        WHERE
                                            now() - interval '1 month' BETWEEN date_start AND date_stop
                                            AND company_id = check_list_product.braid
                                    ) AND (
                                        SELECT
                                            MAX (date_stop)
                                        FROM
                                            account_period
                                        WHERE
                                            now() - interval '1 month' BETWEEN date_start AND date_stop
                                            AND company_id = check_list_product.braid
                                    )
                                GROUP BY
                                    braid,
                                    supid,
                                    check_list_product.type,
                                    rp.code,
                                    proid,
                                    pt.code
                            ) aa
                            )
                    """)

    def view_detail(self, cr, uid, ids, context=None):
        braid = self.browse(cr, uid, ids[0], context=context).braid.id
        supid = self.browse(cr, uid, ids[0], context=context).supid.id
        proid = self.browse(cr, uid, ids[0], context=context).proid.id
        # 取上个月的今日
        today = datetime.datetime.now()
        if today.month != 1:
            year = today.year
            month = today.month - 1
        else:
            year = today.year - 1
            month = 12
        count_day = calendar.monthrange(year, month)[1]
        last_today = today - datetime.timedelta(days=count_day)
        # 计算上个账期的起始日期和结束日期
        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', last_today),
                                                                      ('date_stop', '>=', last_today),
                                                                      ('company_id', '=', braid)])
        start = False
        end = False
        for period_id in period_ids:
            period = self.pool.get('account.period').browse(cr, uid, period_id)
            date_start = period.date_start
            date_stop = period.date_stop
            if start:
                if start < date_start:
                    start = date_start
            else:
                start = date_start
            if end:
                if end > date_start:
                    end = date_stop
            else:
                end = date_stop
        return {
            'name': ('商品明细'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'check.list.product',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('braid', '=', braid), ('supid', '=', supid), ('proid', '=', proid), ('date', '>=', start),
                       ('date', '<=', end)],
        }

    def import_list(self, cr, uid, ids, context=None):
        l_ids = self.pool.get('check.list.product').search(cr, uid, [])
        for l_id in l_ids:
            self.pool.get('check.list.product').unlink(cr, uid, l_id, context=None)
        ms = self.get_sqlca(self)
        sql = "SELECT checkt,braid,supid,proid,checkid,checkdate,amount,receiptid,checkamt,checkqty FROM tmp_bn_check_account_list_pro"
        record = ms.ExecQuery(sql.encode('utf-8'))
        for (checkt, braid, supid, proid, checkid, checkdate, amount, receiptid, checkamt, checkqty) in record:
            if checkt:
                if checkt == 'sales':
                    checkt = '0'
                if checkt == 'payable_dx':
                    checkt = '1'
            company_id = self.pool.get('res.company').search_bycode(cr, uid, braid)
            sup_id = self.pool.get('res.partner').search_bycode(cr, uid, supid)
            proid = self.pool.get('product.template').search_bycode(cr, uid, proid)
            self.pool.get('check.list.product').create(cr, uid, {
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
            })
        return True

    def get_sqlca(self):
        ms = Lz_read_SQLCa(self)
        return ms