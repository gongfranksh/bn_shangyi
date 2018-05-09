# -*- coding: utf-8 -*-
from openerp import models, api, fields

class res_partner(models.Model):
    _inherit='res.partner'

    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.code:
                code=inv.code
            else:
                code=' '
            if inv.name:
                name=inv.name
            else:
                name=' '
            name=code+name
            result.append((inv.id, name))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        return recs.name_get()