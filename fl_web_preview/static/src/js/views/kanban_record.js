/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.KanbanRecord', function (require) {
    "use strict";

	var session = require('web.session');
    var field_utils = require('web.field_utils');
    var KanbanRecord = require('web.KanbanRecord');
	var PreviewDialog = require('fl_web_preview.PreviewDialog');

    KanbanRecord.include({
        events: _.extend({}, KanbanRecord.prototype.events, {
            'click .o_kanban_image_preview': '_onImageClicked',
        }),
        _onImageClicked: function (event) {
            var filename_fieldname = 'filename' in this.fields ? 'filename' : 'name';
            var content_fieldname = 'content' in this.fields ? 'content' : 'datas';
            var last_update = this.recordData.__last_update;
            var mimetype = this.recordData['mimetype'] || null;
            var filename = this.recordData[filename_fieldname] || null;
            var unique = last_update && field_utils.format.datetime(last_update);
            var binary_url = session.url('/web/content', {
                model: this.modelName,
                id: JSON.stringify(this.recordData.id),
                data: null,
                unique: unique ? unique.replace(/[^0-9]/g, '') : null,
                filename_field: filename_fieldname,
                filename: filename,
                field: content_fieldname,
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

});