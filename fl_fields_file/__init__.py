# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from . import fields
from . import models
from . import controllers

#----------------------------------------------------------
# Patch System on Load
#----------------------------------------------------------

def _patch_system():
    from . import patch