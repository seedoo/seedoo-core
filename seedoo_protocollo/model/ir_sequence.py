from openerp.osv import orm, osv
from openerp.tools.translate import _


class IrSequence(orm.Model):
    _inherit = 'ir.sequence'

    def get_serialized_sequence_code(self, cr, uid, sequence_code, context=None):

        self.check_access_rights(cr, uid, 'read')
        company_ids = self.pool.get('res.company').search(cr, uid, [], context=context) + [False]
        ids = self.search(cr, uid, ['&', ('code', '=', sequence_code), ('company_id', 'in', company_ids)])
        return self._next_serialized(cr, uid, ids, context)

    def _next_serialized(self, cr, uid, ids, context=None):
        if not ids:
            return False
        if context is None:
            context = {}
        force_company = context.get('force_company')
        if not force_company:
            force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        sequences = self.read(cr, uid, ids, ['name','company_id','implementation','number_next','prefix','suffix','padding'])
        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        if seq['implementation'] == 'standard':
            cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
            seq['number_next'] = cr.fetchone()
        else:
            cr.execute("BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE READ WRITE;")
            cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE", (seq['id'],))
            cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
            cr.execute("COMMIT TRANSACTION;")
            self.invalidate_cache(cr, uid, ['number_next'], [seq['id']], context=context)
        d = self._interpolation_dict_context(context=context)
        try:
            interpolated_prefix = self._interpolate(seq['prefix'], d)
            interpolated_suffix = self._interpolate(seq['suffix'], d)
        except ValueError:
            raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix