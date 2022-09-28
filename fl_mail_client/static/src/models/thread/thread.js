odoo.define('fl_mail_client/static/src/models/thread/thread.js', function (require) {
    'use strict';

    const {
        registerInstancePatchModel,
        registerFieldPatchModel
    } = require('mail/static/src/model/model_core.js');
    const {many2many, one2many} = require('mail/static/src/model/model_field.js');

    registerInstancePatchModel('mail.thread', 'fl_mail_client/static/src/models/thread/thread.js', {

        /**
         * @param {string} [stringifiedDomain='[]']
         * @returns {fl_mail_client.mail_cache}
         */
        mail_cache(stringifiedDomain = '[]') {
            return this.env.models['fl_mail_client.mail_cache'].insert({
                stringifiedDomain,
                thread: [['link', this]],
            });
        },

    });

    registerFieldPatchModel('mail.thread', 'fl_mail_client/static/src/models/thread/thread.js', {
        mails: many2many('fl_mail_client.mail', {
            inverse: 'threads',
        }),

        mail_caches: one2many('fl_mail_client.mail_cache', {
            inverse: 'thread',
            isCausal: true,
        }),

        mailsAsServerChannel: many2many('fl_mail_client.mail', {
            inverse: 'serverChannels',
        }),
    });

});
