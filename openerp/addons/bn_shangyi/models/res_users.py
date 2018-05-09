# -*- coding: utf-8 -*-
from openerp import models, fields

class res_users(models.Model):
    _inherit='res.users'

    sy_groups=fields.Many2many('purchase.group',string='Purchase Group',)