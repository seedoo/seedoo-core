# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import hashlib
import json
import socket

import requests

from openerp.osv import fields, osv


class gedoc_configuration(osv.osv_memory):
    _name = 'gedoc.configuration'
    _description = 'Gedoc Base Configuration'
    _inherit = 'res.config'

    _columns = {
        'company_name': fields.char('Denominazione',
                                    size=256,
                                    readonly=False,
                                    required=True),
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
        'disclaimer_check': fields.boolean('Disclaimer', readonly=True)
    }

    _defaults = {
        'disclaimer_check': True
    }

    def execute(self, cr, uid, ids, context=None):
        for data in self.browse(cr, uid, ids):
            company_obj = self.pool.get('res.company')
            vals = {
                'name': data['company_name'],
                'ammi_code': data['ipa_code'],
                'street': data['street'],
                'city': data['city'],
                'zip': data['zip']}
            company_obj.write(cr, uid, 1, vals)
            self._track_installation(vals)

    def _track_installation(self, company_vals):
        try:
            digest = hashlib.sha256()
            digest.update(socket.gethostname())
            hash_value = digest.digest().encode('hex')
            data = {
                'company_vals': company_vals,
                'hash': hash_value
            }
            url = "http://seedoo-crm.flosslab.com/count/ping"
            requests.post(url=url, data=json.dumps(data))
        except:
            pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
