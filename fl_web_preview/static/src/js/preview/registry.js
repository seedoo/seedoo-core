/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.registry', function (require) {
"use strict";

var Registry = require('web.Registry');

var PreviewWidget = require('fl_web_preview.PreviewContentUnsupported');

var previewRegistry = new Registry();
previewRegistry.defaultPreview = function () {
    return PreviewWidget;
};

return previewRegistry;

});