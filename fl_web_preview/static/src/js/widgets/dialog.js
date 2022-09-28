/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.PreviewDialog', function (require) {
"use strict";

var core = require('web.core');
var utils = require('web.utils');
var session = require('web.session');

var PreviewManager = require('fl_web_preview.PreviewManager');

var QWeb = core.qweb;
var _t = core._t;

var PreviewDialog = PreviewManager.extend({
    template: "fl_web_preview.PreviewDialog",
	events: _.extend({}, PreviewManager.prototype.events, {
		'click .fl_web_preview_maximize_btn': '_onMaximizeClick',
		'click .fl_web_preview_minimize_btn': '_onMinimizeClick',
	}),
    start: function () {
        this.$el.modal('show');
        this.$el.on('hidden.bs.modal', _.bind(this._onDestroy, this));
        this.$('[data-toggle="tooltip"]').tooltip({delay: 0});
        return this._super.apply(this, arguments); 
    },
    destroy: function () {
        if (this.isDestroyed()) {
            return;
        }
        this.$el.modal('hide');
        this.$el.remove();
        return this._super.apply(this, arguments);
    },
    _renderPreview: function (element) {
    	this._super.apply(this, arguments);
    	this.$('.modal-title').text(this.activeFile.filename || "Preview");
    },
    _onDestroy: function () {
        this.destroy();
    },
    _onMaximizeClick: function(event) {
    	this.$('.fl_web_preview_dialog').addClass("fl_web_preview_maximize");
    },
    _onMinimizeClick: function(event) {
    	this.$('.fl_web_preview_dialog').removeClass("fl_web_preview_maximize");
    },
});


return PreviewDialog;

});