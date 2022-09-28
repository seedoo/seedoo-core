odoo.define('fl_mail_client/static/src/models/messaging_notification_handler/messaging_notification_handler.js', function (require) {
    'use strict';

    const { increment } = require('mail/static/src/model/model_field_command.js');

    const { registerInstancePatchModel } = require('mail/static/src/model/model_core.js');

    registerInstancePatchModel('mail.messaging_notification_handler', 'fl_mail_client/static/src/models/messaging_notification_handler/messaging_notification_handler.js', {

        async _handleNotifications(notifications) {
            await this.async(() => this._super(notifications));
            const filteredNotifications = this._filterNotificationsOnUnsubscribe(notifications);
            const proms = filteredNotifications.map(notification => {
                this._handleMail(notification);
            });
            await this.async(() => Promise.all(proms));
        },

        _handleMail(notification) {
            const [channel, data] = notification;
            const [db, model, id] = channel;
            if (model !== 'mail.list') {
                return;
            }
            if (data.event === 'mailreceived') {
                return this._handleMailReceived(data.mail);
            }
            if (data.event === 'mailsent') {
                return this._handleMailSent(data.mail);
            }
            if (data.event === 'mailupdated') {
                return this._handleMailUpdated(data.mail);
            }
        },

        /**
         * @private
         */
        _handleMailReceived(data) {
            const received = this.env.messaging.received;
            received.update({ counter: increment() });
            this.messaging.messagingMenu.update();
            this._loadMail(data, 'mail-received');
        },

        /**
         * @private
         */
        _handleMailSent(data) {
            const sent = this.env.messaging.sent;
            sent.update({ counter: increment() });
            this.messaging.messagingMenu.update();
            this._loadMail(data, 'mail-sent');
        },

        /**
         * @private
         */
        _handleMailUpdated(data) {
            if (data.direction === 'in') {
                this._loadMail(data, 'mail-received');
            }
            if (data.direction === 'out') {
                this._loadMail(data, 'mail-sent');
            }
        },

        /**
         * @private
         */
        async _loadMail(data, hintType) {
            if ('_beforeLoadMail' in this) {
                await this._beforeLoadMail(data, hintType);
            }
            const convertedData = this.env.models['fl_mail_client.mail'].convertData(data);
            const mail = this.env.models['fl_mail_client.mail'].insert(convertedData);
            for (const thread of mail.threads) {
                let stringifiedDomainActive;
                for (const threadView of thread.threadViews) {
                    threadView.addComponentHint(hintType, { mail });
                    // if domain active isn't the default we need to trigger the manual refresh of the relative cache
                    stringifiedDomainActive = threadView.mailCache.stringifiedDomain;
                    if (stringifiedDomainActive != "[]") {
                        threadView.mailCache.update({ isCacheRefreshRequested: true });
                    }
                }
                // iter over all caches to delete all except the default and the active cache
                for (let mailCache of thread.mail_caches) {
                    if (mailCache.stringifiedDomain != "[]" && mailCache.stringifiedDomain != stringifiedDomainActive) {
                        mailCache.delete();
                    }
                }
            }
        }

    });

});