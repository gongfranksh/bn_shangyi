import time
from openerp.report import report_sxw
from openerp import api, models
from openerp.tools.float_utils import float_round

class bn_shangyi_print_check_account(models.AbstractModel):
    _name = 'report.bn_shangyi.bn_shangyi_print_check_account'
    
    def render_html(self,cr,uid,ids,data=None,context=None):
        heard_data = self.pool.get('check.account').browse(cr,uid,ids[0])
        saledetail_ids=heard_data.saledetail
        saledetail_saleamt_sum=0
        saledetail_costamt_sum=0
        for saledetail_id in saledetail_ids:
            saledetail_saleamt_sum=saledetail_saleamt_sum+saledetail_id.saleamt
            saledetail_costamt_sum=saledetail_costamt_sum+saledetail_id.costamt
        payable_ids=heard_data.payable
        payable_sum=0
        for payable_id in payable_ids:
            payable_sum=payable_sum+payable_id.check_qty*payable_id.receipt_amt
        payable_head_ids=heard_data.payable_head
        payable_head_amount_sum=0
        payable_head_tax_sum=0
        payable_head_sum=0
        for payable_head_id in payable_head_ids:
            payable_head_amount_sum=payable_head_amount_sum+payable_head_id.orderamt
            payable_head_tax_sum=payable_head_tax_sum+payable_head_id.ordertax
            payable_head_sum=payable_head_sum+payable_head_id.amout
        deduct_fund_ids=heard_data.deduct_fund
        deduct_fund_amount=0
        deduct_fund_tax=0
        deduct_fund_sum=0
        for deduct_fund_id in deduct_fund_ids:
            deduct_fund_amount=deduct_fund_amount+deduct_fund_id.amount
            deduct_fund_tax=deduct_fund_tax+deduct_fund_id.tax
            deduct_fund_sum=deduct_fund_sum+deduct_fund_id.sum
        docargs = {
            'heard': heard_data,
            'saledetail': heard_data.saledetail,
            'saledetail_saleamt_sum':saledetail_saleamt_sum,
            'saledetail_costamt_sum':saledetail_costamt_sum,
            'payable': heard_data.payable,
            'payable_sum':payable_sum,
            'payable_head': heard_data.payable_head,
            'payable_head_amount_sum':payable_head_amount_sum,
            'payable_head_tax_sum':payable_head_tax_sum,
            'payable_head_sum':payable_head_sum,
            'deduct_fund': heard_data.deduct_fund,
            'deduct_fund_amount':deduct_fund_amount,
            'deduct_fund_tax':deduct_fund_tax,
            'deduct_fund_sum':deduct_fund_sum,
        }
        return self.pool.get('report').render(cr, uid, [],'bn_shangyi.print_check_account', values=docargs,context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: