# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, SUPERUSER_ID
from odoo import models, api, fields
from odoo.exceptions import AccessError

'''
is_locked_editor permette di poter modificare un documento, anche se bloccato, da un SuperUser.
'''


class Locking(models.AbstractModel):
    _name = 'sd.dms.locking'

    _description = 'Locking Document'

    locked_by_user_id = fields.Many2one(
        string="Locked by",
        comodel_name="res.users",
        readonly=True
    )

    is_locked = fields.Boolean(
        string="Is Locked",
        compute="_compute_is_locked"
    )

    is_lock_editor = fields.Boolean(
        compute='_compute_is_locked',
        string="Editor"
    )

    def lock_document(self):
        self.write(
            {'locked_by_user_id': self.env.uid}
        )

    def unlock_document(self):
        self.write(
            {'locked_by_user_id': None}
        )

    @api.model
    def _check_lock_editor(self, locked_by_user_id):
        return locked_by_user_id in (self.env.uid, SUPERUSER_ID)

    def check_lock(self):
        for record in self:
            if record.locked_by_user_id.exists() and not self._check_lock_editor(record.locked_by_user_id.id):
                message = _("The record (%s [%s]) is locked, by an other user.")
                raise AccessError(message % (record._description, record.id))

    @api.depends('locked_by_user_id')
    def _compute_is_locked(self):
        for record in self:
            if record.locked_by_user_id.exists():
                record.update({'is_locked': True, 'is_lock_editor': record.locked_by_user_id.id == record.env.uid})
            else:
                record.update({'is_locked': False, 'is_lock_editor': False})

    def _write(self, vals):
        self.check_lock()
        return super(Locking, self)._write(vals)

    def unlink(self):
        self.check_lock()
        return super(Locking, self).unlink()
