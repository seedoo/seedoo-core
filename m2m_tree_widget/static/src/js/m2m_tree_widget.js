openerp.m2m_tree_widget = function(instance) {

    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var _lt = instance.web._lt;
    instance.m2m_tree_widget.FieldMany2ManyTree = instance.web.form.AbstractField.extend(instance.web.form.ReinitializeFieldMixin,{
        template: 'm2m_tree',
        events: {
            'change input': 'store_dom_value',
        },
        init: function(field_manager, node) {
            var self = this;
            this._super(field_manager, node);
            this.is_started = false;
            this.set("value", false);
            this.set("values", []);
            this.field_manager.on("view_content_has_changed", this, function() {
                var domain = new openerp.web.CompoundDomain(this.build_domain()).eval();
                if (! _.isEqual(domain, this.get("domain"))) {
                    this.set("domain", domain);
                }
            });
        },
        reinit_value: function(val) {
            this.internal_set_value(val);
            this.floating = false;
            if (this.is_started && !this.no_rerender)
            		this.render_value(true);
        },
        initialize_field: function() {
            this.is_started = true;
            instance.web.form.ReinitializeFieldMixin.initialize_field.call(this);
            this.on("change:domain", this, this.initialize_content);
            this.set("domain", new openerp.web.CompoundDomain(this.build_domain()).eval());
            this.on("change:values", this, this.render_value);
        },
        initialize_content: function() {
            if (!this.get("effective_readonly"))
                this.render_editable();
        },
        render_value: function(no_recurse) {
            var self = this;
            var values = this.get_m2m_values();
            if (values.length == 0) {
                this.display_string("");
                return;
            }
            var display = false;
            if (this.display_value) {
                for (var i=0; i<values.length; i++) {
                    if (display) {
                        display = display + "\n" + this.display_value["" + values[i]];
                    } else {
                        display = this.display_value["" + values[i]];
                    }
                }
            }
            if (display) {
                this.display_string(display);
                return;
            }
            if (! no_recurse && this.get("effective_readonly")) {
                var dataset = new instance.web.DataSetStatic(this, this.field.relation, self.build_context());
                var def = this.alive(dataset.name_get(this.get_m2m_values())).done(function(data_list) {
                    for (var i=0; i<data_list.length; i++) {
                        var data = data_list[i];
                        if (!data[0]) {
                            self.do_warn(_t("Render"), _t("No value found for the field "+self.field.string));
                            return;
                        }
                        if (!self.display_value) {
                            self.display_value = {};
                        }
                        self.display_value["" + data[0]] = data[1];
                    }
                    self.render_value(true);
                });
                if (this.view && this.view.render_value_defs){
                    this.view.render_value_defs.push(def);
                }
            }
        },
        display_string: function(str) {
            var self = this;
            if (this.get("effective_readonly")) {
                var lines = _.escape(str).split("\n");
                var values = self.get_m2m_values();

                for (var i=0; i<lines.length; i++) {
                    var link = '';
                    var value = values[i];
                    if (this.options.no_open) {
                        link = '<span class="oe_form_uri">'+lines[i]+'</span><br />';
                    } else {
                        link = '<a id="oe_form_uri_'+value+'" res_id="'+value+'" class="oe_form_uri" href="#">'+lines[i]+'</a><br />';
                    }
                    this.$el.find('.oe_form_m2m_follow').append(link);

                    var $link = this.$el.find('#oe_form_uri_'+value).unbind('click');
                    if (!this.options.no_open) {
                        $link.click(function (ev) {
                            self.do_action({
                                type: 'ir.actions.act_window',
                                res_model: self.field.relation,
                                res_id: parseInt($(ev.currentTarget).attr('res_id')),
                                views: [[false, 'form']],
                                target: 'current',
                                context: self.build_context().eval(),
                            });
                            return false;
                        });
                    }
                }
            } else {
                this.render_editable();
            }
        },
        render_editable: function() {
            var self = this;

            //this.$input = this.$el.find("input");

            var dataset = new instance.web.DataSet(this, this.field.relation, self.build_context());
            var fields = _.keys(self.fields);
            var label = '';
            var order = '';
            var css_class = false;
            if (self.options.label) {
            	label = self.options.label;
            } else {
                label = 'name';
            }
            if (self.options.css_class) {
            	css_class = self.options.css_class;
            }
            if (self.options.order) {
            	order = self.options.order.split(',');
            } else {
                order = label;
            }

            var modelFields = ['id', label, css_class];
            var pid = 'parent_id';
            if (self.options.parent_field) {
            	pid = self.options.parent_field;
            }
        	modelFields.push(pid);
            if (self.options.field_no_checkbox) {
            	modelFields.push(self.options.field_no_checkbox);
            }
            var zNodes = new instance.web.Model(self.field.relation).query(modelFields)
	            .filter(this.get("domain"))
	            .limit(self.options.limit)
                .order_by(order)
                .context(self.build_context().eval())
	            .all().then(function (res) {
	            	var zNodes = [];
	            	for (r in res) {
	            	    var iconSkin = '';
	            	    if (css_class) {
                            iconSkin =  'class_' + res[r][css_class];
                        }
                        var nocheck = false;
	            	    if (self.options.field_no_checkbox && res[r][self.options.field_no_checkbox]) {
                            nocheck = true;
                        }
	            		zNodes.push(
                            {
                                id: res[r]['id'],
                                pId: res[r][pid] && res[r][pid][0] || false,
                                name: res[r][label],
                                doCheck: true,
                                chkDisabled: nocheck,
                                checked: self.get_m2m_values().indexOf(res[r]['id'])>-1 && true || false,
                                open: false,
                                iconSkin: iconSkin
                            }
	            		);
	            	}

	                var setting = {
                        view: {
                            selectedMulti: true,
                            dblClickExpand: false
                        },
                        check: {
                            enable: true,
                            chkboxType: { "Y" : "", "N" : "" }
                        },
                        data: {
                            simpleData: {
                                enable: true
                            }
                        },
                        callback: {
                            beforeCheck: beforeCheck,
                            onClick: onClick,
                            onCheck: onCheck
                        }
                    };
    		 		var code, log, className = "dark";
    		 		function beforeCheck(treeId, treeNode) {
    		 			return (treeNode.doCheck !== false);
    		 		};
    		 		function onClick(event, treeId, treeNode) {
    		 		    if (!treeNode.chkDisabled) {
    		 		        var zTree = $.fn.zTree.getZTreeObj(treeId);
                            if (zTree) {
                                zTree.checkNode(treeNode, !treeNode.checked,false,true);
                            }
                        }
    		 		};
    		 		function onCheck(e, treeId, treeNode) {
    		 		    var values = self.get_m2m_values();
    		 		    var index = values.indexOf(treeNode['id']);
    		 		    if (index != -1) {
                            values.splice(index, 1);
                        } else {
                            values.push(treeNode['id']);
                        }
    		 			self.set_m2m_values(values);
    		 		};
    		 		function expandParentNode(zTree, node) {
    		 			var pnode = false;
    		 			if (node) {
    		 				pnode = zTree.getNodeByParam("id", node['pId'], null);
    		 			}
    		 			if (pnode) {
    		 				zTree.expandNode(pnode, true, false, true);
    		 				expandParentNode(zTree, pnode);
    		 			}
    		 		};

    				$.fn.zTree.init($("#m2mTreeData_" + self.name), setting, zNodes);

		 			var zTree = $.fn.zTree.getZTreeObj("m2mTreeData_" + self.name);
		 			if (zTree) {
		 			    var nodes = zTree.getNodes();
                        if (! self.options.all_checkable) {
                            for (n in nodes) {
                                if (nodes[n].isParent) {
                                    zTree.setChkDisabled(nodes[n], true);
                                }
                            }
                        }
                        var checkedNodes = zTree.getNodesByParam("checked", true, null);
                        for (var i=0; i<checkedNodes.length; i++) {
                            expandParentNode(zTree, checkedNodes[i]);
                        }
                    }
	            });
        },
        set_value: function(value_) {
            if (value_ instanceof Array) {
                if (value_.length==0 || !(value_[0] instanceof Array)) {
                    value_ = [[6, 0, value_]];
                }
            }
            value_ = value_ || false;
            this.reinit_value(value_);
        },
        get_m2m_values: function() {
            if (this.get('value') instanceof Array) {
                return this.get('value')[0][2];
            } else {
                return [];
            }
        },
        set_m2m_values: function(values) {
            this.set_value([[6, 0, values]]);
        }

    });

    instance.web.form.widgets.add('m2m_tree', 'instance.m2m_tree_widget.FieldMany2ManyTree');
};
