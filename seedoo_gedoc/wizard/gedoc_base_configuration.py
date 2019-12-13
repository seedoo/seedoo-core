# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import json
import threading

import requests

from openerp.osv import fields, osv


class gedoc_configuration(osv.osv_memory):
    _name = 'gedoc.configuration'
    _description = 'Gedoc Base Configuration'
    _inherit = 'res.config'

    _columns = {
        'company_name': fields.char('Denominazione',
                                    size=256,
                                    readonly=False),
        'ipa_code': fields.char('Codice IPA Amministrazione',
                                size=10,
                                readonly=False,
                                required=False),
        'street': fields.char('Indirizzo',
                              size=256,
                              readonly=False,
                              required=False),
        'city': fields.char('Comune',
                            size=256,
                            readonly=False,
                            required=False),
        'zip': fields.char('CAP',
                           size=5,
                           readonly=False,
                           required=False),
        'disclaimer_check': fields.boolean('Disclaimer')
    }

    _defaults = {
        'disclaimer_check': True
    }

    def execute(self, cr, uid, ids, context=None):
        company_obj = self.pool.get("res.company")
        instance_obj = self.pool.get("seedoo_gedoc.instance")

        for data in self.browse(cr, uid, ids):
            vals = {
                'name': data['company_name'] and data['company_name'] or 'Non fornito',
                'ammi_code': data['ipa_code'] and data['ipa_code'] or '',
                'street': data['street'] and data['street'] or '',
                'city': data['city'] and data['city'] or '',
                'zip': data['zip'] and data['zip'] or '',
                'disclaimer_check': data['disclaimer_check'] and data['disclaimer_check'] or '',
            }

            if data['company_name']:
                company_obj.write(cr, uid, 1, vals)

            instance_uuid = instance_obj.get_seedoo_instance_uuid(cr, uid)
            thread = threading.Thread(target=self._track_installation, args=[instance_uuid, vals])
            thread.start()

    def _track_installation(self, instance_uuid, company_vals):
        try:
            headers = {
                "Content-Type": "application/json"
            }

            data = {
                "params": {
                    "instance_uuid": instance_uuid,
                    "company_vals": company_vals
                }
            }

            url = "https://www.seedoo.it/count/instance"

            requests.post(
                url=url,
                headers=headers,
                data=json.dumps(data)
            )
        except:
            pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
