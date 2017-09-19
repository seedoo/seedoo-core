# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.tools import convert

original_xml_import = convert.xml_import

class SeedooProtocolloImport(original_xml_import):

    def _tag_delete(self, cr, rec, data_node=None, mode=None):
        d_model = rec.get("model")
        d_search = rec.get("search",'').encode('utf-8')
        d_id = rec.get("id")
        ids = []

        if d_search:
            super(SeedooProtocolloImport, self)._tag_delete(cr, rec, data_node, mode)
        if d_id:
            try:
                ids.append(self.id_get(cr, d_id))
                super(SeedooProtocolloImport, self)._tag_delete(cr, rec, data_node, mode)
            except ValueError:
                # d_id cannot be found. doesn't matter in this case
                pass

convert.xml_import = SeedooProtocolloImport
