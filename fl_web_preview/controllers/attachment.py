# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import base64
import logging

from odoo import http, registry, SUPERUSER_ID
from odoo.api import Environment
from odoo.http import request
from odoo.tools.misc import str2bool

_logger = logging.getLogger(__name__)


class AttachmentController(http.Controller):

    @http.route('/utils/attachment/content/<int:id>', type='http', auth="none", methods=['GET'], csrf=False)
    def utils_attachment_content(self, model='ir.attachment', id=None, field='datas', access_token=None, db=None, **kw):

        database = db or kw.get("db", False) or request.db
        if database and database in http.db_list():
            with Environment.manage():
                cr = registry(database).cursor()
                env = Environment(cr, SUPERUSER_ID, {})

                status, headers, content = env['ir.http'].with_user(env.ref("base.public_user")).binary_content(
                    model=model, id=id, field=field, access_token=access_token)

                if status != 200:
                    return env['ir.http']._response_by_status(status, headers, content)

                content_base64 = base64.b64decode(content)
                headers.append(('Content-Length', len(content_base64)))
                response = request.make_response(content_base64, headers)
                return response

        logging_info = "Request for attachment %d not bound to a Database. " % id
        if database:
            logging_info += "Database '%s' not found on the database list" % database
        logging.info(logging_info)

        return request.not_found()

    @http.route('/utils/attachment/add', type='http', auth="user", methods=['POST'])
    def add_attachment(self, ufile, temporary=False, **kw):
        tmp = temporary and str2bool(temporary) or False
        name = "Access Attachment: %s" % ufile.filename
        attachment = request.env['ir.attachment'].create({
            'name': tmp and "(Temporary) %s" % name or name,
            'datas': base64.b64encode(ufile.read()),
            # 'datas_fname': ufile.filename,
            'type': 'binary',
            'public': False,
            # 'temporary': tmp,
        })
        attachment.generate_access_token()
        if ufile.mimetype and ufile.mimetype != 'application/octet-stream':
            attachment.sudo().write({
                'mimetype': ufile.mimetype,
            })
        # TODO: il parametro di configurazione è stato inserito nel modulo fl_web_preview ma dovrà essere spostato nel modulo fl_web_preview_msoffice al refactoring di questo metodo
        base_url = request.env['ir.config_parameter'].sudo().get_param('fl_web_preview_msoffice.web_base_url')
        if not base_url:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        result = attachment.read(['name', 'mimetype', 'checksum', 'access_token'])[0]
        result['url'] = '%s/utils/attachment/content/%d?access_token=%s&db=%s' % (
            base_url, attachment.id, attachment.access_token, request.env.cr.dbname)
        return json.dumps(result)
