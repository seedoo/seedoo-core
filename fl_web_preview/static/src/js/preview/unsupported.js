/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.PreviewContentUnsupported', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var utils = require('web.utils');
var session = require('web.session');

var AbstractPreviewContent = require('fl_web_preview.AbstractPreviewContent');

var QWeb = core.qweb;
var _t = core._t;

var PreviewContentUnsupported = AbstractPreviewContent.extend({
	template: "fl_web_preview.PreviewContentUnsupported",
    downloadable: false,
    printable: false,
});

return PreviewContentUnsupported;

});