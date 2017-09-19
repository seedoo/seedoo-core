# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv

class dematerializzazione_config_settings(osv.osv_memory):
    _name = 'dematerializzazione.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'config_id': fields.many2one('dematerializzazione.configurazione', string='Configurazione', required=True),

        'etichetta_altezza': fields.related('config_id', 'etichetta_altezza', type='integer', string='Altezza Etichetta'),
        'etichetta_larghezza': fields.related('config_id', 'etichetta_larghezza', type='integer', string='Larghezza Etichetta'),
        #'importer_ids': fields.related('config_id', 'importer_ids', type='one2many', relation='dematerializzazione.importer', string='Importer'),

        'cron_id': fields.many2one('ir.cron', string='Cron', required=True),

        'active': fields.related('cron_id', 'active', type='boolean', string='Attiva'),
        'interval_number': fields.related('cron_id', 'interval_number', type='integer', string='Intervallo'),
        'interval_type': fields.related('cron_id', 'interval_type', type='selection', selection=[('minutes', 'Minuti'),
            ('hours', 'Ore'), ('work_days','Giorni Lavorativi'), ('days', 'Giorni'),('weeks', 'Settimane'), ('months', 'Mesi')],
                                        string='Tipologia Intervallo'),
        'nextcall': fields.related('cron_id', 'nextcall', type='datetime', string='Data Prossima Esecuzione'),
    }

    def _default_config_id(self, cr, uid, context):
        ir_model_data_obj = self.pool.get('ir.model.data')
        ir_model_data_id = ir_model_data_obj.search(cr, uid, [('name', '=', 'configurazione_default')])[0]
        ir_model_data = ir_model_data_obj.browse(cr, uid, ir_model_data_id)
        return ir_model_data.res_id

    def _default_cron_id(self, cr, uid, context):
        ir_model_data_obj = self.pool.get('ir.model.data')
        ir_model_data_id = ir_model_data_obj.search(cr, uid, [('name', '=', 'ir_cron_mail_dematerializzazione_importer')])[0]
        ir_model_data = ir_model_data_obj.browse(cr, uid, ir_model_data_id)
        return ir_model_data.res_id

    _defaults = {
        'config_id': lambda self, cr, uid, c: self._default_config_id(cr, uid, c),
        'cron_id': lambda self, cr, uid, c: self._default_cron_id(cr, uid, c),
    }

    def on_change_config_id(self, cr, uid, ids, config_id, context=None):
        config_data = self.pool.get('dematerializzazione.configurazione').read(cr, uid, [config_id], [], context=context)[0]
        values = {}
        for fname, v in config_data.items():
            if fname in self._columns:
                values[fname] = v[0] if v and self._columns[fname]._type == 'many2one' else v
        return {'value' : values}

    def on_change_cron_id(self, cr, uid, ids, cron_id, context=None):
        cron_data = self.pool.get('ir.cron').read(cr, uid, [cron_id], [], context=context)[0]
        values = {}
        for fname, v in cron_data.items():
            if fname in self._columns:
                values[fname] = v[0] if v and self._columns[fname]._type == 'many2one' else v
        return {'value' : values}

    # FIXME in trunk for god sake. Change the fields above to fields.char instead of fields.related,
    # and create the function set_website who will set the value on the website_id
    # create does not forward the values to the related many2one. Write does.
    def create(self, cr, uid, vals, context=None):
        config_id = super(dematerializzazione_config_settings, self).create(cr, SUPERUSER_ID, vals, context=context)
        self.write(cr, SUPERUSER_ID, config_id, vals, context=context)
        return config_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
