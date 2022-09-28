/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.AbstractPreviewContent', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var utils = require('web.utils');
var session = require('web.session');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;

var AbstractPreviewContent = Widget.extend({
	init: function(parent, url, mimetype, filename) {
    	this._super.apply(this, arguments);
        this.mimetype = mimetype || "application/octet-stream";
        this.filename = filename || "Unknown";
        this.url = url;
    },
	willStart: function() { 
		return $.when(
			this._super.apply(this, arguments),
			ajax.loadLibs(this)
		);
    },
	start: function () {
		return $.when(
			this._super.apply(this, arguments),
			this.renderPreviewContent(),
		);
    },
	renderPreviewContent: function() {
    	return $.when();
    },
    printable: false,
    downloadable: false,
	contentActions: function() {
    	return [];
    },
});

return AbstractPreviewContent;

});