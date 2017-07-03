# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from . import test_protocollo_in
from . import test_protocollo_out
from . import test_wizard_protocollo

checks = [
    test_protocollo_in,
    test_protocollo_out,
    test_wizard_protocollo,
]
