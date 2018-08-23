# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import osv
from openerp import SUPERUSER_ID

class ir_config_parameter(osv.osv):

    _inherit = 'ir.config_parameter'

    def set_auth_signup_seedoo_params(self, cr, uid, context=None):

        self.pool['ir.config_parameter'].set_param(cr, SUPERUSER_ID, 'auth_signup.reset_password', True, ['base.group_system'])
        self.pool['ir.config_parameter'].set_param(cr, SUPERUSER_ID, 'auth_signup.disable_email_create_user', True, ['base.group_system'])
        self.pool['ir.config_parameter'].set_param(cr, SUPERUSER_ID, 'auth_signup.disable_email_create_employee', True, ['base.group_system'])

        return True
