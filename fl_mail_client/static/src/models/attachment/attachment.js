odoo.define('fl_mail_client/static/src/models/attachment/attachment.js', function (require) {
    'use strict';

    const {
        registerFieldPatchModel
    } = require('mail/static/src/model/model_core.js');
    const {many2many} = require('mail/static/src/model/model_field.js');

    registerFieldPatchModel('mail.attachment', 'mail/static/src/models/attachment/attachment.js', {
        mails: many2many('fl_mail_client.mail', {
            inverse: 'attachments',
        }),
        original_mails: many2many('fl_mail_client.mail', {
            inverse: 'original_attachments',
        })
    });

});
