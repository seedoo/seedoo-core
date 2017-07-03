
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import openerp.addons.web.controllers.main as main
import magic
import base64
import os

from openerp.addons.web import http
openerpweb = http


class PdfStream(main.Binary):
    _cp_path = "/web/binary"

    def return_void(self, req):
        with open(os.path.realpath(__file__).split('controllers')[0] +
                  'void.pdf', 'rb') as f:
            resp = req.make_response(
                f.read(),
                [('Content-Type',
                  'application/pdf')]
            )
            f.close()
            return resp

    @openerpweb.httprequest
    def pdf(self, req, model, field, id=None, filename_field=None, **kw):
        """ Download link for files stored as binary fields.

        If the ``id`` parameter is omitted, fetches the default value for the
        binary field (via ``default_get``), otherwise fetches the field for
        that precise record.

        :param req: OpenERP request
        :type req: :class:`web.common.http.HttpRequest`
        :param str model: name of the model to fetch the binary from
        :param str field: binary field
        :param str id: id of the record from which to fetch the binary
        :param str filename_field: field holding the file's name, if any
        :returns: :class:`werkzeug.wrappers.Response`
        """
        Model = req.session.model(model)
        fields = [field]
        if filename_field:
            fields.append(filename_field)
        if id:
            res = Model.read([int(id)], fields, req.context)[0]
        else:
            return self.return_void(req)
        filecontent = base64.b64decode(res.get(field, ''))
        if not filecontent:
            return self.return_void(req)
        else:
            filename = '%s_%s' % (model.replace('.', '_'), id)
            if filename_field:
                filename = res.get(filename_field, '') or filename
            ct = magic.from_buffer(filecontent, mime=True)
            if ct == 'application/pdf':
                return req.make_response(
                    filecontent,
                    [('Content-Type', ct),
                     ('Content-Length', len(filecontent))]
                )
            else:
                return self.return_void(req)
