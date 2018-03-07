# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp import tools

class protocollo_classification(osv.Model):
    _inherit = 'protocollo.classification'

    _columns = {
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
    }

    def _get_default_aoo_id(self, cr, uid, context=None):
        if context and context.has_key('aoo_id') and context['aoo_id']:
            return context['aoo_id']
        else:
            aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [], context=context)
            if len(aoo_ids) > 0:
                return aoo_ids[0]
        return False

    _defaults = {
        'aoo_id': _get_default_aoo_id,
    }


class protocollo_dossier(osv.Model):
    _inherit = 'protocollo.dossier'
    _columns = {
        'protocollo_ids': fields.many2many(
            'protocollo.protocollo',
            'dossier_protocollo_rel',
            'dossier_id', 'protocollo_id',
            'Protocolli Allegati al Fascicolo',
            readonly=True,
            states={'draft':
                        [('readonly', False)],
                    'open':
                        [('readonly', False)],
                    }
        ),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True),
    }

    def _get_default_aoo_id(self, cr, uid, context=None):
        if context and context.has_key('aoo_id') and context['aoo_id']:
            return context['aoo_id']
        else:
            aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [], context=context)
            if len(aoo_ids) > 0:
                return aoo_ids[0]
        return False

    _defaults = {
        'aoo_id': _get_default_aoo_id,
    }

    def is_document_present(self, cr, uid, ids, *args):
        for dossier in self.browse(cr, uid, ids):
            if len(dossier.protocollo_ids):
                return True
        return super(protocollo_dossier, self). \
            is_document_present(cr, uid, ids, *args)

    def create(self, cr, uid, vals, context=None):
        if 'is_demo' in context and context['is_demo']:
            dossier_type = vals['dossier_type']
            classification_id = vals['classification_id']
            # aoo_id = vals['classification_id']
            # aoo_obj = self.pool.get('protocollo.aoo').browse(cr, uid, aoo_id)

            if vals['name'] and dossier_type and dossier_type in self.DOSSIER_TYPE and classification_id:
                classification = self.pool.get('protocollo.classification').\
                    browse(cr, uid, classification_id, context=context)
                num = len(classification.dossier_ids)
                vals['name'] = '<' + '-' + self.DOSSIER_TYPE[dossier_type] + ' N.' + \
                    str(num) + ' del \'' + \
                    classification.name + '\' >'

        dossier_id = super(protocollo_dossier, self).create(cr, uid, vals, context=context)
        return dossier_id

class DocumentSearch(osv.TransientModel):
    """
        Advanced Document Search
    """
    _inherit = 'gedoc.document.search'

    def _search_action_document(
            self, cr, uid, wizard,
            search_domain, context=None):
        if wizard.name == 'protocollo.protocollo':
            if wizard.text_name:
                search_domain.append(('name', 'ilike', wizard.text_name))
            if wizard.subject:
                search_domain.append(('subject', 'ilike', wizard.subject))
            if wizard.classification_id:
                search_domain.append(
                    ('classification', '=', wizard.classification_id.id))
            if wizard.partner_id:
                search_domain.append(
                    ('sender_receivers',
                     'ilike',
                     wizard.partner_id.name)
                )
            if wizard.office_id:
                search_domain.append(
                    ('assigne',
                     'in',
                     [wizard.office_id.id])
                )
            if wizard.date_close_start:
                search_domain.append(
                    ('registration_date',
                     '>=',
                     wizard.date_close_start)
                )
            if wizard.date_close_end:
                search_domain.append(
                    ('registration_date',
                     '<=',
                     wizard.date_close_end)
                )
            return search_domain
        else:
            return search_domain

class documento_protocollato(osv.osv):
    _name = "documento.protocollato"
    _auto = False
    _order = 'protocol_registration_date desc'

    _columns = {
        'doc_id': fields.many2one('ir.attachment', 'Allegato', readonly=True),
        'protocol_id': fields.many2one('protocollo.protocollo', 'Protocollo', readonly=True),
        'protocol_subject': fields.char('Oggetto', readonly=True),
        'doc_protocol_preview': fields.related('doc_id', 'datas', type='binary', string='Anteprima documento', readonly=True),
        'doc_protocol_download': fields.related('doc_id', 'datas', type='binary', string='Download documento', readonly=True),
        'doc_is_main': fields.related('doc_id', 'is_main', type='boolean', string='Documento principale', readonly=True),
        'doc_is_pdf': fields.related('doc_id', 'is_pdf', type='boolean', string='PDF', readonly=True),
        'doc_name': fields.char('Nome documento', readonly=True),
        'doc_description': fields.char('Descrizione documento', readonly=True),
        'protocol_name': fields.char('Numero Protocollo', readonly=True),
        'protocol_registration_date': fields.char('Data Registrazione', readonly=True),
        'protocol_doc_id': fields.integer('Documento principale', readonly=True),
        'doc_index_content': fields.text('Contenuto indicizzato', readonly=True),
        'doc_file_type': fields.char('Tipo di file', readonly=True),
        'protocol_state': fields.char('Stato Protocollo', readonly=True),
        'protocol_state_related': fields.related('protocol_id', 'state', type='char', string='Stato Protocollo Related', readonly=True),
        'is_visible': fields.related('protocol_id', 'is_visible', type='boolean', string='Visibile', readonly=True),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'documento_protocollato')
        cr.execute("""
            CREATE view documento_protocollato as
              (
                SELECT
                    a.id,
                    a.id as doc_id,
                    a.name as doc_name, 
                    a.datas_description as doc_description,
                    a.index_content as doc_index_content,
                    a.file_type as doc_file_type,
                    p.id as protocol_id,
                    p.name as protocol_name, 
                    p.subject as protocol_subject,
                    p.registration_date as protocol_registration_date, 
                    p.doc_id as protocol_doc_id, 
                    p.state as protocol_state,
                    p.type,
                    t.name
                FROM ir_attachment a 
                JOIN protocollo_protocollo p
                  ON a.res_id = p.id
                JOIN protocollo_typology t
                  ON p.typology = t.id
                WHERE a.res_model = 'protocollo.protocollo'
                
              )
              
        """)
