# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from openerp import api, models
from openerp.tools.float_utils import float_round

class print_stock_check(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(print_stock_check, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_str':self._get_str,
        })
    def _get_str(self, value):
        return ''.join(value[0:10])
    
report_sxw.report_sxw('report.print_stock_check', 'front.check.bak.head', 'addons/sales_property/report/print_stock_check.rml', parser=print_stock_check,header=False)

class bn_shangyi_print_stock_check(models.AbstractModel):
    _name = 'report.bn_shangyi.bn_shangyi_print_stock_check'
    
    def render_html(self,cr,uid,ids,data=None,context=None):
        heard_data = self.pool.get('front.check.bak.head').browse(cr,uid,ids[0])
        docargs = {
            'heard': heard_data,
            'details_id': heard_data.details_id,
        }
        return self.pool.get('report').render(cr, uid, [],'bn_shangyi.print_stock_check', values=docargs,context=context)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: