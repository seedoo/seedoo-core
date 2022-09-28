/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.image', function (require) {
    "use strict";

    var core = require('web.core');
    var utils = require('web.utils');
    var session = require('web.session');
    var fields = require('web.basic_fields');
    var field_utils = require('web.field_utils');

    var PreviewManager = require('fl_web_preview.PreviewManager');
    var PreviewDialog = require('fl_web_preview.PreviewDialog');

    var _t = core._t;
    var QWeb = core.qweb;

    fields.FieldBinaryImage.include({
        events: _.extend({}, fields.FieldBinaryImage.prototype.events, {
            'click img': 'onImagePreview',
        }),
        _render: function () {
            this._super.apply(this, arguments);
            if (this.nodeOptions.no_preview) {
                this.$('.fl_field_image_wrapper').addClass('fl_no_preview');
            }
        },
        onImagePreview: function () {
            if (this.mode === "readonly" && !this.nodeOptions.no_preview) {
                var last_update = this.recordData.__last_update;
                var unique = last_update && field_utils.format.datetime(last_update);
                var binary_url = session.url('/web/content', {
                    model: this.model,
                    id: JSON.stringify(this.res_id),
                    data: utils.is_bin_size(this.value) ? null : this.value,
                    unique: unique ? unique.replace(/[^0-9]/g, '') : null,
                    field: this.name,
                    download: true,
                });
                var preview = new PreviewDialog(
                    this, [{
                        url: binary_url,
                        filename: "image.png",
                        mimetype: "image/png",
                    }], 0
                );
                preview.appendTo($('body'));
                event.stopPropagation();
                event.preventDefault();
            }
        },
    });

});
