# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class mail_mail(osv.osv):
    _inherit = 'mail.mail'
    _columns = {
        'company_id': fields.many2one('res.company', u'门店'),
    }

    def create(self, cr, uid, values, context=None):
        model=False
        if 'model' in values:
            model = values['model']
            values['model'] = False
        res_id=False
        if 'res_id' in values:
            res_id = values['res_id']
            values['res_id'] = False
        if model=='check.account' and res_id:
            record = self.pool.get(model).browse(cr, uid, res_id)
            #回复到发送邮箱
            if 'email_from' in values:
                email_from = values['email_from']
                values['reply_to'] = email_from
            if record:
                company_id = record.company_id and record.company_id.id or False
                values['company_id'] = company_id
            #发送对应的供应商和当前用户
            sup=record.supplier
            if uid:
                user=self.pool.get('res.users').browse(cr,uid,uid)
            if sup:
                values['recipient_ids']=[]
                values['recipient_ids'].append((4,sup.id))
            #抄送
            if context.get('default_template_id'):
                template=self.pool.get('email.template').browse(cr,uid,context.get('default_template_id'))
                if template.email_cc:
                    values['email_cc']=template.email_cc
                    if user and user.partner_id.email:
                        values['email_cc']=values['email_cc']+user.partner_id.email+';'
        return super(mail_mail, self).create(cr, uid, values, context=context)
    
    def _get_partner_access_link(self, cr, uid, mail, partner=None, context=None):
        return super(mail_mail, self)._get_partner_access_link(cr, uid, mail, partner=None, context=None)