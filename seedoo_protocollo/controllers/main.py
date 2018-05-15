
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import openerp.addons.web.controllers.main as main
import simplejson

from openerp.addons.web import http

openerpweb = http


class Binary(main.Binary):

    @http.route('/web/binary/saveas_ajax', type='http', auth="public")
    def saveas_ajax(self, data, token):
        jdata = simplejson.loads(data)
        model = jdata['model']
        if model == 'protocollo.protocollo':
            context = jdata.get('context', {})
            context['skip_check'] = True
            jdata['context'] = context
        new_data = simplejson.dumps(jdata)
        return super(Binary, self).saveas_ajax(new_data, token)
