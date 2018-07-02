# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp import tools


class res_users(osv.Model):
    _inherit = "res.users"

    def on_change_login(self, cr, uid, ids, login, context=None):
        if login and not tools.single_email_re.match(login):
            raise osv.except_osv(_('Warning!'), _('Devi inserire un indirizzo e-mail valido'))
        else:
            return {'value': {'email': login}}

    def create(self, cr, uid, vals, context=None):
        if 'login' in vals and tools.single_email_re.match(vals.get('login')):
            user_id = super(res_users, self).create(cr, uid, vals, context=context)
            return user_id
        else:
            raise osv.except_osv(_('Warning!'), _('Devi inserire un indirizzo e-mail valido'))

    def write(self, cr, uid, ids, values, context=None):
        if 'login' in values:
            if tools.single_email_re.match(values.get('login')) is None:
                raise osv.except_osv(_('Warning!'), _('Devi inserire un indirizzo e-mail valido'))
        res = super(res_users, self).write(cr, uid, ids, values, context=context)
        return res



class protocollo_classification(osv.Model):
    _name = 'protocollo.classification'

    # def name_get(self, cr, uid, ids, context=None):
    #     if isinstance(ids, (list, tuple)) and not len(ids):
    #         return []
    #     if isinstance(ids, (long, int)):
    #         ids = [ids]
    #     reads = self.read(cr, uid, ids, ['name', 'parent_id'], context=context)
    #     res = []
    #     for record in reads:
    #         name = record['name']
    #         if record['parent_id']:
    #             name = record['parent_id'][1] + ' / ' + name
    #         res.append((record['id'], name))
    #
    #     return res

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            if record['code']:
                name = record['code'] + ' - ' + record['name']
            else:
                name = record['name']
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    def _name_and_code_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        classification_obj = self.pool.get('protocollo.classification')
        res = []
        for classification in classification_obj.browse(cr, uid, ids, context=context):
            if classification.code:
                res.append((classification.id, classification.code + " - " + classification.name))
            else:
                res.append((classification.id, classification.name))
        return dict(res)


    _columns = {
        'name': fields.char(
            'Nome', size=256, required=True),
        'parent_id': fields.many2one(
            'protocollo.classification',
            'Padre'),
        'child_ids': fields.one2many(
            'protocollo.classification',
            'parent_id',
            'Children'),
        'complete_name': fields.function(
            _name_get_fnc,
            type="char",
            string='Nome Completo'),
        'name_and_code': fields.function(
            _name_and_code_get_fnc,
            type="char",
            string='Codice e Nome'),
        'description': fields.text('Descrizione'),
        'code': fields.char(
            'Codice Titolario',
            char=16,
            required=False),
        'class_type': fields.selection(
            [
                ('titolo', 'Titolo'),
                ('classe', 'Classe'),
                ('sottoclasse', 'Sottoclasse'),
            ],
            'Tipologia',
            size=32,
            required=True,
            ),
        'dossier_ids': fields.one2many(
            'protocollo.dossier',
            'classification_id',
            'Fascicoli',
        ),
        'sequence': fields.integer('Ordine di visualizzazione', help="Sequence"),
    }

    _default = {
        'sequence': 10
    }
    # _defaults = {
    #     'name_and_code': _name_get_fnc
    # }


class protocollo_dossier(osv.Model):
    _name = 'protocollo.dossier'

    DOSSIER_TYPE = {
        'fascicolo': 'Fascicolo',
        'sottofascicolo': 'Sottofascicolo',
        'inserto': 'Inserto',
    }

    PARENT_TYPE = {
        'fascicolo': False,
        'sottofascicolo': 'fascicolo',
        'inserto': 'sottofascicolo'
    }

    DOSSIER_TYPOLOGY = {
        'procedimento': 'Procedimento Amministrativo',
        'affare': 'Affare',
        'attivita': 'Attivita\'',
        'fisica': 'Persona Fisica',
        'giuridica': 'Persona Giuridica',
    }

    def on_change_dossier_type_classification(
            self, cr, uid, ids,
            dossier_type, classification_id, parent_id, context=None):
        name = ''
        if parent_id and dossier_type != 'fascicolo':
            parent = self.pool.get('protocollo.dossier').browse(
                cr, uid, parent_id, context=context)
            classification_id = parent.classification_id.id
            num = len(parent.child_ids) + 1
            name = '<' + self.DOSSIER_TYPE[dossier_type] + ' N.' + \
                str(num) + ' del "' + \
                parent.name + '">'
        elif dossier_type and dossier_type in self.DOSSIER_TYPE and \
                classification_id:
            classification = self.pool.get('protocollo.classification').\
                browse(cr, uid, classification_id, context=context)
            num = len(classification.dossier_ids)
            name = '<' + self.DOSSIER_TYPE[dossier_type] + ' N.' + \
                str(num) + ' del \'' + \
                classification.name + '\'>'
            if dossier_type == 'fascicolo':
                parent_id = False
        parent_type = self.PARENT_TYPE[dossier_type]
        values = {
            'name': name,
            'classification_id': classification_id,
            'parent_id': parent_id,
            'parent_type': parent_type
        }
        return {'value': values}

    def _parent_type(self, cr, uid, ids, name, arg, context=None):
        if not context:
            context = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = {}
        for dossier in self.browse(cr, uid, ids):
            res[dossier.id] = dossier.dossier_type and \
                self.PARENT_TYPE[dossier.dossier_type] or \
                None
        return res

    _columns = {
        'name': fields.char(
            'Codice Fascicolo',
            size=256,
            required=True,
            readonly=False,
        ),
        'description': fields.text(
            'Oggetto',
            required=True,
            readonly=True,
            states={'draft':
                    [('readonly', False)]
                    }
        ),
        'classification_id': fields.many2one(
            'protocollo.classification',
            'Rif. Titolario',
            required=True,
            readonly=True,
            states={'draft':
                    [('readonly', False)]
                    }),
        'year': fields.char(
            'Anno',
            size=4,
            readonly=True
        ),
        'user_id': fields.many2one(
            'res.users',
            'Responsabile',
            readonly=True
        ),
        'dossier_type': fields.selection(
            DOSSIER_TYPE.items(),
            'Tipo',
            size=32,
            required=True,
            readonly=True,
            states={'draft':
                    [('readonly', False)]
                    }
            ),
        'dossier_typology': fields.selection(
            DOSSIER_TYPOLOGY.items(),
            'Tipologia',
            size=32,
            required=True,
            readonly=True,
            states={'draft':
                    [('readonly', False)]
                    }
            ),
        'date_open': fields.datetime(
            'Data Apertura',
            readonly=True
        ),
        'date_close': fields.datetime(
            'Data Chiusura',
            readonly=True
        ),
        'rel_dossier_id': fields.many2one(
            'protocollo.dossier',
            'Fascicolo Correlato',
            ),
        'parent_id': fields.many2one(
            'protocollo.dossier',
            'Fascicolo di Riferimento',
            readonly=True,
            domain=[('dossier_type', 'in', ('fascicolo', 'sottofascicolo'))],
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
        ),
        'child_ids': fields.one2many(
            'protocollo.dossier',
            'parent_id',
            'Sottofascicoli',
            readonly=True,
        ),
        'parent_type': fields.function(
            _parent_type,
            string='Tipo Padre',
            type='selection',
            selection=DOSSIER_TYPE.items(),
            store=False,
        ),
        'partner_id': fields.many2one(
            'res.partner',
            'Anagrafica Correlata',
            readonly=True,
            states={'draft':
                    [('readonly', False)]
                    }
        ),
        'owner_partner_id': fields.many2one(
            'res.partner',
            'Amministrazione Titolare',
            required=False,
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
        ),
        'participant_partner_ids': fields.many2many(
            'res.partner',
            'dossier_participant_rel',
            'dossier_id', 'partner_id',
            'Amministrazioni Partecipanti',
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
        ),
        'office_comp_ids': fields.many2many(
            'hr.department',
            'dossier_office_comp_rel',
            'dossier_id', 'office_id',
            'Uffici Competenti',
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
            ),
        'office_view_ids': fields.many2many(
            'hr.department',
            'dossier_office_view_rel',
            'dossier_id', 'office_id',
            'Uffici Interessati',
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
            ),
        'employee_comp_ids': fields.many2many(
            'hr.employee',
            'dossier_employee_comp_rel',
            'dossier_id', 'employee_id',
            'Utenti Competenti',
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
            ),
        'employee_view_ids': fields.many2many(
            'hr.employee',
            'dossier_employee_view_rel',
            'dossier_id', 'employee_id',
            'Utenti Interessati',
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
            ),
        # Documents
        'document_ids': fields.many2many(
            'gedoc.document',
            'dossier_document_rel',
            'dossier_id', 'document_id',
            'Documenti Allegati al Fascicolo',
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    'open':
                    [('readonly', False)],
                    }
            ),
        'notes': fields.text('Note'),
        'state': fields.selection(
            [('draft', 'Bozza'),
             ('open', 'Aperto'),
             ('closed', 'Chiuso')],
            'Stato',
            readonly=True,
            help="Lo stato del fascicolo.",
            select=True,
            ),
        # TODO: verify congruence of the next fields.
        'paperless': fields.boolean(
            'Non contiene documenti cartacei',
            readonly=True,
            states={'draft':
                    [('readonly', False)],
                    }
            ),
        'address': fields.char(
            'Posizione',
            help="Indirizzo posizione fisica documenti cartacei"),
        'building': fields.char(
            'Edificio',
            help="Edificio di conservazione dei documenti cartacei"),
        'floor': fields.char(
            'Piano',
            help="Piano in cui si trovano i documenti cartacei"),
        'room': fields.char(
            'Stanza',
            help="Stanza in cui si trovano i documenti cartacei"),
    }

    _defaults = {
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
        'dossier_type': 'fascicolo',
        'dossier_typology': 'procedimento',
    }

    # _sql_constraints = [
    #     ('dossier_name_unique',
    #      'unique (name)',
    #      'Elemento presente nel DB!'),
    #     ]

    def is_document_present(self, cr, uid, ids, *args):
        for dossier in self.browse(cr, uid, ids):
            if len(dossier.document_ids):
                return True
        return False

    def action_open(self, cr, uid, ids, *args):
        for dossier in self.browse(cr, uid, ids):
            if dossier.parent_id:
                num = len(
                    [d.id for d in dossier.parent_id.child_ids
                     if d.state in ('open', 'closed')]
                ) + 1
                name = self.DOSSIER_TYPE[dossier.dossier_type] + \
                    ' N.' + str(num) + ' del "' + \
                    dossier.parent_id.name + '"'
            else:
                num = len(
                    [d.id for d in dossier.classification_id.dossier_ids
                     if d.state in ('open', 'closed') and
                     d.dossier_type == 'fascicolo']
                ) + 1
                name = self.DOSSIER_TYPE[dossier.dossier_type] + \
                    ' N.' + str(num) + ' del \'' + \
                    dossier.classification_id.name + '\''
            date_open = fields.datetime.now()
            year = date_open[:4]
            vals = {
                'name': name,
                'state': 'open',
                'date_open': date_open,
                'year': year,
            }
            if dossier.dossier_type == 'fascicolo':
                vals['parent_id'] = False
            self.write(cr, uid, ids, vals)
        return True

    def action_close(self, cr, uid, ids, *args):
        vals = {
            'state': 'closed',
            'date_close': fields.datetime.now()
        }
        self.write(cr, uid, ids, vals)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if 'dossier_type' in vals and vals['dossier_type'] == 'fascicolo':
            vals['parent_id'] = False
        return super(protocollo_dossier, self).write(
            cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        stat = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for t in stat:
            if t['state'] in ('draft'):
                unlink_ids.append(t['id'])
            else:
                raise osv.except_osv(_('Azione Non Valida!'),
                                     _('Solo i fascicoli in stato \
                                     bozza possono essere eliminati.')
                                     )
        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return super(protocollo_dossier, self).unlink(
            cr, uid, unlink_ids, context=context)

    def copy(self, cr, uid, fid, default=None, context=None):
        raise osv.except_osv(_('Azione Non Valida!'),
                             _('Impossibile duplicare un fascicolo')
                             )
        return True


class gedoc_model_type(osv.Model):
    _name = 'gedoc.model.type'

    _columns = {
        'name': fields.char(
            'Tipo Modello Documento',
            size=512,
            required=True
        ),
        'description': fields.char(
            'Descrizione Tipo Modello Documento',
            size=512,
            required=True
        ),
    }


class gedoc_document_type(osv.Model):
    _name = 'gedoc.document.type'

    _columns = {
        'name': fields.char(
            'Tipo Documento',
            size=512,
            required=True
        ),
        'tipologia_repertorio': fields.selection(
            [
                ('none', 'Non repertoriato'),
                ('manual', 'Numerazione Manuale'),
                ('automatic', 'Numerazione Automatica')
            ],
            'Tipologia Repertorio',
            size=32,
            required=True,
        ),
        'repertorio_sequence': fields.many2one('ir.sequence', 'Sequenza Numerazione', readonly=True)
    }

    def create(self, cr, uid, vals, context=None):
        document_type_id = super(gedoc_document_type, self).create(cr, uid, vals, context=context)
        if vals['tipologia_repertorio'] == 'automatic':
            document_type = self.browse(cr, uid, document_type_id)
            seq_id = self._create_repertorio_sequence(cr, uid, document_type.id, document_type.name)
            self.write(cr, uid, [document_type.id], {'repertorio_sequence': seq_id})
        return document_type_id

    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key('tipologia_repertorio') and vals['tipologia_repertorio'] == 'automatic':
            document_type = self.browse(cr, uid, ids[0])
            if not document_type.repertorio_sequence:
                seq_id = self._create_repertorio_sequence(cr, uid, document_type.id, document_type.name)
                vals['repertorio_sequence'] = seq_id
        document_type_id = super(gedoc_document_type, self).write(cr, uid, ids, vals, context=context)
        return document_type_id

    def _create_repertorio_sequence(self, cr, uid, document_type_id, document_type_name):
        sequence_type_obj = self.pool.get('ir.sequence.type')
        sequence_type_code = 'repertorio.sequence.' + str(document_type_id)
        sequence_type_obj.create(cr, SUPERUSER_ID, {
            'name': 'Sequence Repertorio ' + document_type_name,
            'code': sequence_type_code
        })
        sequence_obj = self.pool.get('ir.sequence')
        sequence_vals = {}
        sequence_vals['name'] = 'Repertorio - ' + document_type_name
        sequence_vals['code'] = sequence_type_code
        sequence_vals['active'] = True
        sequence_vals['suffix'] = '/%(year)s'
        sequence_vals['number_next'] = 1
        sequence_vals['number_increment'] = 1
        sequence_vals['padding'] = 0
        seq_id = sequence_obj.create(cr, SUPERUSER_ID, sequence_vals, context={})
        return seq_id

    def unlink(self, cr, uid, ids, context=None):
        rep = self.browse(cr, uid, ids, context=context)
        sequence_obj = self.pool.get('ir.sequence')
        sequence_type_obj = self.pool.get('ir.sequence.type')
        seq_id = rep.repertorio_sequence.id
        seq_code = rep.repertorio_sequence.code
        res = super(gedoc_document_type, self).unlink(cr, uid, ids, context=context)
        if res:
            seq_type = sequence_type_obj.search(cr, uid, [('code', '=', seq_code)])
            sequence_type_obj.unlink(cr, SUPERUSER_ID, seq_type)
            sequence_obj.unlink(cr, SUPERUSER_ID, seq_id)
        return True


class gedoc_document(osv.Model):
    _name = 'gedoc.document'

    _columns = {
        'name': fields.char(
            'Documento',
            size=512,
            required=True
        ),
        'document_type': fields.many2one(
            'gedoc.document.type',
            'Tipologia Documento',
            required=False
        ),
        'repertorio': fields.selection(
                        [('none', 'Non repertoriato'),
                        ('manual', 'Numerazione Manuale'),
                        ('automatic', 'Numerazione Automatica')],
                        string='Tipologia Repertorio', readonly=True),
        'numero_repertorio': fields.char(
            'Numero Repertorio',
            size=256,
            required=False
        ),
        'subject': fields.text(
            'Oggetto',
            required=True,
        ),
        'main_doc_id': fields.many2one(
            'ir.attachment',
            'Documento Principale',
            required=False,
            readonly=True,
            domain="[('res_model','=',\
            'gedoc.document')]",
        ),
        'user_id': fields.many2one(
            'res.users',
            'Proprietario',
            readonly=True,
        ),
        'data_doc': fields.datetime(
            'Data Caricamento',
            readonly=True,
        ),
        'office_comp_ids': fields.many2many(
            'hr.department',
            'document_office_comp_rel',
            'document_id', 'office_id',
            'Uffici Competenti',
            ),
        'office_view_ids': fields.many2many(
            'hr.department',
            'document_office_view_rel',
            'document_id', 'office_id',
            'Uffici Interessati',
            ),
        'employee_comp_ids': fields.many2many(
            'hr.employee',
            'document_employee_comp_rel',
            'document_id', 'employee_id',
            'Utenti Competenti',
            ),
        'employee_view_ids': fields.many2many(
            'hr.employee',
            'document_employee_view_rel',
            'document_id', 'employee_id',
            'Utenti Interessati',
            ),
        'dossier_ids': fields.many2many(
            'protocollo.dossier',
            'dossier_document_rel',
            'document_id', 'dossier_id',
            'Fascicoli'),
        'attachment_ids': fields.one2many('ir.attachment','res_id', 'Allegati', readonly=True, domain=[('res_model','=','gedoc.document')]),

    }

    _defaults = {
        'name': '<Nuovo Documento>',
        'user_id': lambda obj, cr, uid, context: uid,
     }

    def _get_sequence_code(self, cr, uid, document_type_id):
        document_type_obj = self.pool.get('gedoc.document.type')
        try:
            document_type = document_type_obj.browse(cr, uid, document_type_id)
            seq_id = document_type.repertorio_sequence.id
            sequence_code = self.pool.get('ir.sequence').get_id(cr, uid, seq_id)
        except:
            raise osv.except_osv(_('Si è verificato un problema nella numerazione di repertorio!'),
                                 _('Si prega di riprovare'))
        return sequence_code

    def create(self, cr, uid, vals, context=None):
        if vals.has_key('document_type') and vals['document_type']:
            document_type_obj = self.pool.get('gedoc.document.type')
            document_type = document_type_obj.browse(cr, uid, vals['document_type'])
            if document_type.tipologia_repertorio == 'automatic':
                vals['numero_repertorio'] = self._get_sequence_code(cr,uid,vals['document_type'])
            vals['repertorio'] = document_type.tipologia_repertorio
        document_id = super(gedoc_document, self).create(cr, uid, vals, context=context)
        return document_id

    def on_change_document_type(self, cr, uid, ids, document_type_id, context=None):
        document_type_obj = self.pool.get('gedoc.document.type')
        document_type = document_type_obj.browse(cr, uid, document_type_id)
        values = {
            'repertorio': document_type.tipologia_repertorio
        }
        return {'value': values}


class DocumentSearch(osv.TransientModel):
    """
        Advanced Document Search
    """
    _name = 'gedoc.document.search'
    _description = 'Document Search'

    def _get_models(self, cr, uid, context=None):
        if context is None:
            context = {}
        model_obj = self.pool.get('gedoc.model.type')
        model_ids = model_obj.search(
            cr,
            uid,
            [],
            context=context
        )
        res = []
        for model in model_obj.browse(cr, uid, model_ids, context=context):
            res.append((model.name, model.description))
        return res

    _columns = {
        'name': fields.selection(
            _get_models,
            'Tipologia Documento',
            size=32,
            required=True,
            ),
        'text_name': fields.char(
            'Nome'
        ),
        'subject': fields.char(
            'Oggetto'
        ),
        'dossier_id': fields.many2one(
            'protocollo.dossier',
            'Fascicolo'
        ),
        'classification_id': fields.many2one(
            'protocollo.classification',
            'Titolario'
        ),
        'partner_id': fields.many2one(
            'res.partner',
            'Anagrafica'
        ),
        'user_id': fields.many2one(
            'res.users',
            'Responsabile / Proponente',
        ),
        'index_content': fields.char(
            'Contenuto nel Documento'
        ),
        'date_close_start': fields.datetime(
            'Inizio'
        ),
        'date_close_end': fields.datetime(
            'Fine'
        ),
        'office_id': fields.many2one(
            'hr.department',
            'Ufficio Competente'
        ),
        # Documents
        'document_type': fields.many2one(
            'gedoc.document.type',
            'Tipologia Documento',
        ),
     }

    def _search_action_document(
            self, cr, uid, wizard,
            search_domain, context=None):
        if wizard.name == 'gedoc.document':
            if wizard.text_name:
                search_domain.append(('name', 'ilike', wizard.text_name))
            if wizard.subject:
                search_domain.append(('subject', 'ilike', wizard.subject))
            if wizard.date_close_start:
                search_domain.append(
                    ('data_doc',
                     '>=',
                     wizard.date_close_start)
                    )
            if wizard.date_close_end:
                search_domain.append(
                    ('data_doc',
                     '<=',
                     wizard.date_close_end)
                    )
            if wizard.partner_id:
                search_domain.append(
                    ('partner_id', '=', wizard.partner_id))
            return search_domain
        else:
            return search_domain

    def search_action(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        content_ids = []
        # First we search for index_content
        if wizard.index_content and len(wizard.index_content) > 2:
            query = """
                SELECT DISTINCT res_id
                FROM ir_attachment
                WHERE
                res_model=%s
                AND
                index_content ilike %s
                ORDER BY res_id ASC
            """
            cr.execute(query, (wizard.name, '%' + wizard.index_content + '%'))
            content_ids = map(lambda x: x[0], cr.fetchall())
        search_domain = []
        record_obj = self.pool.get(wizard.name)
        if wizard.dossier_id:
            search_domain.append(('dossier_ids', 'in', [wizard.dossier_id.id]))
        if wizard.user_id:
            search_domain.append(('user_id', '=', wizard.user_id))
        search_domain = self._search_action_document(
            cr, uid, wizard, search_domain, context)
        if search_domain:
            res_domain = record_obj.search(
                cr,
                uid,
                search_domain,
                context=context
                )
        else:
            res_domain = []
        if not isinstance(res_domain, list):
            res_domain = [res_domain]
        if content_ids:
            res_domain = list(set(content_ids) & set(res_domain))
        text_domain = "0"
        if res_domain:
            text_domain = ','.join(map(str, res_domain))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ricerca Avanzata ' + dict(
                self._get_models(cr, uid, context=context))[wizard.name],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': "[('id', 'in', (%s,))]" % text_domain,
            'res_model': wizard.name,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
