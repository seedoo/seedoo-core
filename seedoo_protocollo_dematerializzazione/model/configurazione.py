# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
from openerp import models, fields


class DematerializzazioneConfigurazione(models.Model):
    _name = "dematerializzazione.configurazione"

    etichetta_altezza = fields.Integer(
        string="Altezza Etichetta",
        default=28
    )

    etichetta_larghezza = fields.Integer(
        string="Larghezza Etichetta",
        default=54
    )

    etichetta_logo = fields.Binary(
        string="Logo",
        attacchment=True
    )
