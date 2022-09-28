# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo.addons.fl_fields_file.fields import file

from odoo import models, api

_logger = logging.getLogger(__name__)

class AutoVacuum(models.AbstractModel):

    _inherit = "ir.autovacuum"

    @api.model
    def power_on(self, *args, **kwargs):
        res = super(AutoVacuum, self).power_on(*args, **kwargs)
        file.clean_store(self.env.cr.dbname, self.env)
        return res