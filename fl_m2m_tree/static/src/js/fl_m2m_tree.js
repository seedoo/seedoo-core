odoo.define("fl_m2m_tree.M2mTree", function (require) {
"use strict";

var AbstractField = require("web.AbstractField");
var Domain = require("web.Domain");
var registry = require("web.field_registry");
var core = require("web.core");

var _t = core._t;
var _lt = core._lt;

var M2mTreeField = AbstractField.extend({
    description: _lt("M2mTreeField"),
    supportedFieldTypes: ["many2many"],
    template: "m2m_tree",
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

        var fieldTypology = "";
        var uncheckDifferentTypology = false;
        if (self.nodeOptions.field_typology) {
            fieldTypology = self.nodeOptions.field_typology
            modelFields.push(fieldTypology);
            if (self.nodeOptions.uncheck_different_typology) {
                uncheckDifferentTypology = self.nodeOptions.uncheck_different_typology;
            }
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
                var nodeTypology = '';
                if (fieldTypology) {
                    nodeTypology =  res[r][fieldTypology];
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
                    checked: self.value.res_ids.indexOf(res[r]["id"])>-1 && true || false,
                    open: false,
                    typology: nodeTypology,
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
            function beforeCheck(treeId, treeNode) {
                return (treeNode.doCheck !== false);
            };
            function onClick(event, treeId, treeNode) {
                if (!treeNode.chkDisabled) {
                    var zTree = $.fn.zTree.getZTreeObj(treeId);
                    if (zTree) {
                        zTree.checkNode(treeNode, !treeNode.checked, false, true);
                    }
                }
            };
            function onCheck(e, treeId, treeNode) {
                if (self.value.res_ids.indexOf(treeNode["id"])>-1) {
                    self._setValue({ operation: "FORGET", ids: [treeNode["id"]]});
                } else {
                    self._setValue({ operation: "ADD_M2M", ids: [{id: treeNode["id"]}]});
                }
                if (treeNode.checked && uncheckDifferentTypology) {
                    for (var treeNodeChildIndex in treeNode.children) {
                        var treeNodeChild = treeNode.children[treeNodeChildIndex];
                        if (treeNode.typology!=treeNodeChild.typology && treeNodeChild.checked) {
                            zTree.checkNode(treeNodeChild, false,false,true);
                        }
                    }
                    var treeNodeParent = treeNode.getParentNode();
                    if (treeNodeParent && treeNode.typology!=treeNodeParent.typology && treeNodeParent.checked) {
                        zTree.checkNode(treeNodeParent, false,false,true);
                    }
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
                var checkedNodes = zTree.getNodesByParam("checked", true, null);
                for (var i=0; i<checkedNodes.length; i++) {
                    expandParentNode(zTree, checkedNodes[i]);
                }
            }
        });

        self.isRendered = true;
    },
    _renderReadonly: function () {
        var self = this;

        var fieldNames = ["id"];
        var fieldName = "";
        if (self.nodeOptions.field_name) {
            fieldName = self.nodeOptions.field_name;
        } else {
            fieldName = "name";
        }
        fieldNames.push(fieldName);

        self._rpc({
            model: self.field.relation,
            method: "read",
            args: [self.value.res_ids, fieldNames],
        }).then(function (results) {
            results.forEach(function (result) {
                if (self.nodeOptions.no_open) {
                    var link = _.str.sprintf("<span class='oe_form_uri'>%s</span><br/>", result[fieldName]);
                } else {
                    var link = _.str.sprintf("<a id='oe_form_uri_%s' class='oe_form_uri' href='#id=%s&model=%s' res_id='%s'><span>%s</span></a><br/>", result["id"], result["id"], self.field.relation, result["id"], result[fieldName]);
                }
                self.$el.find(".oe_form_m2m_follow").append(link);
                if (!self.nodeOptions.no_open) {
                    var $link = self.$el.find(_.str.sprintf("#oe_form_uri_%s", result["id"])).unbind("click");
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
            });
        });
    }
});

registry.add("m2m_tree", M2mTreeField);

return M2mTreeField;

});