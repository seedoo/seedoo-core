from contextlib import contextmanager
from unittest.mock import patch

from odoo.addons.sd_dms.tests.common import DmsTestCommon
from odoo.addons.fl_mail_client_pec.tests.common import MailClientPecTestCommon
from odoo.addons.sd_protocollo.utilities.protocollo_actions import ProtocolloActions as PA
from odoo.addons.sd_protocollo.utilities.protocollo_wizard_actions import ProtocolloWizardActions as PWA
from odoo.sql_db import Cursor
from odoo.tests import tagged


@tagged('-standard', 'sd_protocollo')
class ProtocolloTestCommon(DmsTestCommon, MailClientPecTestCommon):

    @classmethod
    def setUpClass(cls):
        super(ProtocolloTestCommon, cls).setUpClass()
        cls.protocollo_obj = cls.env["sd.protocollo.protocollo"]
        cls.archivio_obj = cls.env["sd.protocollo.archivio"]
        cls.registro_obj = cls.env["sd.protocollo.registro"]
        cls.registro_emergenza_obj = cls.env["sd.protocollo.registro.emergenza"]
        cls.assegnazione_obj = cls.env["sd.protocollo.assegnazione"]
        cls.mezzo_trasmissione_obj = cls.env["sd.protocollo.mezzo.trasmissione"]
        cls.fl_set_obj = cls.env["fl.set.set"]
        cls.voce_organingramma_obj = cls.env["fl.set.voce.organigramma"]
        cls.bus_obj = cls.env["bus.bus"]

    @contextmanager
    def mock_commit_request(self):
        """
        Patch del metodo commit per evitare che alcuni metodi dove viene utilizzato il cr.commit, come ad esempio
        la registrazione del protocollo, committino sul db e facciano il clear dei prerollback.
        """
        def _commit_request(model, *args, **kwargs):
            pass

        with patch.object(Cursor, "commit", autospec=True, wraps=Cursor, side_effect=_commit_request) as commit_request:
            yield

    @contextmanager
    def mock_protocollo_registrazione(self):
        """
        Patch del processo di registrazione.
        """
        protocollo_registra_original = PA.registra

        def _registra_action(model, *args, **kwargs):
            return model.verifica_campi_obbligatori()

        def _registra(model, *args, **kwargs):
            errors = protocollo_registra_original(model, *args, **kwargs)
            if not errors:
                self.env.user._request_notify_message("success", "Esito Registrazione", "test")
            else:
                self.env.user._request_notify_message("danger", "Esito Registrazione", "test")

        with patch.object(PWA, "protocollo_registra_action", autospec=True, wraps=PWA, side_effect=_registra_action) as protocol_registra_action, \
             patch.object(PA, "registra", autospec=True, wraps=PA, side_effect=_registra) as protocol_registra :
            yield
