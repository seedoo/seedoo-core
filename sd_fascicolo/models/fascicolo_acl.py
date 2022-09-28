from odoo import models, fields, api, _


class FascicoloAcl(models.Model):

    _name = "sd.fascicolo.fascicolo.acl"
    _description = "Dossier Acl inherited"
    _inherit = ["fl.acl"]

    _acl_field = "fascicolo_id"
    _security_field = "fascicolo_ids"

    fascicolo_ids = fields.Many2many(
        string="Fascicoli",
        comodel_name="sd.fascicolo.fascicolo",
        relation="sd_fascicolo_fascicolo_acl_rel",
        column1="acl_id",
        column2="fascicolo_id"
    )

    # Il codice SQL definito nel metodo init serve a creare un trigger SQL che si occupa di eliminare le istanze delle
    # acl che vengono rimosse da un modello solamente nel caso in cui le acl non siano crate dal sistema e non siano
    # ereditate. Il trigger serve quindi per risolvere il problema dell'eliminazione di una acl che avviene da
    # interfaccia, quindi quando è fatta da un utente che utilizza il sistema. Essendo infatti il campo fascicolo_ids un
    # campo Manymany, all'eliminazione del collegamento con una acl non avviene la corrispondente eliminazione. Di
    # conseguenza, il trigger si occupa, all'eliminazione di una riga dalla tabella sd_fascicolo_fascicolo_acl_rel, di
    # verificare ed eventualmente eliminare la corrispondete riga di acl.
    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE FUNCTION process_delete_sd_fascicolo_fascicolo_acl_row() RETURNS TRIGGER AS $$
                BEGIN
                    IF (TG_OP = 'DELETE') THEN
                        DELETE FROM sd_fascicolo_fascicolo_acl WHERE id = OLD.acl_id AND create_system = FALSE;
                        RETURN OLD;
                    END IF;
                END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS sd_fascicolo_fascicolo_acl_rel ON sd_fascicolo_fascicolo_acl_rel;

            CREATE TRIGGER sd_fascicolo_fascicolo_acl_rel
            AFTER DELETE ON sd_fascicolo_fascicolo_acl_rel
                FOR EACH ROW EXECUTE PROCEDURE process_delete_sd_fascicolo_fascicolo_acl_row();
        """)

    @api.model
    def get_default_module_id(self):
        return self.env.ref("base.module_sd_fascicolo")

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default["fascicolo_ids"] = [(6, 0, [])]
        return super(FascicoloAcl, self).copy(default=default)