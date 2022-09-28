odoo.define('fl_widget_ztree.zTree', function (require) {
    "use strict";

    var zTreeWidget = require('app_web_widget_ztree.zTree');
    var core = require('web.core');
    var rpc = require("web.rpc");
    var _t = core._t;

    zTreeWidget.zTree.include({
        init: function (setting, data) {
            self = this
            this._super.apply(this, arguments);
            this.ztree_title_field = data.ztree_title_field;
            this.ztree_nodes_to_disable = data.ztree_nodes_to_disable ? data.ztree_nodes_to_disable : [];
            this.ztree_only_child = data.ztree_only_child;
            this.ztree_custom_class = data.ztree_custom_class ? data.ztree_custom_class : "no-hover";
            this.setting.view = {
                addDiyDom: function addDiyDom(treeId, node) {
                    if (self.checkNodeToDisable(self.ztree_only_child, self.ztree_nodes_to_disable, node)) {
                        $.fn.zTree._z.tools.$(node, $.fn.zTree.consts.id.A, self.setting).addClass(self.ztree_custom_class);
                    }
                }
            };
            if (setting.view) {
                $.extend(this.setting.view, setting.view);
            }
        },
        start: function () {
            // E' stato fatto l'ovverride del metodo start in modo da poter passare al metodo select node il terzo
            // paramentro a true. Il paramento in questione si chiama isSilent è permette di non perdere il focus sulla
            // inputbox quando si sta scrivendo. Se isSilent è a false, quando si sta cancellando una voce
            // precedentemente selezionata, viene perso il focus perché viene riaperto il popup con l'elemento
            // selezionato
            var self = this;
            if (!self.$zTree) {
                self.$zTree = $.fn.zTree.init(self.$el, self.setting, self.zNodes);
                if (self.ztree_selected_id != null && self.ztree_selected_id > 0) {
                    var node = self.$zTree.getNodeByParam('id', self.ztree_selected_id, null);

                    self.$zTree.selectNode(node, undefined, true);
                }
            }
        },

        checkNodeToDisable: function (ztree_only_child, ztree_nodes_to_disable, node) {
            //Disabilitazione del nodo in caso:
            // - il parametro ztree_only_child sia impostato su only_child e il nodo abbia dei figli
            // - l'id del nodo è contenuto nel parametro ztree_nodes_to_disable
            return (ztree_only_child === "only_child" && "child_ids" in node && node.child_ids.length > 0) ||
                    ztree_nodes_to_disable.includes(node.id);
        }
    });

    zTreeWidget.FieldZTree.include({
        init: function (setting, data) {
            this._super.apply(this, arguments);
            this.ztree_title_field = this.nodeOptions.ztree_title_field;
            this.ztree_child_key = this.nodeOptions.ztree_child_key;
            this.ztree_only_child = this.nodeOptions.ztree_only_child;
            this.ztree_only_child_by_function = this.nodeOptions.ztree_only_child_by_function
            this.ztree_name_field_readonly = this.nodeOptions.ztree_name_field_readonly
            this.ztree_tree_dimension = this.nodeOptions.ztree_tree_dimension;
            this.ztree_custom_class = this.nodeOptions.ztree_custom_class;
            this.nodeContext = this.record.getContext({additionalContext: this.attrs.context || {}});
            this.dropdown = false;
        },
        start: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (this.ztree_only_child_by_function) {
                rpc.query({
                    model: "ir.config_parameter",
                    method: this.ztree_only_child_by_function,
                }).then(function (result) {
                    if (result === "only_child") {
                        self.ztree_only_child = "only_child"
                    }
                });
            }
        },
        _selectNode: function (event, item) {
            var self = this;
            var disable_ids = [];
            if ("disable_ids" in self.nodeContext) {
                disable_ids = self.nodeContext.disable_ids;
            }
            if (self.many2one.checkNodeToDisable(self.ztree_only_child, disable_ids, item)){
                return false;
            }

            return this._super.apply(this, arguments);
        },
        _search: function (search_val) {
            var self = this;
            var def = new Promise(function (resolve, reject) {
                var context = self.record.getContext(self.recordParams);
                var domain = self.record.getDomain(self.recordParams);

                // Add the additionalContext
                _.extend(context, self.additionalContext);

                var blacklisted_ids = self._getSearchBlacklist();
                if (blacklisted_ids.length > 0) {
                    domain.push(['id', 'not in', blacklisted_ids]);
                }
                if (search_val && search_val != "") {
                    // Ricerca basata sul nome mostrato (se presente) invece che sul name
                    if (self.ztree_name_field) {
                        domain.push([self.ztree_name_field, 'ilike', search_val]);
                    } else {
                        domain.push(['name', 'ilike', search_val]);
                    }
                }
                var parent_key = self.ztree_parent_key;
                var child_key = self.ztree_child_key;
                var root_id = self.ztree_root_id;
                var expend_level = self.ztree_expend_level;
                var name_field = self.ztree_name_field;
                var title_field = self.ztree_title_field;
                self._rpc({
                    model: self.field.relation,
                    method: "search_ztree",
                    kwargs: {
                        domain: domain,
                        context: context,
                        parent_key: parent_key,
                        child_key: child_key,
                        root_id: root_id,
                        expend_level: expend_level,
                        name_field: name_field,
                        title_field: title_field,
                        limit: parseInt(self.limit + 1),
                        order: self.order,
                    }
                })
                    .then(function (result) {
                        var values = result;
                        if (values.length > self.limit) {
                            values = self._manageSearchMore(values, search_val, domain, context);
                        }
                        var create_enabled = self.can_create && !self.nodeOptions.no_create;
                        var raw_result = _.map(result, function (x) {
                            return x[1];
                        });

                        if (create_enabled && !self.nodeOptions.no_quick_create &&
                            search_val.length > 0 && !_.contains(raw_result, search_val)) {
                            values.push({
                                id: null,
                                name: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
                                    $('<span />').text(search_val).html()),
                                font: {'color': '#00A09D', 'font-weight': 'bold'},
                                label: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
                                    $('<span />').text(search_val).html()),
                                action: self._quickCreate.bind(self, search_val),
                                classname: 'o_m2o_dropdown_option'
                            });
                        }
                        if (create_enabled && !self.nodeOptions.no_create_edit) {
                            var createAndEditAction = function () {
                                // Clear the value in case the user clicks on discard
                                self.$('input').val('');
                                return self._searchCreatePopup("form", false, self._createContext(search_val));
                            };
                            values.push({
                                id: null,
                                name: _t("Create and Edit..."),
                                font: {'color': '#00A09D', 'font-weight': 'bold'},
                                label: _t("Create and Edit..."),
                                action: createAndEditAction,
                                classname: 'o_m2o_dropdown_option',
                            });
                        } else if (values.length === 0) {
                            values.push({
                                id: null,
                                name: _t("No results to show..."),
                                font: {'color': '#00A09D', 'font-weight': 'bold'},
                                label: _t("No results to show..."),
                            });
                        }
                        resolve(values);
                    });
            });
            this.orderer.add(def);
            return def;
        },
        buildTreeView: function (search_val) {
            var self = this;
            var domain = self.record.getDomain(self.recordParams);
            var blacklisted_ids = self._getSearchBlacklist();
            if (blacklisted_ids.length > 0) {
                domain.push(['id', 'not in', blacklisted_ids]);
            }
            if (self.many2one) {
                self.many2one.destroy();
                self.many2one = undefined;
            }
            var setting = {
                callback: {
                    onClick: function (event, treeId, treeNode, clickFlag) {
                        self._selectNode(event, treeNode);
                    },
                }
            };
            self._search(search_val).then(function (result) {
                // bug fix modulo app_web_widget_ztree: elimina eventuali div ztree contenenti i risultati
                jQuery('.ztree').remove();
                if (self.value && self.value.data.id && self.value.data.id > 0)
                    var ztree_selected_id = self.value.data.id;
                self.many2one = new zTreeWidget.zTree(setting, {
                    zNodes: result,
                    ztree_domain: domain,
                    ztree_field: self.field.name,
                    ztree_model: self.field.relation,
                    ztree_parent_key: self.ztree_parent_key,
                    ztree_child_key: self.ztree_child_key,
                    ztree_root_id: self.ztree_root_id,
                    ztree_expend_level: self.ztree_expend_level,
                    ztree_name_field: self.ztree_name_field,
                    ztree_selected_id: ztree_selected_id,
                    ztree_only_child: self.ztree_only_child,
                    ztree_custom_class: self.ztree_custom_class,
                    ztree_nodes_to_disable: self.nodeContext.disable_ids
                });
                self.many2one.appendTo(self.$input.parent());
                self.$input.css('height', 'auto');
            });
        },
        _renderReadonly: async function () {
            if (this.ztree_name_field_readonly && this.value && this.value.data && this.value.data.id) {
                const records = await this._rpc({
                    model: this.field.relation,
                    method: "read",
                    args: [this.value.data.id, [this.ztree_name_field_readonly]],
                    context: this.context,
                });
                if (records.length > 0) {
                    var escapedValue = _.escape((records[0][this.ztree_name_field_readonly] || "").trim());
                    var value = escapedValue.split('\n').map(function (line) {
                        return '<span>' + line + '</span>';
                    }).join('<br/>');
                    this.$el.html(value);
                    if (!this.noOpen && this.value) {
                        this.$el.attr('href', _.str.sprintf('#id=%s&model=%s', this.value.res_id, this.field.relation));
                        this.$el.addClass('o_form_uri');
                    }
                    return;
                }
            } else {
                this._super.apply(this, arguments);
            }
        }
    });
});
