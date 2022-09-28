odoo.define('fl_mail_client/static/src/models/thread_cache/thread_cache.js', function (require) {
    'use strict';

    const {
        registerInstancePatchModel,
    } = require('mail/static/src/model/model_core.js');

    registerInstancePatchModel('mail.thread_cache', 'fl_mail_client/static/src/models/thread_cache/thread_cache.js', {
         /**
         * @private
         */
        _onHasToLoadMessagesChanged() {
             /**
              * Avoids to load messages if Mail mail item is selected
              */
            if (!(this.thread && (this.thread.id === "mailreceived" || this.thread.id === "mailsent"))) {
                this._super(...arguments);
            }
        }

    });

});
