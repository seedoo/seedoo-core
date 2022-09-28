# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class DocumentAcl(models.Model):

    _name = "sd.dms.document.acl"
    _description = "Document Acl"
    _inherit = ["fl.acl"]

    _acl_field = "document_id"
    _security_field = "document_ids"

    document_ids = fields.Many2many(
        string="Documents",
        comodel_name="sd.dms.document",
        relation="sd_dms_document_acl_rel",
        column1="acl_id",
        column2="document_id"
    )

    # Il codice SQL definito nel metodo init serve a creare un trigger SQL che si occupa di eliminare le istanze delle
    # acl che vengono rimosse da un modello solamente nel caso in cui le acl non siano crate dal sistema e non siano
    # ereditate. Il trigger serve quindi per risolvere il problema dell'eliminazione di una acl che avviene da
    # interfaccia, quindi quando è fatta da un utente che utilizza il sistema. Essendo infatti il campo document_ids un
    # campo Manymany, all'eliminazione del collegamento con una acl non avviene la corrispondente eliminazione. Di
    # conseguenza, il trigger si occupa, all'eliminazione di una riga dalla tabella sd_dms_document_acl_rel, di
    # verificare ed eventualmente eliminare la corrispondete riga di acl.
    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE FUNCTION process_delete_sd_dms_document_acl_row() RETURNS TRIGGER AS $$
                BEGIN
                    IF (TG_OP = 'DELETE') THEN
                        DELETE FROM sd_dms_document_acl WHERE id = OLD.acl_id AND create_system = FALSE;
                        RETURN OLD;
                    END IF;
                END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS sd_dms_document_acl_rel ON sd_dms_document_acl_rel;
            
            CREATE TRIGGER sd_dms_document_acl_rel
            AFTER DELETE ON sd_dms_document_acl_rel
                FOR EACH ROW EXECUTE PROCEDURE process_delete_sd_dms_document_acl_row();
        """)

    @api.model
    def get_default_module_id(self):
        return self.env.ref("base.module_sd_dms")

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["document_ids"] = [(6, 0, [])]
        return super(DocumentAcl, self).copy(default=default)