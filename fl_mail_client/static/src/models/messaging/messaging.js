odoo.define('fl_mail_client/static/src/models/messaging/messaging.js', function (require) {
    'use strict';

    const {
        registerFieldPatchModel
    } = require('mail/static/src/model/model_core.js');
    const {one2one} = require('mail/static/src/model/model_field.js');

    registerFieldPatchModel('mail.messaging', 'mail/static/src/models/messaging/messaging.js', {
        received: one2one('mail.thread'),
        sent:  one2one('mail.thread'),
    });

});
