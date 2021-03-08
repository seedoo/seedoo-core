# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
import werkzeug

from openerp import SUPERUSER_ID, tools, api
from openerp.osv import orm, fields, osv
from openerp.tools.translate import _
from util.selection import *
import logging

_logger = logging.getLogger(__name__)

EMPLOYEE_MASK = 100000000
DEPARTMENT_MASK = 200000000

class protocollo_assegnatario(osv.osv):
    _name = 'protocollo.assegnatario'
    _auto = False
    _rec_name = 'nome'

    def _dept_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.complete_name_get(cr, uid, ids, context=context)
        return dict(res)

    def _name_search_fnc(self, cr, uid, obj, name, args, domain=None, context=None):
        new_args = []
        for arg in args:
            new_arg = list(arg)
            if new_arg[0] == 'name':
                new_arg[0] = 'nome'
            new_args.append(new_arg)
        return new_args

    def _get_child_ids(self, cr, uid, assegnatario):
        res = []
        for child in assegnatario.child_ids:
            res.append(child.id)
            child_res = self._get_child_ids(cr, uid, child)
            res = res + child_res
        return res

    def _get_assegnatario_not_visibile_ids(self, cr, uid):
        assegnatario_not_visible_ids = []
        assegnatario_not_active_ids = self.search(cr, uid, [
            '|', '|',
            ('active', '=', False),
            '&', ('tipologia', '=', 'employee'), ('parent_id', '=', False),
            '&', ('tipologia', '=', 'department'), ('aoo_id', '=', False)
        ])
        for assegnatario_not_active_id in assegnatario_not_active_ids:
            if not (assegnatario_not_active_id in assegnatario_not_visible_ids):
                assegnatario_not_visible_ids.append(assegnatario_not_active_id)
                assegnatario_not_active = self.browse(cr, uid, assegnatario_not_active_id)
                assegnatario_not_visible_ids += self._get_child_ids(cr, uid, assegnatario_not_active)
        return assegnatario_not_visible_ids

    def _is_visible(self, cr, uid, ids, name, arg, context=None):
        res = []
        assegnatario_not_visible_ids = self._get_assegnatario_not_visibile_ids(cr, uid)
        for id in ids:
            if id in assegnatario_not_visible_ids:
                res.append((id, False))
            else:
                res.append((id, True))
        return dict(res)

    def _is_visible_search(self, cr, uid, obj, name, args, domain=None, context=None):
        assegnatario_not_visible_ids = self._get_assegnatario_not_visibile_ids(cr, uid)
        return [('id', 'not in', assegnatario_not_visible_ids)]

    def _no_checkbox_get_fnc(self, cr, uid, ids, prop, unknow_none, context={}):
        if context is None:
            context = {}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]

        reserved = False
        if context.has_key('reserved'):
            reserved = context['reserved']

        prima_assegnazione = context.get('prima_assegnazione', False)
        configurazione_assegnazione = self.pool.get('protocollo.configurazione').get_configurazione_assegnazione(cr, uid, prima_assegnazione)

        reads = self.read(cr, uid, ids, ['tipologia', 'child_ids'], context=context)
        res = []
        for record in reads:
            no_checkbox = False
            if reserved:
                if record['tipologia']=='department':
                    no_checkbox = True
            else:
                if record['tipologia']=='department':
                    if configurazione_assegnazione=='employee' or not record['child_ids']:
                        no_checkbox = True
                    else:
                        employee_found = False
                        for child_id in record['child_ids']:
                            if child_id < DEPARTMENT_MASK:
                                employee_found = True
                                break
                        if not employee_found:
                            no_checkbox = True
                elif record['tipologia']=='employee':
                    if configurazione_assegnazione=='department':
                        no_checkbox = True
            res.append((record['id'], no_checkbox))
        return res

    _columns = {
        'complete_name': fields.function(_dept_name_get_fnc, fnct_search=_name_search_fnc, type='char', string='Name'),
        'nome': fields.char('Nome', size=512, readonly=True),
        'tipologia': fields.selection(TIPO_ASSEGNATARIO_SELECTION, 'Tipologia', readonly=True),
        'employee_id': fields.many2one('hr.employee', 'Dipendente', readonly=True),
        'department_id': fields.many2one('hr.department', 'Dipartimento', readonly=True),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', readonly=True),
        'parent_id': fields.many2one('protocollo.assegnatario', 'Ufficio di Appartenenza', readonly=True),
        'active': fields.boolean(string='Attivo'),
        'child_ids': fields.one2many('protocollo.assegnatario', 'parent_id', 'Figli'),
        'no_checkbox': fields.function(_no_checkbox_get_fnc, type='boolean', string='No Checkbox'),
        'is_visible': fields.function(_is_visible, fnct_search=_is_visible_search, type='boolean', string='Visibile'),
    }

    def complete_name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['nome', 'parent_id'], context=context)
        res = []
        for record in reads:
            name = record['nome']
            if record['parent_id']:
                parent_reads = self.read(cr, uid, [record['parent_id'][0]], ['complete_name'], context=context)
                name = parent_reads[0]['complete_name']+' / '+name
            res.append((record['id'], name))
        return res

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'protocollo_assegnatario')
        cr.execute("""
            CREATE view protocollo_assegnatario as
              (
                SELECT
                  %s + e.id AS id,
                  e.name_related AS nome,
                  'employee' AS tipologia,
                  e.id AS employee_id,
                  NULL AS department_id,
                  NULL AS aoo_id,
                  %s + e.department_id AS parent_id,
                  r.active AS active
                FROM hr_employee e, resource_resource r
                WHERE e.resource_id=r.id
              )
              UNION
              (
                SELECT 
                  %s + d.id AS id,
                  d.name AS nome,
                  'department' AS tipologia,
                  NULL AS employee_id,
                  d.id AS department_id,
                  d.aoo_id AS aoo_id,
                  %s + d.parent_id AS parent_id,
                  d.active AS active
                FROM hr_department d
              )
        """, (EMPLOYEE_MASK, DEPARTMENT_MASK, DEPARTMENT_MASK, DEPARTMENT_MASK))


class protocollo_assegnazione(orm.Model):
    _name = 'protocollo.assegnazione'
    _description = 'Assegnazione Protocollo'
    _order = 'tipologia_assegnazione,create_date'

    _rec_name = 'assegnatario_id'

    _columns = {
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo', ondelete='cascade'),
        'assegnatario_id': fields.many2one('protocollo.assegnatario', 'Assegnatario'),
        'assegnatario_name': fields.char('Assegnatario', size=512),
        'tipologia_assegnatario': fields.selection(TIPO_ASSEGNATARIO_SELECTION, string='Tipologia Assegnatario'),

        # campi per tipologia assegnatario 'employee'
        'assegnatario_employee_id': fields.many2one('hr.employee', 'Assegnatario (Dipendente)'),
        'assegnatario_employee_department_id': fields.many2one('hr.department', 'Assegnatario (Ufficio del Dipendente)'),

        # campi per tipologia assegnatario 'department'
        'assegnatario_department_id': fields.many2one('hr.department', 'Assegnatario (Ufficio)'),
        'assegnatario_department_parent_id': fields.many2one('hr.department', 'Assegnatario (Ufficio Padre)'),

        'tipologia_assegnazione': fields.selection(TIPO_ASSEGNAZIONE_SELECTION, 'Tipologia Assegnazione'),
        'state': fields.selection(STATE_ASSEGNATARIO_SELECTION, 'Stato'),

        'assegnatore_id': fields.many2one('hr.employee', 'Assegnatore'),
        'assegnatore_name': fields.char('Assegnatore', size=512),
        'assegnatore_complete_name': fields.char('Assegnatore', size=512),
        'assegnatore_department_id': fields.many2one('hr.department', 'Ufficio Assegnatore'),

        'parent_id': fields.many2one('protocollo.assegnazione', 'Assegnazione Ufficio', ondelete='cascade'),
        'child_ids': fields.one2many('protocollo.assegnazione', 'parent_id', 'Assegnazioni Dipendenti'),

        'motivazione_rifiuto': fields.text('Motivazione del Rifiuto'),

        'archivio_id': fields.many2one('protocollo.archivio', 'Archivio'),
    }

    # _sql_constraints = [
    #     ('protocollo_assegnazione_unique', 'unique(protocollo_id, assegnatario_id, tipologia_assegnazione)',
    #      'Protocollo e Assegnatario con già uno stato nel DB!'),
    # ]

    def delete_indexes(self, cr):
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_id\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_id')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_parent_id\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_parent_id')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_protocollo_id\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_protocollo_id')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_archivio_id\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_archivio_id')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnatario_emp\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipologia_assegnatario_emp')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnatario_dep\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipologia_assegnatario_dep')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipassegnatario_assemp_state\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipassegnatario_assemp_state')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipassegnatario_assdep_state\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipassegnatario_assdep_state')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipassegnatario_assempdep_state\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipassegnatario_assempdep_state')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnazione_com\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipologia_assegnazione_com')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnazione_con\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipologia_assegnazione_con')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologiaassegnazione_parent_state\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipologiaassegnazione_parent_state')

        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnatario_parent_null\'')
        if cr.fetchone():
            cr.execute('DROP INDEX idx_protocollo_assegnazione_tipologia_assegnatario_parent_null')

    def create_indexes(self, cr):
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_id
                ON public.protocollo_assegnazione
                USING btree
                (id);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_protocollo_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_protocollo_id
                ON public.protocollo_assegnazione
                USING btree
                (protocollo_id);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_parent_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_parent_id
                ON public.protocollo_assegnazione
                USING btree
                (parent_id);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_archivio_id\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_archivio_id
                ON public.protocollo_assegnazione
                USING btree
                (archivio_id);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnatario_emp\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipologia_assegnatario_emp
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnatario)
                WHERE tipologia_assegnatario = 'employee';
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnatario_dep\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipologia_assegnatario_dep
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnatario)
                WHERE tipologia_assegnatario = 'department';
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipassegnatario_assemp_state\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipassegnatario_assemp_state
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnatario, assegnatario_employee_id, state);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipassegnatario_assdep_state\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipassegnatario_assdep_state
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnatario, assegnatario_department_id, state);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipassegnatario_assempdep_state\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipassegnatario_assempdep_state
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnatario, assegnatario_employee_department_id, state);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnazione_com\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipologia_assegnazione_com
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnazione)
                WHERE tipologia_assegnazione = 'competenza';
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnazione_con\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipologia_assegnazione_con
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnazione)
                WHERE tipologia_assegnazione = 'conoscenza';
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologiaassegnazione_parent_state\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipologiaassegnazione_parent_state
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnazione, parent_id, state);
            """)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'idx_protocollo_assegnazione_tipologia_assegnatario_parent_null\'')
        if not cr.fetchone():
            cr.execute("""
                CREATE INDEX idx_protocollo_assegnazione_tipologia_assegnatario_parent_null
                ON public.protocollo_assegnazione
                USING btree
                (tipologia_assegnatario, parent_id)
                WHERE (tipologia_assegnatario = 'department' OR (tipologia_assegnatario = 'employee' AND parent_id IS NULL));
            """)

    def init(self, cr):
        self.create_indexes(cr)

    def _crea_assegnazione(self, cr, uid, protocollo_id, assegnatario_id, assegnatore_id, tipologia, parent_id=False, values={}):
        assegnatario_obj = self.pool.get('protocollo.assegnatario')
        assegnatario = assegnatario_obj.browse(cr, uid, assegnatario_id)
        assegnatore_obj = self.pool.get('hr.employee')
        assegnatore = assegnatore_obj.browse(cr, uid, assegnatore_id)
        assegnatore_name = assegnatore.name
        assegnatore_complete_name = assegnatore_name
        assegnatore_department = assegnatore.department_id if assegnatore.department_id else False
        while assegnatore_department and assegnatore_department.id:
            assegnatore_complete_name = assegnatore_department.name + ' / ' + assegnatore_complete_name
            assegnatore_department = assegnatore_department.parent_id

        vals = dict(values or {})
        vals['protocollo_id'] = protocollo_id
        vals['assegnatario_id'] = assegnatario.id
        vals['assegnatario_name'] = assegnatario.complete_name
        vals['tipologia_assegnatario'] = assegnatario.tipologia
        vals['tipologia_assegnazione'] = tipologia
        vals['state'] = 'assegnato'
        vals['assegnatore_id'] = assegnatore.id
        vals['assegnatore_name'] = assegnatore_name
        vals['assegnatore_complete_name'] = assegnatore_complete_name
        vals['assegnatore_department_id'] = assegnatore.department_id.id if assegnatore.department_id else False
        vals['parent_id'] = parent_id
        vals['archivio_id'] = self.pool.get('protocollo.archivio').search(cr, uid, [('is_current', '=', True)])[0]

        if assegnatario.tipologia == 'employee':
            vals['assegnatario_employee_id'] = assegnatario.employee_id.id
            vals['assegnatario_employee_department_id'] = assegnatario.employee_id.department_id.id if assegnatario.employee_id.department_id else False
        if assegnatario.tipologia == 'department':
            vals['assegnatario_department_id'] = assegnatario.department_id.id
            vals['assegnatario_department_parent_id'] = assegnatario.department_id.parent_id.id if assegnatario.department_id.parent_id.id else False

        assegnazione_id = self.create(cr, uid, vals, {'recompute': False})
        assegnazione = self.browse(cr, uid, assegnazione_id, {'skip_check': True})
        self.notifica_assegnazione(cr, uid, assegnazione)
        # il metodo refresh serve per invalidare la cache degli id memorizzati nell'oggetto assegnatario_obj: se non si
        # invalida la cache ad ogni creazione di un'assegnazione, si ricalcola il name anche per le assegnazione create
        # in precedenza, rallentando notevolmente il processo
        assegnatario_obj.refresh(cr, uid)
        return assegnazione_id


    def _crea_assegnazioni(self, cr, uid, protocollo_id, assegnatario_ids, assegnatore_id, tipologia, values={}):
        for assegnatario_id in assegnatario_ids:
            assegnazione_id = self._crea_assegnazione(cr, uid, protocollo_id, assegnatario_id,
                                                      assegnatore_id, tipologia, False, values)

            dipendente_assegnatario_ids = self.pool.get('protocollo.assegnatario').search(cr, uid, [
                ('parent_id', '=', assegnatario_id),
                ('tipologia', '=', 'employee')
            ])
            for dipendente_assegnatario_id in dipendente_assegnatario_ids:
                self._crea_assegnazione(cr, uid, protocollo_id, dipendente_assegnatario_id,
                                                          assegnatore_id, tipologia, assegnazione_id, values)


    def check_assegnazione_competenza(self, cr, uid, assegnatario_ids):
        if len(assegnatario_ids) > 1:
            raise orm.except_orm('Attenzione!', 'Non si possono inserire più assegnatari per competenza!')


    def get_assegnatario_to_create_ids(self, cr, uid, assegnatario_ids, old_assegnatario_ids, assegnatario_id_to_replace, context={}):
        if assegnatario_id_to_replace:
            return assegnatario_ids
        elif context and 'riassegna' in context:
            return assegnatario_ids
        else:
            return list(set(assegnatario_ids) - set(old_assegnatario_ids))


    def get_assegnatario_to_unlink_ids(self, cr, uid, assegnatario_ids, old_assegnatario_ids, assegnatario_id_to_replace, context={}):
        if assegnatario_id_to_replace:
            return [assegnatario_id_to_replace]
        elif context and 'riassegna' in context:
            return old_assegnatario_ids
        else:
            return list(set(old_assegnatario_ids) - set(assegnatario_ids))


    def salva_assegnazione_competenza(self, cr, uid, protocollo_id, assegnatario_ids, assegnatore_id, assegnatario_id_to_replace=False, values={}, context={}):
        import time
        time_start = time.time()
        if protocollo_id and assegnatore_id:

            self.check_assegnazione_competenza(cr, uid, assegnatario_ids)

            assegnazione_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnazione', '=', 'competenza'),
                ('parent_id', '=', False)
            ])

            assegnatario_to_create_ids = []
            assegnatario_to_unlink_ids = []

            if assegnazione_ids:
                old_assegnatari = self.read(cr, uid, assegnazione_ids, ['assegnatario_id'])
                old_assegnatario_ids = []
                for old_assegnatario in old_assegnatari:
                    old_assegnatario_ids.append(old_assegnatario['assegnatario_id'][0])

                assegnatario_to_create_ids = self.get_assegnatario_to_create_ids(cr, uid, assegnatario_ids, old_assegnatario_ids, assegnatario_id_to_replace, context)
                assegnatario_to_unlink_ids = self.get_assegnatario_to_unlink_ids(cr, uid, assegnatario_ids, old_assegnatario_ids, assegnatario_id_to_replace, context)
            else:
                assegnatario_to_create_ids = assegnatario_ids

            if assegnatario_to_unlink_ids:
                # eliminazione delle vecchie assegnazioni (eventuali figli vengono eliminati a cascata)
                assegnazione_to_unlink_ids = self.search(cr, uid, [
                    ('protocollo_id', '=', protocollo_id),
                    ('tipologia_assegnazione', '=', 'competenza'),
                    ('assegnatario_id', 'in', assegnatario_to_unlink_ids),
                    ('parent_id', '=', False)
                ])
                if assegnazione_to_unlink_ids:
                    self.unlink(cr, uid, assegnazione_to_unlink_ids, {'recompute': False})

            if assegnatario_to_create_ids:
                # creazione della nuova assegnazione
                self._crea_assegnazioni(cr, uid, protocollo_id, assegnatario_to_create_ids, assegnatore_id, 'competenza', values)

        time_end = time.time()
        time_duration = time_end - time_start
        _logger.debug("crea assegnazioni: %s sec" % (time_duration, ))


    def salva_assegnazione_conoscenza(self, cr, uid, protocollo_id, assegnatario_ids, assegnatore_id, delete=True):
        if protocollo_id and assegnatore_id:

            assegnazione_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnazione', '=', 'conoscenza'),
                ('parent_id', '=', False)
            ])

            assegnatario_to_create_ids = []
            assegnatario_to_unlink_ids = []

            if assegnazione_ids:
                old_assegnatari = self.read(cr, uid, assegnazione_ids, ['assegnatario_id'])
                old_assegnatario_ids = []
                for old_assegnatario in old_assegnatari:
                    old_assegnatario_ids.append(old_assegnatario['assegnatario_id'][0])

                assegnatario_to_create_ids = list(set(assegnatario_ids) - set(old_assegnatario_ids))
                assegnatario_to_unlink_ids = list(set(old_assegnatario_ids) - set(assegnatario_ids))
            else:
                assegnatario_to_create_ids = assegnatario_ids

            if assegnatario_to_unlink_ids and delete:
                # eliminazione delle vecchie assegnazioni (eventuali figli vengono eliminati a cascata)
                assegnazione_to_unlink_ids = self.search(cr, uid, [
                    ('protocollo_id', '=', protocollo_id),
                    ('tipologia_assegnazione', '=', 'conoscenza'),
                    ('assegnatario_id', 'in', assegnatario_to_unlink_ids)
                ])
                if assegnazione_to_unlink_ids:
                    self.unlink(cr, uid, assegnazione_to_unlink_ids, {'recompute': False})

            if assegnatario_to_create_ids:
                # creazione della nuova assegnazione
                self._crea_assegnazioni(cr, uid, protocollo_id, assegnatario_to_create_ids, assegnatore_id, 'conoscenza')


    def modifica_stato_assegnazione(self, cr, uid, protocollo_ids, state, assegnatario_employee_id=None, motivazione_rifiuto=None):
        employee_obj = self.pool.get('hr.employee')
        if assegnatario_employee_id:
            employee_ids = [assegnatario_employee_id]
        else:
            employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
            if len(employee_ids) == 0:
                raise orm.except_orm('Attenzione!', 'Non è stato trovato il dipendente per la tua utenza!')

        assegnazione_list = []
        for protocollo_id in protocollo_ids:
            if state in ['preso', 'rifiutato']:
                # verifica che il protocollo non abbia uno stato diverso da 'assegnato'
                assegnazione_state_ids = self.search(cr, uid, [
                    ('protocollo_id', '=', protocollo_id),
                    ('tipologia_assegnazione', '=', 'competenza'),
                    ('tipologia_assegnatario', '=', 'employee'),
                    ('assegnatario_employee_id', 'in', employee_ids),
                    ('state', 'not in', ['assegnato', 'archiviato'])
                ])
                for assegnazione_state_id in assegnazione_state_ids:
                    assegnazione_state = self.browse(cr, uid, assegnazione_state_id)

                    # verifica che l'assegnazione sia per dipendente oppure se è per ufficio si deve controllare anche
                    # che l'ufficio sia lo stesso attualmente assegnato al dipendente
                    if not assegnazione_state.parent_id or \
                            assegnazione_state.assegnatario_employee_department_id.id == assegnazione_state.assegnatario_employee_id.department_id.id:
                        for state_assegnatario in self._fields['state'].selection:
                            if state_assegnatario[0] == assegnazione_state.state:
                                raise orm.except_orm(
                                    'Attenzione!',
                                    '''
                                    Non è più possibile eseguire l\'operazione richiesta!
                                    Il protocollo è in stato "%s"!
                                    ''' % (str(state_assegnatario[1]),)
                                )
                                break

            # verifica che l'utente sia uno degli assegnatari del protocollo
            assegnazione_ids = []

            # ricerca per prima cosa se esiste un'assegnazione per dipendente
            assegnazione_employee_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnazione', '=', 'competenza'),
                ('assegnatario_employee_id', 'in', employee_ids),
                ('parent_id', '=', False)
            ])
            assegnazione_ids = assegnazione_ids + assegnazione_employee_ids

            if not assegnazione_ids:
                for employee_id in employee_ids:
                    # per seconda cosa ricerca per ogni employee se esiste un'assegnazione per ufficio in cui è
                    # attualmente presente, infatti l'assegnazione per ufficio non sarebbe più valida se lui non
                    # appartenesse più all'ufficio
                    employee = employee_obj.browse(cr, uid, employee_id)
                    if employee.department_id:
                        assegnazione_employee_department_ids = self.search(cr, uid, [
                            ('protocollo_id', '=', protocollo_id),
                            ('tipologia_assegnazione', '=', 'competenza'),
                            ('assegnatario_employee_id', '=', employee.id),
                            ('assegnatario_employee_department_id', '=', employee.department_id.id),
                            ('parent_id', '!=', False)
                        ])
                        assegnazione_ids = assegnazione_ids + assegnazione_employee_department_ids

            if len(assegnazione_ids) == 0:
                # se non trova assegnazioni per l'utente allora verifica che ci sia l'assegnazione per il suo ufficio,
                # infatti potrebbe verificarsi che l'utente viene spostato o inserito nell'ufficio dopo la creazione del
                # protocollo. In tale caso, l'istanza di assegnazione per l'utente non sarebbe presente ed è necessario
                # crearne una.
                assegnazione_found = False

                for employee_id in employee_ids:
                    employee = employee_obj.browse(cr, uid, employee_id)
                    assegnazione_ids = self.search(cr, uid, [
                        ('protocollo_id', '=', protocollo_id),
                        ('tipologia_assegnazione', '=', 'competenza'),
                        ('assegnatario_department_id', '=', employee.department_id.id)
                    ])
                    if assegnazione_ids:
                        assegnazione_ufficio = self.browse(cr, uid, assegnazione_ids[0])
                        dipendente_assegnatario_ids = self.pool.get('protocollo.assegnatario').search(cr, uid, [
                            ('parent_id', '=', assegnazione_ufficio.assegnatario_id.id),
                            ('employee_id', '=', employee_id),
                            ('tipologia', '=', 'employee')
                        ])
                        assegnazione_id = self._crea_assegnazione(cr, uid, protocollo_id, dipendente_assegnatario_ids[0],
                                                                  assegnazione_ufficio.assegnatore_id.id, 'competenza',
                                                                  assegnazione_ufficio.id)
                        assegnazione_ids = [assegnazione_id]
                        assegnazione_found = True
                        break

                if not assegnazione_found:
                    raise orm.except_orm('Attenzione!', 'Non sei uno degli assegnatari del protocollo!')

            # aggiorna il nuovo stato per l'assegnazione dell'utente
            self.write(cr, uid, assegnazione_ids, {
                'state': state,
                'motivazione_rifiuto': motivazione_rifiuto
            })

            for assegnazione_id in assegnazione_ids:
                # aggiorna, se presente, anche l'assegnazione dell'ufficio
                assegnazione = self.browse(cr, uid, assegnazione_id)
                assegnazione_list.append(assegnazione)
                if assegnazione.parent_id:
                    self.write(cr, uid, [assegnazione.parent_id.id], {
                        'state': state,
                        'motivazione_rifiuto': motivazione_rifiuto
                    })

        return assegnazione_list

    def modifica_stato_assegnazione_conoscenza(self, cr, uid, protocollo_ids, state, assegnatario_employee_id=None):
        employee_obj = self.pool.get('hr.employee')
        if assegnatario_employee_id:
            employee_ids = [assegnatario_employee_id]
        else:
            employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
            if len(employee_ids) == 0:
                raise orm.except_orm('Attenzione!', 'Non è stato trovato il dipendente per la tua utenza!')

        assegnazione_list = []
        for protocollo_id in protocollo_ids:
            # verifica che l'utente sia uno degli assegnatari del protocollo
            assegnazione_ids = []

            # ricerca per prima cosa se esiste un'assegnazione per dipendente
            assegnazione_employee_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnazione', '=', 'conoscenza'),
                ('assegnatario_employee_id', 'in', employee_ids),
                ('parent_id', '=', False)
            ])
            assegnazione_ids = assegnazione_ids + assegnazione_employee_ids

            for employee_id in employee_ids:
                # per seconda cosa ricerca per ogni employee se esiste un'assegnazione per ufficio in cui è attualmente
                # presente, infatti l'assegnazione per ufficio non sarebbe più valida se lui non appartenesse più all'
                # ufficio
                employee = employee_obj.browse(cr, uid, employee_id)
                if employee.department_id:
                    assegnazione_employee_department_ids = self.search(cr, uid, [
                        ('protocollo_id', '=', protocollo_id),
                        ('tipologia_assegnazione', '=', 'conoscenza'),
                        ('assegnatario_employee_id', '=', employee.id),
                        ('assegnatario_employee_department_id', '=', employee.department_id.id),
                        ('parent_id', '!=', False)
                    ])
                    assegnazione_ids = assegnazione_ids + assegnazione_employee_department_ids

            if len(assegnazione_ids) == 0:
                # se non trova assegnazioni per l'utente allora verifica che ci sia l'assegnazione per il suo ufficio,
                # infatti potrebbe verificarsi che l'utente viene spostato o inserito nell'ufficio dopo la creazione del
                # protocollo. In tale caso, l'istanza di assegnazione per l'utente non sarebbe presente ed è necessario
                # crearne una.
                assegnazione_found = False

                for employee_id in employee_ids:
                    employee = employee_obj.browse(cr, uid, employee_id)
                    assegnazione_ids = self.search(cr, uid, [
                        ('protocollo_id', '=', protocollo_id),
                        ('tipologia_assegnazione', '=', 'conoscenza'),
                        ('assegnatario_department_id', '=', employee.department_id.id)
                    ])
                    if assegnazione_ids:
                        assegnazione_ufficio = self.browse(cr, uid, assegnazione_ids[0])
                        dipendente_assegnatario_ids = self.pool.get('protocollo.assegnatario').search(cr, uid, [
                            ('parent_id', '=', assegnazione_ufficio.assegnatario_id.id),
                            ('employee_id', '=', employee_id),
                            ('tipologia', '=', 'employee')
                        ])
                        assegnazione_id = self._crea_assegnazione(cr, uid, protocollo_id, dipendente_assegnatario_ids[0],
                                                                  assegnazione_ufficio.assegnatore_id.id, 'conoscenza',
                                                                  assegnazione_ufficio.id)
                        assegnazione_ids = [assegnazione_id]
                        assegnazione_found = True
                        break

                if not assegnazione_found:
                    raise orm.except_orm('Attenzione!', 'Non sei uno degli assegnatari del protocollo!')

            # aggiorna il nuovo stato per l'assegnazione dell'utente
            self.write(cr, uid, assegnazione_ids, {'state': state})

            for assegnazione_id in assegnazione_ids:
                # aggiorna, se presente, anche l'assegnazione dell'ufficio se tutti i dipendenti hanno lo stesso stato
                assegnazione = self.browse(cr, uid, assegnazione_id)
                assegnazione_list.append(assegnazione)
                if assegnazione.parent_id:
                    assegnazioni_stesso_stato_ids = self.search(cr, uid, [
                        ('protocollo_id', '=', protocollo_id),
                        ('parent_id', '=', assegnazione.parent_id.id),
                        ('tipologia_assegnazione', '=', 'conoscenza'),
                        ('tipologia_assegnatario', '=', 'employee'),
                        ('state', '=', assegnazione.parent_id.state)
                    ])
                    if len(assegnazioni_stesso_stato_ids) == 0:
                        self.write(cr, uid, [assegnazione.parent_id.id], {'state': state})

        return assegnazione_list

    def get_default_assegnatore_department_id(self, cr, uid, protocollo_id):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        employee_obj = self.pool.get('hr.employee')

        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
        employee_count = len(employee_ids)
        if employee_count == 0:
            return False
        elif employee_count == 1:
            employee = employee_obj.browse(cr, uid, employee_ids[0])
            if employee.department_id:
                return employee.department_id.id

        protocollo = protocollo_obj.browse(cr, uid, protocollo_id, {'skip_check': True})

        # se il protocollo è stato registrato e l'utente corrente ha un dipendente che ha preso in carico il protocollo,
        # allora l'ufficio dell'assegnatore è lo stesso dell'assegnatario per competenza
        if protocollo.registration_date:
            assegnazione_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnazione', '=', 'competenza'),
                ('assegnatario_employee_id', 'in', employee_ids),
                ('state', '=', 'preso')
            ])
            if assegnazione_ids:
                if len(assegnazione_ids) == 1:
                    assegnazione = self.browse(cr, uid, assegnazione_ids[0])
                    return assegnazione.assegnatario_employee_department_id.id

        # se l'utente non ha un dipendente fra gli assegnatari allora si controlla se l'utente ha un dipendente
        # appartenente all'ufficio di protocollazione, al fine di usare quest'ultimo come ufficio dell'assegnatore
        if protocollo.registration_employee_department_id:
            employee_ids = employee_obj.search(cr, uid, [
                ('id', 'in', employee_ids),
                ('department_id', '=', protocollo.registration_employee_department_id.id)
            ])
            if employee_ids:
                return protocollo.registration_employee_department_id.id

        return False

    def notifica_assegnazione(self, cr, uid, assegnazione):
        if not assegnazione:
            return
        if not assegnazione.protocollo_id.registration_date:
            return
        try:
            data_obj = self.pool.get('ir.model.data')
            email_template_obj = self.pool.get('email.template')
            if assegnazione.tipologia_assegnatario == 'employee':
                user = assegnazione.assegnatario_employee_id.user_id
                if not user:
                    return
                notifica_permesso = 'seedoo_protocollo.group_notifica_assegnazione_' + assegnazione.tipologia_assegnazione
                if assegnazione.parent_id:
                    notifica_permesso += '_ufficio'
                else:
                    notifica_permesso += '_utente'
                notifica_assegnazione = self.user_has_groups(cr, user.id, notifica_permesso)
                if notifica_assegnazione:
                    template_id = data_obj.get_object_reference(cr, uid, 'seedoo_protocollo', 'notify_protocol')[1]
                    email_template_obj.send_mail(cr, uid, template_id, assegnazione.id, context={'skip_check': True, 'lang': 'it_IT'})
            else:
                for child in assegnazione.child_ids:
                    self.notifica_assegnazione(cr, uid, child)
        except Exception as e:
            _logger.error(e.message)

    @api.multi
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        url_params = {
            'id': self.protocollo_id.id,
            'view_type': 'form',
            'model': 'protocollo.protocollo',
            'menu_id': self.env.ref('seedoo_protocollo.protocollo_protocollo_notified_menu').id,
            'action': self.env.ref('seedoo_protocollo.protocollo_protocollo_act').id,
        }

        params = '/web?#%s' % werkzeug.url_encode(url_params)
        return base_url + params
