/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.binary', function (require) {
    "use strict";

    var core = require('web.core');
    var utils = require('web.utils');
    var session = require('web.session');
    var fields = require('web.basic_fields');
    var registry = require('web.field_registry');
    var field_utils = require('web.field_utils');

    var PreviewManager = require('fl_web_preview.PreviewManager');
    var PreviewDialog = require('fl_web_preview.PreviewDialog');

    var _t = core._t;
    var QWeb = core.qweb;

    fields.FieldBinaryFile.include({
        events: _.extend({}, fields.FieldBinaryFile.prototype.events, {
            "click .fl_field_preview_button": "_onPreviewButtonClick",
        }),
        _renderReadonly: function () {
            this._super.apply(this, arguments);
            var $button = $('<button/>', {
                class: 'fl_field_preview_button',
                type: 'button',
                html: '<i class="fa fa-file-text-o"></i>',
            });
            this.$el.prepend($button);
        },
        _onPreviewButtonClick: function (event) {
            var filename_fieldname = this.attrs.filename;
            var last_update = this.recordData.__last_update;
            var mimetype = this.recordData['mimetype'] || null;
            var filename = this.recordData[filename_fieldname] || null;
            var unique = last_update && field_utils.format.datetime(last_update);
            var binary_url = session.url('/web/content', {
                model: this.model,
                id: JSON.stringify(this.res_id),
                data: utils.is_bin_size(this.value) ? null : this.value,
                unique: unique ? unique.replace(/[^0-9]/g, '') : null,
                filename_field: filename_fieldname,
                filename: filename,
                field: this.name,
                download: true,
            });
            var preview = new PreviewDialog(
                this, [{
                    url: binary_url,
                    filename: filename,
                    mimetype: mimetype,
                }], 0
            );
            preview.appendTo($('body'));
            event.stopPropagation();
            event.preventDefault();
        },
    });

    var FieldBinaryPreview = fields.FieldBinaryFile.extend({
        template: 'fl_web_preview.FieldBinaryPreview',
        _renderReadonly: function () {
            this._renderPreview();
        },
        _renderEdit: function () {
            if (this.value) {
                this.$('.fl_field_preview_container').removeClass("o_hidden");
                this.$('.o_select_file_button').first().addClass("o_hidden");
                this._renderPreview();
            } else {
                this.$('.fl_field_preview_container').addClass("o_hidden");
                this.$('.o_select_file_button').first().removeClass("o_hidden");
            }
        },
        _renderPreview: function () {
            var manager_vals = {}
            this.$('.fl_field_preview_container').empty();
            var filename_fieldname = this.attrs.filename;
            var last_update = this.recordData.__last_update;
            var filename = this.recordData[filename_fieldname] || null;
            var mimetype = this.recordData['mimetype'] || null;
            function urlExists(url) {
                var http = new XMLHttpRequest();
                http.open('HEAD', url, false);
                http.send();
                if (http.status != 404)
                    return true;
                else
                    return false;
            };
            var unique = last_update && field_utils.format.datetime(last_update);
            var binary_url = session.url('/web/content', {
                model: this.model,
                id: JSON.stringify(this.res_id),
                data: utils.is_bin_size(this.value) ? null : this.value,
                unique: unique ? unique.replace(/[^0-9]/g, '') : null,
                filename_field: filename_fieldname,
                filename: filename,
                field: this.name,
                download: true,
            });
            if (this.res_id && urlExists(binary_url)) {
                manager_vals = {
                    url: binary_url,
                    filename: filename,
                    mimetype: mimetype,
                }
            } else {
                manager_vals = {
                    url: false,
                    filename: false,
                    mimetype: undefined,
                }
            }
            var manager = new PreviewManager(
                this, [manager_vals], 0
            );
            manager.appendTo(this.$('.fl_field_preview_container'));
        },
        on_save_as: function (event) {
            event.stopPropagation();
        },
    });

    registry.add('binary_preview', FieldBinaryPreview);

    return FieldBinaryPreview;

});
