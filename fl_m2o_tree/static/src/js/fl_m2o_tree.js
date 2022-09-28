odoo.define("fl_m2o_tree.M2oTree", function (require) {
"use strict";

var AbstractField = require("web.AbstractField");
var Domain = require("web.Domain");
var registry = require("web.field_registry");
var core = require("web.core");

var _t = core._t;
var _lt = core._lt;

var M2oTreeField = AbstractField.extend({
    description: _lt("M2oTreeField"),
    supportedFieldTypes: ["many2one"],
    template: "m2o_tree",
    init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        this.nodeOptions = _.defaults(this.nodeOptions, {});
        this.nodeContext = this.record.getContext({additionalContext: this.attrs.context || {}});
        if (this.record.getDomain({fieldName: this.name}).length>0) {
            this.nodeDomain = this.record.getDomain({fieldName: this.name});
        } else {
             this.nodeDomain = Domain.prototype.stringToArray(this.attrs.domain || "");
        }
        this.isRendered = false;
    },
    _setValue: function (value, options) {
        value = value || {};
        // we need to specify the model for the change in basic_model
        // the value is then now a dict with id, display_name and model
        value.model = this.field.relation;
        return this._super(value, options);
    },
    _renderEdit: function () {
        var self = this;
        if (self.isRendered) {
            return;
        }
        var modelFields = ["id"];

        var field_name = "";
        if (self.nodeOptions.field_name) {
            field_name = self.nodeOptions.field_name;
        } else {
            field_name = "name";
        }
        modelFields.push(field_name);

        var fieldStyle = false;
        if (self.nodeOptions.field_style) {
            fieldStyle = self.nodeOptions.field_style;
            modelFields.push(fieldStyle);
        }

        var pid = "parent_id";
        if (self.nodeOptions.field_parent) {
            pid = self.nodeOptions.field_parent;
        }
        modelFields.push(pid);

        if (self.nodeOptions.field_checkable) {
            modelFields.push(self.nodeOptions.field_checkable);
        }

        var order = [{name: field_name}];
        if (self.nodeOptions.order) {
            order = _.map(self.nodeOptions.order.split(","), function (orderComponent) {
                var orderFieldComponents = orderComponent.split(" ");
                if (orderFieldComponents.length > 1) {
                    return {
                        name: orderFieldComponents[0],
                        asc: orderFieldComponents[1].toLowerCase()=="desc" ? false : true
                    };
                } else {
                    return {
                        name: orderFieldComponents[0]
                    };
                }
            });
        }

        self._rpc({
            model: self.field.relation,
            method: "search_read",
            args: [],
            kwargs: {
                domain: self.nodeDomain,
                fields: modelFields,
                limit: self.nodeOptions.limit,
                order: order,
                context: self.nodeContext,
            }
        }).then(function (res) {
            var zNodes = [];
            for (var r in res) {
                var iconSkin = "";
                if (fieldStyle) {
                    iconSkin =  res[r][fieldStyle];
                }
                var nocheck = false;
                if (self.nodeOptions.field_checkable && res[r][self.nodeOptions.field_checkable]) {
                    nocheck = true;
                } else if (self.nodeContext.disable_ids && self.nodeContext.disable_ids.indexOf(res[r]["id"])!==-1) {
                    nocheck = true;
                }
                var zNode = {
                    id: res[r]["id"],
                    pId: res[r][pid] && res[r][pid][0] || false,
                    name: res[r][field_name],
                    doCheck: true,
                    chkDisabled: nocheck,
                    checked: self.value.res_id == res[r]["id"] && true || false,
                    open: false,
                    iconSkin: iconSkin,
                    isParent: self.nodeContext.async
                };
                if (self.nodeContext.async) {
                    zNode["isParent"] = true;
                }
                zNodes.push(zNode);
            }

            var setting = {
                view: {
                    selectedMulti: false,
                    dblClickExpand: false
                },
                check: {
                    enable: true,
                    chkStyle: "radio",
                    radioType: "all"
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
            if (self.nodeContext.async) {
                setting["async"] = {
                    enable: true,
                    contentType: "application/json",
                    dataType: "json",
                    url: self.nodeContext.async_url,
                    autoParam: ["id"],
                    dataFilter: filter
                };
                function filter(treeId, parentNode, result) {
                    var childNodes = result["result"];
                    return childNodes;
                }
            }
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
                if (self.value.res_id == treeNode["id"]) {
                    self._setValue({id: false}, {});
                } else {
                    self._setValue({id: treeNode["id"]}, {});
                }
            };
            function expandParentNode(zTree, node) {
                var pnode = false;
                if (node) {
                    pnode = zTree.getNodeByParam("id", node["pId"], null);
                }
                if (pnode) {
                    zTree.expandNode(pnode, true, false, true);
                    expandParentNode(zTree, pnode);
                }
            };

            $.fn.zTree.init(self.$el, setting, zNodes);
            var zTree = $.fn.zTree.getZTreeObj("treeData_" + self.name);
            if (zTree) {
                var all_parent_nodes = zTree.getNodesByParam("isParent", true, null);

                if (! self.nodeOptions.all_checkable) {
                    for (var n in all_parent_nodes) {
                        if (all_parent_nodes[n].isParent) {
                            zTree.setChkDisabled(all_parent_nodes[n], true);
                        }
                    }
                }
                var checked = zTree.getNodeByParam("checked", true, null);
                expandParentNode(zTree, checked);
            }

            self.isRendered = true;
        });
    },
    _renderReadonly: function () {
        var self = this;
        
        var escapedValue = _.escape((self.value && self.value.data && self.value.data.display_name || "").trim());
        var value = escapedValue.split("\n").map(function (line) {
            return "<span>" + line + "</span>";
        }).join("<br/>");
        if (self.nodeOptions.no_open) {
            var link = _.str.sprintf("<span class='oe_form_uri'>%s</span><br/>", value);
        } else {
            var link = _.str.sprintf("<a id='oe_form_uri_%s' class='oe_form_uri' href='#id=%s&model=%s' res_id='%s'><span>%s</span></a><br/>", self.value.res_id, self.value.res_id, self.field.relation, self.value.res_id, value);
        }
        self.$el.append(link);
        if (!self.nodeOptions.no_open) {
            var $link = self.$el.find(_.str.sprintf("#oe_form_uri_%s", self.value.res_id)).unbind("click");
            $link.click(function (ev) {
                self.do_action({
                    type: "ir.actions.act_window",
                    res_model: self.field.relation,
                    res_id: parseInt($(ev.currentTarget).attr("res_id")),
                    views: [[false, "form"]],
                    target: "current",
                    context: self.nodeContext,
                });
                return false;
            });
        }
    }
});

registry.add("m2o_tree", M2oTreeField);

return M2oTreeField;

});