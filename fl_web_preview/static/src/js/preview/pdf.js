/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.PreviewContentPDF', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var utils = require('web.utils');
var session = require('web.session');

var registry = require('fl_web_preview.registry');

var AbstractPreviewContent = require('fl_web_preview.AbstractPreviewContent');

var QWeb = core.qweb;
var _t = core._t;

var PreviewContentPDF = AbstractPreviewContent.extend({
	template: "fl_web_preview.PreviewContentPDF",
	init: function(parent, url, mimetype, filename) {
    	this._super.apply(this, arguments);
        this.viewer_url = '/web/static/lib/' + 
        	'pdfjs/web/viewer.html?file=' + 
        	encodeURIComponent(this.url);
    },
    renderPreviewContent: function() {
    	var def = $.Deferred();
    	this.$('.fl_web_preview_pdf iframe').on('load', function () {
    		$(this).contents().find('button#openFile').hide();
    		def.resolve();
        });
    	return def;
    },
    downloadable: false,
    printable: false,
});

registry.add('pdf', PreviewContentPDF);
registry.add('.pdf', PreviewContentPDF);
registry.add('application/pdf', PreviewContentPDF);

return PreviewContentPDF;

});