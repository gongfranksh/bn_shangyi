# -*- coding: utf-8 -*-
import datetime

from openerp.osv import fields, osv
from BNmssql import Lz_test_SQLCa


class begin_check(osv.osv):
    _name = 'begin.check'
    _columns = {
        'account_id': fields.many2one('account.period', u'账期'),
        'date': fields.date(u'日期'),
        'company_id': fields.many2one('res.company', u'门店'),
        'code': fields.related('company_id', 'code', type='char', string=u'门店编号'),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'begin.check',
                                                                                                 context=c),
        'date': fields.datetime.now(),
    }

    def onchange_date(self, cr, uid, ids, date):
        users = self.pool.get('res.users').browse(cr, uid, uid)
        company_id = users.company_id and users.company_id.id or False
        if company_id:
            p_ids = self.pool.get('account.period').search(cr, uid,
                                                           [('company_id', '=', company_id), ('date_start', '<=', date),
                                                            ('date_stop', '>=', date)])
        return {'value': {'account_id': p_ids[0]}}

    def onchange_company(self, cr, uid, ids, company_id):
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id)
            code = company.code
        return {'value': {'code': code}}

    def begin_check(self, cr, uid, ids, context=False):
        ms = Lz_test_SQLCa(self)
        # 从checkplan表查出盘点的开始时间和结束时间
        nowdate = str(datetime.datetime.now())[0:19]
        sql_plan_date = "SELECT MIN(c.CheckDate) AS start_date,MAX(c.EndDate) AS end_date FROM checkplan c WHERE '%s' BETWEEN c.CheckDate AND c.EndDate" % (
        nowdate)
        plan_date = ms.ExecQuery(sql_plan_date.encode('utf-8'))
        if plan_date[0][0] and plan_date[0][1]:
            start_date = plan_date[0][0]
            end_date = plan_date[0][1]
        else:
            raise osv.except_osv((u'错误'), (u'没有正在进行中的盘点'))
        # 同步盘点明细
        company_id = self.pool.get('begin.check').browse(cr, uid, ids[0]).company_id
        braid = company_id.code
        # 验证是否同步
        begin_check = self.browse(cr, uid, ids[0])
        front_check_bak_ids = self.pool.get('front.check.bak').search(cr, uid, [('head_id.company_id.code', '=', braid),
                                                                                ('head_id.start_date', '>=',
                                                                                 begin_check.account_id.date_start), (
                                                                                'head_id.end_date', '<=',
                                                                                begin_check.account_id.date_stop), ])
        if front_check_bak_ids:
            raise osv.except_osv((u'错误'), (u'该门店该账期已经同步！！！'))
        # 开始同步
        sql_front_check_bak = "select Braid,InputDate,Posno,OperatorId,ProId,CheckQty1,ReceiptNo,ShieldNo from Front_check_bak where InputDate between '%s' and '%s' and checkstep='0' and braid='%s'" % (
        start_date, end_date, braid)
        front_check_bak = ms.ExecQuery(sql_front_check_bak.encode('utf-8'))
        for (Braid, InputDate, Posno, OperatorId, ProId, CheckQty1, ReceiptNo, ShieldNo) in front_check_bak:
            if Braid:
                braid_ids = self.pool.get('res.company').search(cr, uid, [('code', '=', Braid)])
                if braid_ids:
                    braid_id = braid_ids[0]
                else:
                    braid_id = False
            if OperatorId:
                o_ids = self.pool.get('hr.employee').search(cr, uid, [('code', '=', OperatorId)])
                if o_ids:
                    o_id = o_ids[0]
                else:
                    o_id = False
            if ProId:
                p_ids = self.pool.get('product.template').search(cr, uid, [('code', '=', ProId)])
                if p_ids:
                    p_id = p_ids[0]
                else:
                    p_id = False
            val = {
                'operaorid': o_id,
                'posno': Posno,
                'inputdate': InputDate,
                'product_id': p_id,
                'checkqty1': CheckQty1,
                'checkqty2': CheckQty1,
                'receiptno': ReceiptNo,
                'shield': ShieldNo,
                'checkstep': '1',
                'company_id': braid_id,
            }
            self.pool.get('front.check.bak').create(cr, uid, val)
        sql_front_check_bak_head = "SELECT distinct convert(varchar(10),fcb.InputDate,121) AS inputdate,fcb.ShieldNo,fcb.Braid FROM front_check_bak fcb where fcb.InputDate between '%s' and '%s' and checkstep='0' and braid='%s'" % (
        start_date, end_date, braid)
        front_check_bak_head = ms.ExecQuery(sql_front_check_bak_head.encode('utf-8'))
        inc = 1
        for (inputdate, ShieldNo, Braid) in front_check_bak_head:
            if Braid:
                braid_ids = self.pool.get('res.company').search(cr, uid, [('code', '=', Braid)])
                b_code = Braid
                if braid_ids:
                    braid_id = braid_ids[0]
                else:
                    braid_id = False
            else:
                b_code = '00000'
            if inputdate:
                id_code = inputdate[2:4] + inputdate[5:7]
            else:
                id_code = '0000'
            code = b_code + id_code + str(inc).zfill(4)
            inc = inc + 1
            val = {
                'code': code,
                'start_date': start_date,
                'end_date': end_date,
                'date': inputdate,
                'shield': ShieldNo,
                'company_id': braid_id,
                'state': '1',
            }
            self.pool.get('front.check.bak.head').create(cr, uid, val)
        b_ids = self.pool.get('front.check.bak').search(cr, uid, [('head_id', '=', False)])
        for b_id in b_ids:
            record = self.pool.get('front.check.bak').browse(cr, uid, b_id)
            record_company_id = record.company_id and record.company_id.id
            record_shield = record.shield
            record_inputdate = record.inputdate
            head_ids = self.pool.get('front.check.bak.head').search(cr, uid, [('start_date', '<=', record_inputdate),
                                                                              ('end_date', '>=', record_inputdate),
                                                                              ('shield', '=', record_shield),
                                                                              ('company_id', '=', record_company_id)])
            h_id = False
            for head_id in head_ids:
                state = self.pool.get('front.check.bak.head').browse(cr, uid, head_id).state
                if state != '3':
                    h_id = head_id
                    continue
            self.pool.get('front.check.bak').write(cr, uid, b_id, {'head_id': h_id})
        return


class front_check_bak_head(osv.osv):
    _name = "front.check.bak.head"
    _columns = {
        'code': fields.char(u'盘点批次号'),
        'start_date': fields.date(u'开始日期'),
        'end_date': fields.date(u'结束日期'),
        'date': fields.date('初盘日期'),
        'shield': fields.char(u'货架号'),
        'company_id': fields.many2one('res.company', u'门店'),
        'r_id': fields.many2one('hr.employee', u'复盘人'),
        'r_operaorid': fields.many2one('hr.employee', u'复盘录入人'),
        'state': fields.selection([('1', u'初盘'), ('2', u'复盘'), ('3', u'已抛砖')], u'状态', readonly=True),
        'details_id': fields.one2many('front.check.bak', 'head_id', string=u'盘点明细'),
    }
    _rec_name = 'code'

    # 增加盘点明细
    def add_detail(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False,
            'shield': record.shield,
            'company_id': record.company_id and record.company_id.id
        })
        return {
            'name': u'增加明细',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'front.check.bak.add',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    # 初次修改保存盘点录入员；验证当前用户是否盘点录入员
    def write(self, cr, uid, ids, vals, context=None):
        if type(ids) == list:
            r_operaorid = self.pool.get('front.check.bak.head').browse(cr, uid, ids[0]).r_operaorid
        elif type(ids) == int:
            r_operaorid = self.pool.get('front.check.bak.head').browse(cr, uid, ids).r_operaorid
        else:
            raise osv.except_osv((u'错误'), (u'传递的id不正确！！！'))
        if r_operaorid:
            r_operaorid = self.pool.get('hr.employee').browse(cr, uid, r_operaorid.id)
            user_id = r_operaorid and r_operaorid.resource_id and r_operaorid.resource_id.user_id and r_operaorid.resource_id.user_id.id or False
            if user_id and user_id != uid:
                raise osv.except_osv((u'错误'), (u'当前登陆用户不是盘点录入员！！'))
        else:
            resource_ids = self.pool.get('resource.resource').search(cr, uid, [('user_id', '=', uid)])
            h_ids = []
            for resource_id in resource_ids:
                hr_employee = self.pool.get('hr.employee').search(cr, uid, [('resource_id', '=', resource_id)])
                employee = self.pool.get('hr.employee').browse(cr, uid, hr_employee[0])
                user_id = employee.user_id and employee.user_id.id
                h_ids.append(hr_employee[0])
            if h_ids:
                vals['r_operaorid'] = h_ids[0]
            else:
                raise osv.except_osv((u'错误'), (u'当前用户没有权限录入！！请检查权限设置以及当前用户是否绑定员工！！'))
        if 'state' not in vals.keys():
            vals['state'] = '2'
        return super(front_check_bak_head, self).write(cr, uid, ids, vals, context=context)


class front_check_bak(osv.osv):
    _name = "front.check.bak"
    _columns = {
        'operaorid': fields.many2one('hr.employee', u'初盘人'),
        'posno': fields.char(u'POS机号'),
        'inputdate': fields.datetime(u'录入时间'),
        'product_id': fields.many2one('product.template', '产品'),
        'proid': fields.related('product_id', 'code', type='char', string=u'产品编码'),
        'barcode': fields.related('product_id', 'barcode', type='char', string=u'条码'),
        'checkqty1': fields.integer(u'初盘数'),
        'checkqty2': fields.integer(u'复盘数'),
        'receiptno': fields.char(u'初盘流水号'),
        'shield': fields.char(u'货架号'),
        'checkstep': fields.selection([('1', u'初盘'), ('2', u'复盘')], u'步骤', readonly=True),
        'company_id': fields.many2one('res.company', u'门店'),
        'head_id': fields.many2one('front.check.bak.head', 'head_id', ondelete='cascade'),
    }


class front_check_bak_add(osv.osv_memory):
    _name = 'front.check.bak.add'
    _columns = {
        'head_id': fields.many2one('front.check.bak.head', u'盘点批次'),
        'shield': fields.char(u'货架号'),
        'company_id': fields.many2one('res.company', u'门店'),
        'detail_ids': fields.one2many('front.check.bak.add.detail', 'add_id', string=u'新增明细'),
    }

    def default_get(self, cr, uid, fields, context=None):
        active_id = context.get('active_id', False)
        shield = context.get('shield', False)
        company_id = context.get('company_id', False)
        return {
            'head_id': active_id,
            'shield': shield,
            'company_id': company_id,
        }
        return super(front_check_bak_add, self).default_get(cr, uid, fields, context=context)

    def add_detail(self, cr, uid, ids, context=None):
        add = self.browse(cr, uid, ids[0])
        details = add.detail_ids
        for detail in details:
            val = {
                'product_id': detail.product_id.id,
                'checkqty2': detail.checkqty2,
                'shield': add.shield,
                'checkstep': '2',
                'company_id': add.company_id and add.company_id.id or False,
                'head_id': add.head_id and add.head_id.id,
            }
            self.pool.get('front.check.bak').create(cr, uid, val)
        return


class front_check_bak_add_detail(osv.osv_memory):
    _name = 'front.check.bak.add.detail'
    _columns = {
        'product_id': fields.many2one('product.template', u'产品', domain=[('code', '!=', False)]),
        'checkqty2': fields.integer(u'复盘数'),
        'add_id': fields.many2one('front.check.bak.add', 'add_id'),
    }


class front_check_bak_wizard(osv.osv_memory):
    _name = "front.check.bak.wizard"
    _columns = {
        'details': fields.one2many('front.check.bak.wizard.detail', 'wizard_id', string=u'批次明细 '),
    }

    def default_get(self, cr, uid, fields, context=None):
        active_ids = context.get('active_ids', False)
        val = []
        for a_id in active_ids:
            head_id = self.pool.get('front.check.bak.head').browse(cr, uid, a_id)
            if head_id.state == '2':
                val.append((0, 0, {'head_id': a_id, 'state': head_id.state}))
        return {
            'details': val,
        }
        return super(front_check_bak_wizard, self).default_get(cr, uid, fields, context=context)

    def return_shangyi(self, cr, uid, ids, context=None):
        details = self.browse(cr, uid, ids[0]).details
        value = False
        for detail in details:
            head_id = detail.head_id
            details_id = head_id.details_id
            for bak in details_id:
                if value:
                    value = value + "INSERT INTO front_check(Braid,InputDate,Posno,OperatorId,ProId,BarCode,ClassId,CheckQty1,ReceiptNo,ShieldNo,flag) select '" + bak.company_id.code + "'," + 'getdate(),' + "'odoo','" + bak.head_id.r_id.code + "','" + bak.product_id.code + "','" + bak.product_id.barcode + "','" + bak.product_id.categ_id.code + "','" + str(
                        bak.checkqty1) + "','" + bak.head_id.code + "','" + bak.shield + "','9';"
                else:
                    value = "INSERT INTO front_check(Braid,InputDate,Posno,OperatorId,ProId,BarCode,ClassId,CheckQty1,ReceiptNo,ShieldNo,flag) select '" + bak.company_id.code + "'," + 'getdate(),' + "'odoo','" + bak.head_id.r_id.code + "','" + bak.product_id.code + "','" + bak.product_id.barcode + "','" + bak.product_id.categ_id.code + "','" + str(
                        bak.checkqty1) + "','" + bak.head_id.code + "','" + bak.shield + "','9';"
        ms = Lz_test_SQLCa
        ms.ExecNonQuery(value.encode('utf-8'))
        for detail in details:
            head_id = detail.head_id
            employee_id = detail.head_id.r_operaorid
            u_id = employee_id.resource_id.user_id.id
            self.pool.get('front.check.bak.head').write(cr, u_id, head_id.id, {'state': '3'})
        return


class front_check_bak_wizard_detail(osv.osv_memory):
    _name = "front.check.bak.wizard.detail"
    _columns = {
        'head_id': fields.many2one('front.check.bak.head', u'盘点批次', domain=[('state', '=', '2')]),
        'state': fields.related('head_id', 'state', type='selection',
                                selection=[('1', u'初盘'), ('2', u'复盘'), ('3', u'已抛砖')], string=u'状态'),
        'wizard_id': fields.many2one('front.check.bak.wizard', 'Wizard'),
    }
