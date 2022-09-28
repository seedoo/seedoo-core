odoo.define('sd.protocollo.mezzo_trasmissione', function (require) {
    "use strict";
    var core = require('web.core');
    // var BasicFields= require('web.basic_fields');
    // var FormController = require('web.FormController');
    // var Registry = require('web.field_registry');
    // var utils = require('web.utils');
    // var session = require('web.session');
    // var field_utils = require('web.field_utils');
    //
    // var _t = core._t;
    // var QWeb = core.qweb;
    //
    // var ListRenderer = require("web.ListRenderer");

    var field_registry = require('web.field_registry');
    var relational_fields = require('web.relational_fields');
    var FieldMany2One = relational_fields.FieldMany2One;

    var IconLabel = FieldMany2One.extend({

        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
        },
        /**
         * @override
         * @private
         */
        _render: function () {
            var icon_fa = "fa fa-paper-plane";
            var icon_color = "#D2691E";
            var field_name_icon = this.nodeOptions["icon_field"] || false;
            var field_name_icon_color = this.nodeOptions["icon_color_field"] || false;
            if (field_name_icon && field_name_icon_color) {
                icon_fa = this.recordData[field_name_icon];
                icon_color = this.recordData[field_name_icon_color];
            }

            this._super.apply(this, arguments);
            this.$el.attr('href', '').css({'cursor': 'pointer', 'pointer-events' : 'none'});
            this.$el.addClass(icon_fa);
            this.$el.css("color", icon_color);
        },

    });

    field_registry.add('icon_label', IconLabel);

    return IconLabel;

});
//
//     var FieldIconLabel = FieldMany2One.extend({
//         template: 'FieldSignature',
//     ListRenderer.include({
//         /**
//          * Colorize a cell during it's render
//          *
//          * @override
//          */
//         _renderBodyCell: function (record, node) {
//             var $cell = this._super.apply(this, arguments);
//             console.log ("ci mezzo_trasmissione: "+ record.data);
//             if (record.model === "sd.protocollo.protocollo" && node.attrs.name ==="mezzo_trasmissione_id") {
//                 $cell.addClass("fa fa-user");
//             }
//             return $cell;
//         },
//     });
// });

