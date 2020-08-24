
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import openerp.addons.web.controllers.main as main
import simplejson

from openerp import SUPERUSER_ID
from openerp.http import request
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


class DataSet(main.DataSet):

    def do_search_read(self, model, fields=False, offset=0, limit=False, domain=None, sort=None):
        if model == 'protocollo.protocollo' and request.uid != SUPERUSER_ID:
            Model = request.session.model(model)
            search_protocollo_ids = Model.get_search_protocollo_ids(domain)
            filtered_protocollo_ids = Model.filter_protocollo_ids(search_protocollo_ids, request.context)
            request.context['filtered_protocollo_ids'] = filtered_protocollo_ids
        return super(DataSet, self).do_search_read(model, fields, offset, limit, domain, sort)
