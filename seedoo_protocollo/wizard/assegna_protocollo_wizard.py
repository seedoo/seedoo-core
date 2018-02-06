# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.osv import orm
from openerp.tools.translate import _
from ..model.util.selection import *

_logger = logging.getLogger(__name__)


class protocollo_assegna_wizard(osv.TransientModel):
    """
        A wizard to manage the modification of protocol object
    """
    _name = 'protocollo.assegna.wizard'
    _description = 'Assegna Protocollo'

    def  set_before(self, before, label, value):
        if not value:
            value = ''
        before += value + '\n'
        return before

    def set_after(self, after, label, value):
        after += value + '\n'
        return after

    _columns = {
        'name': fields.char('Numero Protocollo', size=256, required=True, readonly=True),
        'reserved': fields.boolean('Riservato', readonly=True),
        'registration_date': fields.datetime('Data Registrazione', readonly=True),
        'type': fields.selection([('out', 'Uscita'),('in', 'Ingresso'),('internal', 'Interno')], 'Tipo', size=32, required=True, readonly=True),
        'cause': fields.text('Motivo della Modifica', required=True),

        'assegnatari_competenza_uffici_ids': fields.one2many('protocollo.assegna.ufficio.wizard',
                 'competenza_uffici_wizard_id', 'Uffici Assegnatari per Competenza'),
        'assegnatari_competenza_dipendenti_ids': fields.one2many('protocollo.assegna.dipendente.wizard',
                 'competenza_dipendenti_wizard_id', 'Dipendenti Assegnatari per Competenza'),
        'assegnatari_conoscenza_uffici_ids': fields.one2many('protocollo.assegna.ufficio.wizard',
                 'conoscenza_uffici_wizard_id', 'Uffici Assegnatari per Conoscenza'),
        'assegnatari_conoscenza_dipendenti_ids': fields.one2many('protocollo.assegna.dipendente.wizard',
                 'conoscenza_dipendenti_wizard_id', 'Dipendenti Assegnatari per Conoscenza'),
    }

    def _default_name(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.name

    def _default_reserved(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.reserved

    def _default_registration_date(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.registration_date

    def _default_type(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        return protocollo.type

    def _default_assegnatari_competenza_uffici_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        assegnatari = []
        for assegnatario in protocollo.assegnatari_competenza_uffici_ids:
            assegnatari.append({
                'protocollo_assegnatario_ufficio_id': assegnatario.id,
                'department_id': assegnatario.department_id.id,
                'tipo': assegnatario.tipo,
            })
        return assegnatari

    def _default_assegnatari_competenza_dipendenti_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        assegnatari = []
        for assegnatario in protocollo.assegnatari_competenza_dipendenti_ids:
            assegnatari.append({
                'protocollo_assegnatario_dipendenti_id': assegnatario.id,
                'dipendente_id': assegnatario.dipendente_id.id,
                'state': assegnatario.state,
            })
        return assegnatari

    def _default_assegnatari_conoscenza_uffici_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        assegnatari = []
        for assegnatario in protocollo.assegnatari_conoscenza_uffici_ids:
            assegnatari.append({
                'protocollo_assegnatario_ufficio_id': assegnatario.id,
                'department_id': assegnatario.department_id.id,
                'tipo': assegnatario.tipo,
            })
        return assegnatari

    def _default_assegnatari_conoscenza_dipendenti_ids(self, cr, uid, context):
        protocollo = self.pool.get('protocollo.protocollo').browse(cr, uid, context['active_id'])
        assegnatari = []
        for assegnatario in protocollo.assegnatari_conoscenza_dipendenti_ids:
            assegnatari.append({
                'protocollo_assegnatario_dipendenti_id': assegnatario.id,
                'dipendente_id': assegnatario.dipendente_id.id,
                'state': assegnatario.state,
            })
        return assegnatari

    _defaults = {
        'name': _default_name,
        'reserved': _default_reserved,
        'registration_date': _default_registration_date,
        'type': _default_type,
        'assegnatari_competenza_uffici_ids': _default_assegnatari_competenza_uffici_ids,
        'assegnatari_competenza_dipendenti_ids': _default_assegnatari_competenza_dipendenti_ids,
        'assegnatari_conoscenza_uffici_ids': _default_assegnatari_conoscenza_uffici_ids,
        'assegnatari_conoscenza_dipendenti_ids': _default_assegnatari_conoscenza_dipendenti_ids,
    }

    def _salva_assegnatari_ufficio(self, cr, uid, protocollo_id, old_assegnatari, new_assegnatari, tipo):
        update_assegnatari_ids = []
        department_ids = []
        assegnatario_ufficio_obj = self.pool.get('protocollo.assegnatario.ufficio')

        for assegnatario_ufficio in new_assegnatari:
            if not assegnatario_ufficio.department_id.id in department_ids:
                if assegnatario_ufficio.protocollo_assegnatario_ufficio_id:
                    assegnatario_ufficio_obj.write(cr, uid, [assegnatario_ufficio.protocollo_assegnatario_ufficio_id.id], {
                        'department_id': assegnatario_ufficio.department_id.id
                    })
                    update_assegnatari_ids.append(assegnatario_ufficio.protocollo_assegnatario_ufficio_id.id)
                else:
                    assegnatario_ufficio_obj.create(cr, uid, {
                        'protocollo_id': protocollo_id,
                        'department_id': assegnatario_ufficio.department_id.id,
                        'tipo': tipo
                    })
                department_ids.append(assegnatario_ufficio.department_id.id)
            else:
                raise orm.except_orm(_('Attenzione!'), _('Ci sono uffici duplicati fra gli assegnatari per %s!' % tipo))

        for old_assegnatario_ufficio_id in old_assegnatari.ids:
            if old_assegnatario_ufficio_id not in update_assegnatari_ids:
                assegnatario_ufficio_obj.unlink(cr, uid, [old_assegnatario_ufficio_id])



    def _salva_assegnatari_dipendente(self, cr, uid, protocollo_id, old_assegnatari, new_assegnatari, tipo):
        update_assegnatari_ids = []
        dipendente_ids = []
        assegnatario_dipendente_obj = self.pool.get('protocollo.assegnatario.dipendente')

        for assegnatario_dipendente in new_assegnatari:
            if not assegnatario_dipendente.dipendente_id.id in dipendente_ids:
                if assegnatario_dipendente.protocollo_assegnatario_dipendente_id:
                    assegnatario_dipendente_obj.write(cr, uid, [assegnatario_dipendente.protocollo_assegnatario_dipendente_id.id], {
                        'dipendente_id': assegnatario_dipendente.dipendente_id.id
                    })
                    update_assegnatari_ids.append(assegnatario_dipendente.protocollo_assegnatario_dipendente_id.id)
                else:
                    assegnatario_dipendente_obj.create(cr, uid, {
                        'protocollo_id': protocollo_id,
                        'dipendente_id': assegnatario_dipendente.dipendente_id.id,
                        'tipo': tipo
                    })
                dipendente_ids.append(assegnatario_dipendente.dipendente_id.id)
            else:
                raise orm.except_orm(_('Attenzione!'), _('Ci sono dipendenti duplicati fra gli assegnatari per %s!' % tipo))

        for old_assegnatario_dipendente_id in old_assegnatari.ids:
            if old_assegnatario_dipendente_id not in update_assegnatari_ids:
                assegnatario_dipendente_obj.unlink(cr, uid, [old_assegnatario_dipendente_id])


    def action_save(self, cr, uid, ids, context=None):
        before = {'Uffici Assegnatari per Competenza': '', 'Dipendenti Assegnatari per Competenza': '', 'Uffici Assegnatari per Conoscenza': '', 'Dipendenti Assegnatari per Conoscenza': ''}
        after = {'Uffici Assegnatari per Competenza': '', 'Dipendenti Assegnatari per Competenza': '', 'Uffici Assegnatari per Conoscenza': '', 'Dipendenti Assegnatari per Conoscenza': ''}
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'], context=context)
        vals = {}

        if not protocollo.reserved:
            before['Uffici Assegnatari per Competenza'] = self.set_before(before['Uffici Assegnatari per Competenza'], 'Uffici Assegnatari per Competenza',
                ', '.join([a.department_id.name for a in protocollo.assegnatari_competenza_uffici_ids])
            )
            after['Uffici Assegnatari per Competenza'] = self.set_after(after['Uffici Assegnatari per Competenza'], 'Uffici Assegnatari per Competenza',
                ', '.join([aw.department_id.name for aw in wizard.assegnatari_competenza_uffici_ids])
            )
            self._salva_assegnatari_ufficio(cr, uid, protocollo.id,
                                            protocollo.assegnatari_competenza_uffici_ids,
                                            wizard.assegnatari_competenza_uffici_ids, 'competenza')

        before['Dipendenti Assegnatari per Competenza'] = self.set_before(before['Dipendenti Assegnatari per Competenza'], 'Dipendenti Assegnatari per Competenza',
            ', '.join([a.dipendente_id.name for a in protocollo.assegnatari_competenza_dipendenti_ids])
        )
        after['Dipendenti Assegnatari per Competenza'] = self.set_after(after['Dipendenti Assegnatari per Competenza'], 'Dipendenti Assegnatari per Competenza',
            ', '.join([aw.dipendente_id.name for aw in wizard.assegnatari_competenza_dipendenti_ids])
        )
        self._salva_assegnatari_dipendente(cr, uid, protocollo.id,
                                        protocollo.assegnatari_competenza_dipendenti_ids,
                                        wizard.assegnatari_competenza_dipendenti_ids, 'competenza')

        if not protocollo.reserved:
            before['Uffici Assegnatari per Conoscenza'] = self.set_before(before['Uffici Assegnatari per Conoscenza'], 'Uffici Assegnatari per Conoscenza',
                ', '.join([a.department_id.name for a in protocollo.assegnatari_conoscenza_uffici_ids])
            )
            after['Uffici Assegnatari per Conoscenza'] = self.set_after(after['Uffici Assegnatari per Conoscenza'], 'Uffici Assegnatari per Conoscenza',
                ', '.join([aw.department_id.name for aw in wizard.assegnatari_conoscenza_uffici_ids])
            )
            self._salva_assegnatari_ufficio(cr, uid, protocollo.id,
                                            protocollo.assegnatari_conoscenza_uffici_ids,
                                            wizard.assegnatari_conoscenza_uffici_ids, 'conoscenza')

        if not protocollo.reserved:
            before['Dipendenti Assegnatari per Conoscenza'] = self.set_before(before['Dipendenti Assegnatari per Conoscenza'], 'Dipendenti Assegnatari per Conoscenza',
                ', '.join([a.dipendente_id.name for a in protocollo.assegnatari_conoscenza_dipendenti_ids])
            )
            after['Dipendenti Assegnatari per Conoscenza'] = self.set_after(after['Dipendenti Assegnatari per Conoscenza'], 'Dipendenti Assegnatari per Conoscenza',
                ', '.join([aw.dipendente_id.name for aw in wizard.assegnatari_conoscenza_dipendenti_ids])
            )
            self._salva_assegnatari_dipendente(cr, uid, protocollo.id,
                                            protocollo.assegnatari_conoscenza_dipendenti_ids,
                                            wizard.assegnatari_conoscenza_dipendenti_ids, 'conoscenza')

        action_class = "history_icon update"
        body = "<div class='%s'><ul>" % action_class
        for key, before_item in before.items():
            if before[key] != after[key]:
                body = body + "<li>%s: <span style='color:#990000'> %s</span> -> <span style='color:#009900'> %s </span></li>" \
                                % (str(key), str(before_item), str(after[key]))
            else:
                body = body + "<li>%s: <span style='color:#999'> %s</span> -> <span style='color:#999'> %s </span></li>" \
                                % (str(key), str(before_item), str(after[key]))

        protocollo_obj.write(cr, uid, [context['active_id']], vals)
        body += "</ul></div>"

        post_vars = {'subject': "Modifica assegnatari: \'%s\'" % wizard.cause,
                     'body': body,
                     'model': "protocollo.protocollo",
                     'res_id': context['active_id'],
                    }

        new_context = dict(context).copy()
        # if protocollo.typology.name == 'PEC':
        new_context.update({'pec_messages': True})

        thread_pool = self.pool.get('protocollo.protocollo')
        thread_pool.message_post(cr, uid, context['active_id'], type="notification", context=new_context, **post_vars)

        return {'type': 'ir.actions.act_window_close'}


class protocollo_assegna_ufficio_wizard(osv.TransientModel):
    _name = 'protocollo.assegna.ufficio.wizard'

    def on_change_department_id(self, cr, uid, ids, department_id, context=None):
        dipendente_ids = []
        if department_id:
            department_obj = self.pool.get('hr.department')
            department = department_obj.browse(cr, uid, department_id)
            for dipendente_id in department.member_ids:
                dipendente_ids.append((0, 0, {'dipendente_id': dipendente_id}))
        return {'value': {'assegnatari_dipendenti_ids': dipendente_ids}}

    _columns = {
        'competenza_uffici_wizard_id': fields.many2one('protocollo.assegna.wizard'),
        'conoscenza_uffici_wizard_id': fields.many2one('protocollo.assegna.wizard'),

        'protocollo_assegnatario_ufficio_id': fields.many2one('protocollo.assegnatario.ufficio'),

        'department_id': fields.many2one('hr.department', 'Ufficio', required=True),

        'assegnatari_dipendenti_ids': fields.one2many('protocollo.assegna.dipendente.wizard', 'ufficio_assegnatario_id', 'Dipendenti'),
    }


class protocollo_assegna_dipendente_wizard(osv.TransientModel):
    _name = 'protocollo.assegna.dipendente.wizard'
    _columns = {
        'ufficio_assegnatario_id': fields.many2one('protocollo.assegna.ufficio.wizard'),

        'competenza_dipendenti_wizard_id': fields.many2one('protocollo.assegna.wizard'),
        'conoscenza_dipendenti_wizard_id': fields.many2one('protocollo.assegna.wizard'),

        'protocollo_assegnatario_dipendente_id': fields.many2one('protocollo.assegnatario.dipendente'),

        'dipendente_id': fields.many2one('hr.employee', 'Dipendente', required=True),
        'state': fields.selection(STATE_ASSEGNATARIO_SELECTION, 'Stato', readonly=True),
    }