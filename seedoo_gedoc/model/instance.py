# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import uuid

from openerp import models, fields, api
from openerp.exceptions import MissingError
from openerp.tools.translate import _


class Instance(models.Model):
    _name = "seedoo_gedoc.instance"

    _constraints = [
        ("uuid_uniq", "UNIQUE(uuid)", "UUID must be unique")
    ]

    uuid = fields.Char(
        string="UUID",
        help="Universally unique identifier",
        required=True
    )

    install_datetime = fields.Datetime(
        string="Install date and time",
        required=True
    )

    @api.model
    def create(self, vals):
        if "uuid" not in vals:
            vals["uuid"] = str(uuid.uuid4())

        if "install_datetime" not in vals:
            vals["install_datetime"] = fields.Datetime.now()

        return super(Instance, self).create(vals)

    @api.v8
    def get_seedoo_instance(self):
        instance_id = self.search([], limit=1)
        if not instance_id:
            raise MissingError(_("Instance not found"))

        return instance_id

    @api.v7
    def get_seedoo_instance(self, cr, uid, context=None):
        instanceid = self.search(cr, uid, [], limit=1)
        if not instanceid:
            raise MissingError(_("Instance not found"))

        return instanceid

    @api.v8
    def get_seedoo_instance_uuid(self):
        instance_id = self.search([], limit=1)
        if not instance_id:
            raise MissingError(_("Instance not found"))

        return instance_id.uuid

    @api.v7
    def get_seedoo_instance_uuid(self, cr, uid, context=None):
        instanceid = self.search(cr, uid, [], limit=1)
        if not instanceid:
            raise MissingError(_("Instance not found"))

        instance_id = self.browse(cr, uid, [instanceid[0]])
        if not instance_id:
            raise MissingError(_("Instance not found"))

        return instance_id.uuid
