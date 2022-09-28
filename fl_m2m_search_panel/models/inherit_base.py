from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import OrderedSet
from odoo.models import regex_field_agg, VALID_AGGREGATE_FUNCTIONS, lazy_name_get
from odoo.addons.web.models.models import SEARCH_PANEL_ERROR_MESSAGE
from odoo.osv.expression import AND


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        field = self._fields[field_name]
        if field.type != 'many2many':
            return super(Base, self).search_panel_select_range(field_name, **kwargs)

        # START ########################################################################################################
        #supported_types = ['many2one', 'selection']
        supported_types = ['many2many']
        # END ##########################################################################################################
        if field.type not in supported_types:
            types = dict(self.env["ir.model.fields"]._fields["ttype"]._description_selection(self.env))
            raise UserError(_(
                'Only types %(supported_types)s are supported for category (found type %(field_type)s)',
                supported_types=", ".join(types[t] for t in supported_types),
                field_type=types[field.type],
            ))

        model_domain = kwargs.get('search_domain', [])
        extra_domain = AND([
            kwargs.get('category_domain', []),
            kwargs.get('filter_domain', []),
        ])

        if field.type == 'selection':
            return {
                'parent_field': False,
                'values': self._search_panel_selection_range(field_name, model_domain=model_domain,
                                extra_domain=extra_domain, **kwargs
                            ),
            }

        Comodel = self.env[field.comodel_name].with_context(hierarchical_naming=False)
        field_names = ['display_name']
        hierarchize = kwargs.get('hierarchize', True)
        parent_name = False
        if hierarchize and Comodel._parent_name in Comodel._fields:
            parent_name = Comodel._parent_name
            field_names.append(parent_name)

            def get_parent_id(record):
                value = record[parent_name]
                return value and value[0]
        else:
            hierarchize = False

        comodel_domain = kwargs.get('comodel_domain', [])
        enable_counters = kwargs.get('enable_counters')
        expand = kwargs.get('expand')
        limit = kwargs.get('limit')

        if enable_counters or not expand:
            domain_image = self._search_panel_field_image(field_name,
                model_domain=model_domain, extra_domain=extra_domain,
                only_counters=expand,
                set_limit= limit and not (expand or hierarchize or comodel_domain), **kwargs
            )

        if not (expand or hierarchize or comodel_domain):
            values = list(domain_image.values())
            if limit and len(values) == limit:
                return {'error_msg': str(SEARCH_PANEL_ERROR_MESSAGE)}
            return {
                'parent_field': parent_name,
                'values': values,
            }

        if not expand:
            image_element_ids = list(domain_image.keys())
            if hierarchize:
                condition = [('id', 'parent_of', image_element_ids)]
            else:
                condition = [('id', 'in', image_element_ids)]
            comodel_domain = AND([comodel_domain, condition])
        comodel_records = Comodel.search_read(comodel_domain, field_names, limit=limit)

        if hierarchize:
            ids = [rec['id'] for rec in comodel_records] if expand else image_element_ids
            comodel_records = self._search_panel_sanitized_parent_hierarchy(comodel_records, parent_name, ids)

        if limit and len(comodel_records) == limit:
            return {'error_msg': str(SEARCH_PANEL_ERROR_MESSAGE)}

        field_range = {}
        for record in comodel_records:
            record_id = record['id']
            values = {
                'id': record_id,
                'display_name': record['display_name'],
            }
            if hierarchize:
                values[parent_name] = get_parent_id(record)
            if enable_counters:
                image_element = domain_image.get(record_id)
                values['__count'] = image_element['__count'] if image_element else 0
                # keeps original count value
                values['__count_distinct'] = image_element['__count'] if image_element else 0
            field_range[record_id] = values

        if hierarchize and enable_counters:
            self._search_panel_global_counters(field_range, parent_name)

        return {
            'parent_field': parent_name,
            'values': list(field_range.values()),
        }


    @api.model
    def _search_panel_domain_image(self, field_name, domain, set_count=False, limit=False):
        field = self._fields[field_name]
        if field.type != 'many2many':
            return super(Base, self)._search_panel_domain_image(field_name, domain, set_count=set_count, limit=limit)

        def group_id_name(value):
            return value

        domain = AND([
            domain,
            [(field_name, '!=', False)],
        ])
        # START ########################################################################################################
        # groups = self.read_group(domain, [field_name], [field_name], limit=limit)
        groups = self.read_group_m2m(domain, [field_name], [field_name], limit=limit)
        # END ##########################################################################################################

        domain_image = {}
        for group in groups:
            id, display_name = group_id_name(group[field_name])
            values = {
                'id': id,
                'display_name': display_name,
            }
            if set_count:
                values['__count'] = group[field_name + '_count']
            domain_image[id] = values

        return domain_image


    @api.model
    def read_group_m2m(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # START ########################################################################################################
        # result = self._read_group_raw(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        result = self._read_group_raw_m2m(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        # END ##########################################################################################################

        groupby = [groupby] if isinstance(groupby, str) else list(OrderedSet(groupby))
        dt = [
            f for f in groupby
            if self._fields[f.split(':')[0]].type in ('date', 'datetime')  # e.g. 'date:month'
        ]

        # iterate on all results and replace the "full" date/datetime value
        # (range, label) by just the formatted label, in-place
        for group in result:
            for df in dt:
                # could group on a date(time) field which is empty in some
                # records, in which case as with m2o the _raw value will be
                # `False` instead of a (value, label) pair. In that case,
                # leave the `False` value alone
                if group.get(df):
                    group[df] = group[df][1]
        return result


    @api.model
    def _read_group_raw_m2m(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        self.check_access_rights('read')
        query = self._where_calc(domain)
        fields = fields or [f.name for f in self._fields.values() if f.store]
        # START ########################################################################################################
        table_link_suffix = 'm2m'
        for field in fields:
            query.join(self._table, 'id', self._fields[field].relation, self._fields[field].column1, table_link_suffix)
        # END ##########################################################################################################
        groupby = [groupby] if isinstance(groupby, str) else list(OrderedSet(groupby))
        groupby_list = groupby[:1] if lazy else groupby
        # START ########################################################################################################
        #annotated_groupbys = [self._read_group_process_groupby(gb, query) for gb in groupby_list]
        annotated_groupbys = []
        groupby_terms = []
        orderby_terms = []
        for field in fields:
            column2_m2m = '%s__%s.%s' % (self._table, table_link_suffix, self._fields[field].column2)
            groupby_terms.append(column2_m2m)
            orderby_terms.append(column2_m2m)
            annotated_groupbys.append({
                'field': field,
                'groupby': field,
                'type': 'many2many',
                'display_format': None,
                'interval': None,
                'tz_convert': None,
                'qualified_field': column2_m2m
            })
        # END ##########################################################################################################
        groupby_fields = [g['groupby'] for g in annotated_groupbys]
        order = orderby or ','.join([g for g in groupby_list])
        groupby_dict = {gb['groupby']: gb for gb in annotated_groupbys}

        self._apply_ir_rules(query, 'read')
        # START ########################################################################################################
        # for gb in groupby_fields:
        #     assert gb in self._fields, "Unknown field %r in 'groupby'" % gb
        #     gb_field = self._fields[gb].base_field
        #     assert gb_field.store and gb_field.column_type, "Fields in 'groupby' must be regular database-persisted fields (no function or related fields), or function fields with store=True"
        # END ##########################################################################################################

        aggregated_fields = []
        select_terms = []
        # START ########################################################################################################
        # fnames = []  # list of fields to flush
        #
        # for fspec in fields:
        #     if fspec == 'sequence':
        #         continue
        #     if fspec == '__count':
        #         # the web client sometimes adds this pseudo-field in the list
        #         continue
        #
        #     match = regex_field_agg.match(fspec)
        #     if not match:
        #         raise UserError(_("Invalid field specification %r.", fspec))
        #
        #     name, func, fname = match.groups()
        #     if func:
        #         # we have either 'name:func' or 'name:func(fname)'
        #         fname = fname or name
        #         field = self._fields.get(fname)
        #         if not field:
        #             raise ValueError("Invalid field %r on model %r" % (fname, self._name))
        #         if not (field.base_field.store and field.base_field.column_type):
        #             raise UserError(_("Cannot aggregate field %r.", fname))
        #         if func not in VALID_AGGREGATE_FUNCTIONS:
        #             raise UserError(_("Invalid aggregation function %r.", func))
        #     else:
        #         # we have 'name', retrieve the aggregator on the field
        #         field = self._fields.get(name)
        #         if not field:
        #             raise ValueError("Invalid field %r on model %r" % (name, self._name))
        #         if not (field.base_field.store and
        #                 field.base_field.column_type and field.group_operator):
        #             continue
        #         func, fname = field.group_operator, name
        #
        #     fnames.append(fname)
        #
        #     if fname in groupby_fields:
        #         continue
        #     if name in aggregated_fields:
        #         raise UserError(_("Output name %r is used twice.", name))
        #     aggregated_fields.append(name)
        #
        #     expr = self._inherits_join_calc(self._table, fname, query)
        #     if func.lower() == 'count_distinct':
        #         term = 'COUNT(DISTINCT %s) AS "%s"' % (expr, name)
        #     else:
        #         term = '%s(%s) AS "%s"' % (func, expr, name)
        #     select_terms.append(term)
        # END ##########################################################################################################

        for gb in annotated_groupbys:
            select_terms.append('%s as "%s" ' % (gb['qualified_field'], gb['groupby']))

        # START ########################################################################################################
        # self._flush_search(domain, fields=fnames + groupby_fields)
        #
        # groupby_terms, orderby_terms = self._read_group_prepare(order, aggregated_fields, annotated_groupbys, query)
        # END ##########################################################################################################
        from_clause, where_clause, where_clause_params = query.get_sql()
        if lazy and (len(groupby_fields) >= 2 or not self._context.get('group_by_no_leaf')):
            count_field = groupby_fields[0] if len(groupby_fields) >= 1 else '_'
        else:
            count_field = '_'
        count_field += '_count'

        prefix_terms = lambda prefix, terms: (prefix + " " + ",".join(terms)) if terms else ''
        prefix_term = lambda prefix, term: ('%s %s' % (prefix, term)) if term else ''

        query = """
            SELECT min("%(table)s".id) AS id, count("%(table)s".id) AS "%(count_field)s" %(extra_fields)s
            FROM %(from)s
            %(where)s
            %(groupby)s
            %(orderby)s
            %(limit)s
            %(offset)s
        """ % {
            'table': self._table,
            'count_field': count_field,
            'extra_fields': prefix_terms(',', select_terms),
            'from': from_clause,
            'where': prefix_term('WHERE', where_clause),
            'groupby': prefix_terms('GROUP BY', groupby_terms),
            'orderby': prefix_terms('ORDER BY', orderby_terms),
            'limit': prefix_term('LIMIT', int(limit) if limit else None),
            'offset': prefix_term('OFFSET', int(offset) if limit else None),
        }
        self._cr.execute(query, where_clause_params)
        fetched_data = self._cr.dictfetchall()

        if not groupby_fields:
            return fetched_data

        # START ########################################################################################################
        # self._read_group_resolve_many2one_fields(fetched_data, annotated_groupbys)
        self._read_group_resolve_many2many_fields(fetched_data, annotated_groupbys)
        # END ##########################################################################################################

        data = [{k: self._read_group_prepare_data(k, v, groupby_dict) for k, v in r.items()} for r in fetched_data]

        if self.env.context.get('fill_temporal') and data:
            data = self._read_group_fill_temporal(data, groupby, aggregated_fields,
                                                  annotated_groupbys)

        result = [self._read_group_format_result(d, annotated_groupbys, groupby, domain) for d in data]

        if lazy:
            # Right now, read_group only fill results in lazy mode (by default).
            # If you need to have the empty groups in 'eager' mode, then the
            # method _read_group_fill_results need to be completely reimplemented
            # in a sane way
            result = self._read_group_fill_results(
                domain, groupby_fields[0], groupby[len(annotated_groupbys):],
                aggregated_fields, count_field, result, read_group_order=order,
            )
        return result


    def _read_group_resolve_many2many_fields(self, data, fields):
        many2manyfields = {field['field'] for field in fields if field['type'] == 'many2many'}
        for field in many2manyfields:
            ids_set = {d[field] for d in data if d[field]}
            m2m_records = self.env[self._fields[field].comodel_name].browse(ids_set)
            data_dict = dict(lazy_name_get(m2m_records.sudo()))
            for d in data:
                d[field] = (d[field], data_dict[d[field]]) if d[field] else False