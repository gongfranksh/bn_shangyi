# -*- coding: utf-8 -*-
from BNmssql import Lz_read_SQLCa
from openerp import models, api, fields
from openerp.osv import osv


class sale_plan_model_company(models.Model):
    _name = 'sale.plan.model.company'

    code = fields.Char(u'模板编号')
    detail_ids = fields.One2many('sale.plan.model.bigclass', 'model_id', string=u'大类明细')
    state = fields.Selection([('0', u'未审核'), ('1', u'已审核')], u'状态', default='0', )

    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            result.append((inv.id, inv.code))
        return result

    # 计算大类下的品牌明细
    def compute_brand(self, cr, uid, ids, context=None):
        context = {}
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False,
        })
        return {
            'name': u'导入品牌明细',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'compute.rate',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    # 审核计划模板
    @api.one
    def aduit(self):
        # 检查公司模板模板
        details = self.detail_ids
        detail_sale_sum = 0.0
        detail_profit_sum = 0.0
        for detail in details:
            detail_sale_sum = detail_sale_sum + detail.sale_weight
            detail_profit_sum = detail_profit_sum + detail.profit_weight
        if detail_sale_sum != 100.0:
            raise osv.except_osv(('错误!'), (u'该模板大类的销售权重有误，所有权重之和应为100%！！！'))
        if detail_profit_sum != 100.0 and detail_profit_sum != 0.00:
            raise osv.except_osv(('错误!'), (u'该模板大类的毛利权重有误，所有权重之和应为100%！！！'))
        # 检查大类模板
        class_records = self.env['sale.plan.model.bigclass'].search([('model_id', '=', self.id)])
        for class_record in class_records:
            brands = class_record.brands
            brands_sale_sum = 0.0
            brands_profit_sum = 0.0
            for brand in brands:
                brands_sale_sum = brands_sale_sum + brand.sale_weight
                brands_profit_sum = brands_profit_sum + brand.profit_weight
            if int(brands_sale_sum - 100.0) <> 0.0:
                msg = u'该模板的{0}大类的品牌销售权重有误，所有权重之和应为100%！！！'
                msg = msg.format(class_record.bigclass.name)
                raise osv.except_osv(('错误!'), (msg))
            if int(brands_sale_sum - 100.0) <> 0.0 and detail_profit_sum - 0.0 != 0.0:
                msg = u'该模板的{0}大类的品牌毛利权重有误，所有权重之和应为100%！！！'
                msg = msg.format(class_record.bigclass.name)
                raise osv.except_osv(('错误!'), (msg))
        self.write({'state': '1',})


class sale_plan_model_bigclass(models.Model):
    _name = 'sale.plan.model.bigclass'

    @api.one
    @api.depends('model_id.state')
    def _get_state(self):
        self.state = self.model_id.state

    model_id = fields.Many2one('sale.plan.model.company', u'上级模板', ondelete='cascade', )
    state = fields.Selection([('0', u'未审核'), ('1', u'已审核')], u'状态', compute='_get_state', store=False, readonly=True)
    bigclass = fields.Many2one('product.category', u'大类', domain="[('parent_id.name','=','乐之产品分类')]", )
    sale_weight = fields.Float(u'销售权重(%)', digits=(16, 4))
    profit_weight = fields.Float(u'毛利权重(%)', digits=(16, 4))
    brands = fields.One2many('sale.plan.model.brand', 'model_id', string=u'品牌明细')

    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.model_id.code:
                code = inv.model_id.code
            else:
                code = ' '
            if inv.bigclass.code:
                bigclass_code = inv.bigclass.code
            else:
                bigclass_code = ' '
            result.append((inv.id, code + bigclass_code))
        return result


class sale_plan_model_brand(models.Model):
    _name = 'sale.plan.model.brand'
    model_id = fields.Many2one('sale.plan.model.bigclass', u'上级模板', ondelete='cascade', )
    brand = fields.Many2one('product.brand', u'品牌')
    sale_weight = fields.Float(u'销售权重(%)', digits=(16, 4))
    profit_weight = fields.Float(u'毛利权重(%)', digits=(16, 4))


class create_sale_plan_detail(models.TransientModel):
    _name = 'create.sale.plan.detail'
    sale_id = fields.Many2one('sale.plan', u'销售计划')
    period_id = fields.Many2one('account.period', u'账期', related='sale_id.period_id')
    model_id = fields.Many2one('sale.plan.model.company', u'模板', domain="[('state','=','1')]")

    def default_get(self, cr, uid, fields_list, context=None):
        active_id = context.get('active_id', False)
        active_id = int(active_id)
        default = {}
        default['sale_id'] = active_id
        return default
        return super(create_sale_plan_detail, self).default_get(cr, uid, fields, context=context)

    @api.one
    def create_detail(self):
        sale_id = self.sale_id
        # 删除所有子明细
        self.env['category.sale.plan'].search([('sale_plan_id', '=', sale_id.id)]).unlink()
        #        self.env['sale.plan.daily'].search([('sale_plan_id','=',sale_id.id)]).unlink()
        # 根据模板添加明细
        sale_plan = self.model_id
        for detail in sale_plan.detail_ids:
            val = {
                'sale_plan_id': sale_id.id,
                'category': detail.bigclass.id,
                'sale_weight': detail.sale_weight,
                'profit_weight': detail.profit_weight,
                'plan_sale': sale_id.plan_sale * detail.sale_weight / 100,
                'plan_profit': sale_id.plan_profit * detail.profit_weight / 100,
                'period_id': sale_id.period_id.id,
                'company_id': sale_id.company_id.id,
            }
            self.env['category.sale.plan'].create(val)
        for categ in sale_plan.detail_ids:
            categ_id = self.env['category.sale.plan'].search([('category', '=', categ.bigclass.id),
                                                              ('sale_plan_id', '=', sale_id.id)], limit=1)
            for detail in categ.brands:
                val = {
                    'category_sale_plan': categ_id.id,
                    'brand': detail.brand.id,
                    'sale_weight': detail.sale_weight,
                    'profit_weight': detail.profit_weight,
                    'plan_sale': categ_id.plan_sale * detail.sale_weight / 100,
                    'plan_profit': categ_id.plan_profit * detail.profit_weight / 100,
                    'period_id': sale_id.period_id.id,
                    'company_id': sale_id.company_id.id,
                }
                self.env['brand.sale.plan'].create(val)
        # 检查是否有日明细 若有 同步日明细
        daily_detail = sale_id.daily_detail
        if daily_detail:
            for daily in daily_detail:
                category_sale_plan = self.env['category.sale.plan'].search([('sale_plan_id', '=', sale_id.id)])
                for category in category_sale_plan:
                    val = {
                        'category_sale_plan': category.id,
                        'date': daily.date,
                    }
                    self.env['category.sale.plan.daily'].create(val)
                brand_sale_plan = self.env['brand.sale.plan'].search(
                    [('category_sale_plan.sale_plan_id', '=', sale_id.id)])
                for brand in brand_sale_plan:
                    val = {
                        'brand_sale_plan': brand.id,
                        'date': daily.date,
                    }
                    self.env['brand.sale.plan.daily'].create(val)


class compute_rate(models.TransientModel):
    _name = 'compute.rate'
    is_all = fields.Boolean(string=u'是否按门店计算')
    company_code = fields.Char(string=u'门店编码',)
    model_id = fields.Many2one('sale.plan.model.company', string=u'模板',domain="[('state','=','1')]")
    company_id = fields.Many2one('res.company', string=u'门店',)

    @api.onchange('is_all')
    def onchange_messages(self):
        is_all = self.is_all
        if is_all:
            uid = self._uid
            urser = self.env['res.users'].browse(uid)
            self.company_id = urser.company_id.id
            self.company_code = urser.company_id.code
        else:
            self.company_id = False
            self.company_code = False

    def default_get(self, cr, uid, fields_list, context=None):
        active_id = context.get('active_id', False)
        active_id = int(active_id)
        default = {}
        default['model_id'] = active_id
        return default
        return super(create_sale_plan_detail, self).default_get(cr, uid, fields, context=context)

    # 根据100业绩计算品牌权重
    @api.one
    def compute_brand(self):
        # 删除已有品牌明细
        unlink_ids = self.env['sale.plan.model.brand'].search([('model_id.model_id', '=', self.model_id.id)])
        for unlink_id in unlink_ids:
            unlink_id.unlink()
        # 创建品牌明细
        day = 100
        if self.company_code:
            braid = self.company_code
        else:
            braid = ''
        sql = """
            DECLARE @braid NVARCHAR(5);
            SELECT @braid ='{1}';
            SELECT z.top_classid,
                   z.brandid,
                   z.brandamount / y.classamount*100 AS bc_sale_rate,
                   z.brandprofit / y.classprofit*100   AS bc_profit_rate
            FROM   (SELECT top_classid,
                           brandid,
                           brandname,
                           Sum(amount)      AS brandamount,
                           Abs(Sum(profit)) AS brandprofit
                    FROM   v_bn_saledetail
                    WHERE  Datediff(day, date, Getdate()) <= {0}
                           AND top_classid <> '0900' and (@braid='' OR  braid=@braid)
                    GROUP  BY top_classid,
                              top_class_name,
                              brandid,
                              brandname) z
                   LEFT JOIN (SELECT top_classid,
                                     top_class_name,
                                     Sum(amount) AS classamount,
                                     abs(Sum(profit)) AS classprofit
                              FROM   v_bn_saledetail
                              WHERE  Datediff(day, date, Getdate()) <= {0}
                                     AND brandid IS NOT NULL
                                     AND top_classid <> '0900' and (@braid='' OR  braid=@braid)
                              GROUP  BY top_classid,
                                        top_class_name) y
                          ON z.top_classid = y.top_classid
        """
        sql = sql.format(day, braid)
        ms = Lz_read_SQLCa(self)
        records = ms.ExecQuery(sql)
        for (top_classid, brandid, bc_sale_rate, bc_profit_rate) in records:
            if top_classid:
                categ_id = self.env['sale.plan.model.bigclass'].search([('bigclass.code', '=', top_classid),
                                                                        ('model_id', '=', self.model_id.id)])
                if categ_id:
                    categ_id = categ_id[0].id
                else:
                    category_id = self.env['product.category'].search([('code', '=', top_classid)])
                    msg = u'该公司模板{0}大类未建立！！！'
                    msg = msg.format(category_id[0].name)
                    raise osv.except_osv(('错误!'), (msg))
            brand_id = False
            if brandid:
                brand_id = self.env['product.brand'].search([('code', '=', brandid)])
                if brand_id:
                    brand_id = brand_id[0].id
            val = {
                'model_id': categ_id,
                'brand': brand_id,
                'sale_weight': bc_sale_rate,
                'profit_weight': bc_profit_rate,
            }
            self.env['sale.plan.model.brand'].create(val)
