from odoo import models, fields, api

SELCTION_INTEROPERABILITY = [
    ("False", "False"),
    ("2001", "2001"),
    ("2013", "2013"),
    ("2021", "2021"),
]

class Protocollo(models.Model):
    _inherit = "sd.protocollo.protocollo"

    segnatura_xml = fields.Text(
        string="Segnatura XML",
        compute="_compute_segnatura_xml",
        readonly=True,
        store=True
    )

    interoperability = fields.Selection(
        string="interoperability",
        selection=SELCTION_INTEROPERABILITY,
        default=SELCTION_INTEROPERABILITY[0][0],
    )

    @api.depends("state", "documento_id_content")
    def _compute_segnatura_xml(self):
        # viene richiamata oltre al trigger dei campi presenti in api.depends:
        # in fase di reinvio di una mail (vedi wizard protocollo_reinvio_mail)
        # in fase di caricamento di un allegato se lo stato del protocollo è registrato
        for rec in self:
            rec.aggiorna_segnatura_xml()

    def _get_allegato_filename(self, allegato):
        if not allegato.protocollo_segnatura_xml:
            super(Protocollo, self)._get_allegato_filename(allegato)