odoo.define('fl_mail_client/static/src/models/messaging_initializer/messaging_initializer.js', function (require) {
'use strict';

const { registerInstancePatchModel } = require('mail/static/src/model/model_core.js');

    registerInstancePatchModel('mail.messaging_initializer', 'fl_mail_client/static/src/models/messaging_initializer/messaging_initializer.js', {
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Adds "Sent" and "Received" items menu in Discuss Sidebar
         * @override
         */
        async start() {
            await this.async(() => this._super());
            this.messaging.update({
                received: [['create', {
                    id: 'mailreceived',
                    isServerPinned: true,
                    model: 'mail.box',
                    name: this.env._t("Received "),
                }]],
                sent: [['create', {
                    id: 'mailsent',
                    isServerPinned: true,
                    model: 'mail.box',
                    name: this.env._t("Sent "),
                }]],
            });
        },
    });

});

