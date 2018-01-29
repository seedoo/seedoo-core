openerp.seedoo_protocollo = function(instance) {

    instance.web.form.One2ManyList.include({

        pad_table_to_parent: function(count) {
            if (this.records.length >= count ||
                    _(this.columns).any(function(column) { return column.meta; })) {
                return;
            }
            var cells = [];
            if (this.options.selectable) {
                cells.push('<th class="oe_list_record_selector"></td>');
            }
            _(this.columns).each(function(column) {
                if (column.invisible === '1') {
                    return;
                }
                cells.push('<td title="' + column.string + '">&nbsp;</td>');
            });
            if (this.options.deletable) {
                cells.push('<td class="oe_list_record_delete"><button type="button" style="visibility: hidden"> </button></td>');
            }
            cells.unshift('<tr>');
            cells.push('</tr>');

            var row = cells.join('');
            this.$current
                .children('tr:not([data-id])').remove().end()
                .append(new Array(count - this.records.length + 1).join(row));
        },

        pad_table_to: function (count) {

            var modelWithLimit1 = [
                'protocollo.assegnatario.ufficio',
                'protocollo.assegnatario.dipendente',
                'protocollo.assegna.ufficio.wizard',
                'protocollo.assegna.dipendente.wizard'
            ];

            if (modelWithLimit1.indexOf(this.dataset.model)>=0) {

                if (!this.view.is_action_enabled('create') || this.is_readonly()) {
                    this.pad_table_to_parent(1);
                    return;
                }

                this.pad_table_to_parent(1);

                if (this.records.length == 0) {
                    var self = this;
                    var columns = _(this.columns).filter(function (column) {
                        return column.invisible !== '1';
                    }).length;
                    if (this.options.selectable) { columns++; }
                    if (this.options.deletable) { columns++; }

                    var $cell = $('<td>', {
                        colspan: columns,
                        'class': this._add_row_class || ''
                    }).append(
                        $('<a>', {href: '#'}).text('Inserisci Assegnatario')
                            .mousedown(function () {
                                // FIXME: needs to be an official API somehow
                                if (self.view.editor.is_editing()) {
                                    self.view.__ignore_blur = true;
                                }
                            })
                            .click(function (e) {
                                e.preventDefault();
                                e.stopPropagation();
                                // FIXME: there should also be an API for that one
                                if (self.view.editor.form.__blur_timeout) {
                                    clearTimeout(self.view.editor.form.__blur_timeout);
                                    self.view.editor.form.__blur_timeout = false;
                                }
                                self.view.ensure_saved().done(function () {
                                    self.view.do_add_record();
                                });
                            }));

                    var $padding = this.$current.find('tr:not([data-id]):first');
                    var $newrow = $('<tr>').append($cell);
                    if ($padding.length) {
                        $padding.before($newrow);
                    } else {
                        this.$current.append($newrow)
                    }
                }

            } else {
                this._super(count);
            }



        }
    });
};