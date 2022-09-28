odoo.define('fl_mail_client/static/src/models/mail/mail.js', function (require) {
'use strict';

const emojis = require('mail.emojis');
const { registerNewModel } = require('mail/static/src/model/model_core.js');
const { attr, many2many, many2one, one2many } = require('mail/static/src/model/model_field.js');
const { clear } = require('mail/static/src/model/model_field_command.js');
const { addLink, htmlToTextContentInline, parseAndTransform, timeFromNow } = require('mail.utils');

const { str_to_datetime } = require('web.time');

function factory(dependencies) {

    class Mail extends dependencies['mail.model'] {

        //----------------------------------------------------------------------
        // Public
        //----------------------------------------------------------------------

        /**
         * @static
         * @param {Object} data
         * @return {Object}
         */
        static convertData(data) {
            const data2 = {};
            if ('attachment_ids' in data) {
                if (!data.attachment_ids) {
                    data2.attachments = [['unlink-all']];
                } else {
                    data2.attachments = [
                        ['insert-and-replace', data.attachment_ids.map(attachmentData =>
                            this.env.models['mail.attachment'].convertData(attachmentData)
                        )],
                    ];
                }
            }

            if ('original_attachment_ids' in data) {
                if (!data.original_attachment_ids) {
                    data2.original_attachments = [['unlink-all']];
                } else {
                    data2.original_attachments = [
                        ['insert-and-replace', data.original_attachment_ids.map(attachmentData =>
                            this.env.models['mail.attachment'].convertData(attachmentData)
                        )],
                    ];
                }
            }

            if ('body_html' in data) {
                data2.body = data.body_html;
            }

            if ('state' in data) {
                data2.state = data.state;
            }

            if ('failure_reason' in data && data.failure_reason) {
                data2.failure_reason = data.failure_reason;
            }

            if ('original_body' in data && data.original_body) {
                data2.original_body = data.original_body;
            }

            if ('original_subject' in data && data.original_subject) {
                data2.original_subject = data.original_subject;
            }

            if ('original_email_from' in data && data.original_email_from) {
                data2.original_email_from = data.original_email_from;
            }

            if ('direction' in data) {
                data2.direction = data.direction;
                data2.isReceived = data.direction === 'in';
                data2.isSent = data.direction === 'out';
            }

            if ('create_date' in data && data.create_date) {
                data2.create_date = moment(str_to_datetime(data.create_date));
            }

            if ('server_received_datetime' in data && data.server_received_datetime) {
                data2.server_received_datetime = moment(str_to_datetime(data.server_received_datetime));
            }

            if ('sent_datetime' in data && data.sent_datetime) {
                data2.sent_datetime = moment(str_to_datetime(data.sent_datetime));
            }

            if ('email_from' in data) {
                data2.email_from = data.email_from;
            }

            if ('email_to' in data) {
                data2.email_to = data.email_to;
            }

            if ('email_cc' in data) {
                data2.email_cc = data.email_cc;
            }

            if ('reply_to' in data) {
                data2.reply_to = data.reply_to;
            }

            if ('id' in data) {
                data2.id = data.id;
            }

            if ('model' in data && 'res_id' in data && data.model && data.res_id) {
                const originThreadData = {
                    id: data.res_id,
                    model: data.model,
                };
                if ('record_name' in data && data.record_name) {
                    originThreadData.name = data.record_name;
                }
                if ('res_model_name' in data && data.res_model_name) {
                    originThreadData.model_name = data.res_model_name;
                }
                if ('module_icon' in data) {
                    originThreadData.moduleIcon = data.module_icon;
                }
                data2.originThread = [['insert', originThreadData]];
            }

            if ('subject' in data) {
                data2.subject = data.subject;
            }

            return data2;
        }

        /**
         * Performs the `mail_fetch` RPC on `mail.message`.
         *
         * @static
         * @param {Array[]} domain
         * @param {integer} [limit]
         * @param {integer[]} [moderated_channel_ids]
         * @param {Object} [context]
         * @returns {mail.mail[]}
         */
        static async performRpcMailFetch(domain, limit, moderated_channel_ids, context) {
            const mailsData = await this.env.services.rpc({
                model: 'mail.mail',
                method: 'mail_fetch',
                kwargs: {
                    context,
                    domain,
                    limit,
                },
            }, { shadow: true });

            const mails = this.env.models['fl_mail_client.mail'].insert(mailsData.map(
                mailData => this.env.models['fl_mail_client.mail'].convertData(mailData)
            ));

            return mails;
        }

        /**
         * @static
         * @param {mail.thread} thread
         * @param {string} threadStringifiedDomain
         */
        static uncheckAll(thread, threadStringifiedDomain) {
            const mailCache = thread.cache(threadStringifiedDomain);
            mailCache.update({ checkedMails: [['unlink', mailCache.mails]] });
        }

        /**
         * Refreshes the value of `dateFromNow` field to the "current now".
         */
        refreshDateFromNow() {
            this.update({ dateFromNow: this._computeDateFromNow() });
        }

        /**
         * Action to initiate reply to current message in Discuss Inbox. Assumes
         * that Discuss and Inbox are already opened.
         */
        <!-- TODO: actually not used in Mail client module -->
        replyTo() {
            this.env.messaging.discuss.replyToMessage(this);
        }

        //----------------------------------------------------------------------
        // Private
        //----------------------------------------------------------------------

        /**
         * @override
         */
        static _createRecordLocalId(data) {
            return `${this.modelName}_${data.id}`;
        }

        /**
         * @returns {string}
         */
        _computeDateFromNow() {
            if (!this.date) {
                return clear();
            }
            return timeFromNow(this.date);
        }

        /**
         * @returns {boolean}
         */
        _computeFailureNotifications() {
            return [['replace', this.notifications.filter(notifications =>
                ['exception', 'bounce'].includes(notifications.notification_status)
            )]];
        }

        /**
         * @private
         * @returns {boolean}
         */
        _computeIsCurrentPartnerAuthor() {
            return !!(
                this.author &&
                this.messagingCurrentPartner &&
                this.messagingCurrentPartner === this.author
            );
        }

        /**
         * @private
         * @returns {boolean}
         */
        _computeIsBodyEqualSubtypeDescription() {
            if (!this.body || !this.subtype_description) {
                return false;
            }
            const inlineBody = htmlToTextContentInline(this.body);
            return inlineBody.toLowerCase() === this.subtype_description.toLowerCase();
        }

        /**
         * The method does not attempt to cover all possible cases of empty
         * messages, but mostly those that happen with a standard flow. Indeed
         * it is preferable to be defensive and show an empty message sometimes
         * instead of hiding a non-empty message.
         *
         * The main use case for when a message should become empty is for a
         * message posted with only an attachment (no body) and then the
         * attachment is deleted.
         *
         * The main use case for being defensive with the check is when
         * receiving a message that has no textual content but has other
         * meaningful HTML tags (eg. just an <img/>).
         *
         * @private
         * @returns {boolean}
         */
        _computeIsEmpty() {
            const isBodyEmpty = (
                !this.body ||
                [
                    '',
                    '<p></p>',
                    '<p><br></p>',
                    '<p><br/></p>',
                ].includes(this.body.replace(/\s/g, ''))
            );
            return (
                isBodyEmpty &&
                this.attachments.length === 0 &&
                this.tracking_value_ids.length === 0 &&
                !this.subtype_description
            );
        }

         /**
         * @private
         * @returns {boolean}
         */
        _computeIsSubjectSimilarToOriginThreadName() {
            if (
                !this.subject ||
                !this.originThread ||
                !this.originThread.name
            ) {
                return false;
            }
            const threadName = this.originThread.name.toLowerCase().trim();
            const prefixList = ['re:', 'fw:', 'fwd:'];
            let cleanedSubject = this.subject.toLowerCase();
            let wasSubjectCleaned = true;
            while (wasSubjectCleaned) {
                wasSubjectCleaned = false;
                if (threadName === cleanedSubject) {
                    return true;
                }
                for (const prefix of prefixList) {
                    if (cleanedSubject.startsWith(prefix)) {
                        cleanedSubject = cleanedSubject.replace(prefix, '').trim();
                        wasSubjectCleaned = true;
                        break;
                    }
                }
            }
            return false;
        }

        /**
         * @private
         * @returns {mail.messaging}
         */
        _computeMessaging() {
            return [['link', this.env.messaging]];
        }

        /**
         * This value is meant to be based on field body which is
         * returned by the server (and has been sanitized before stored into db).
         * Do not use this value in a 't-raw' if the message has been created
         * directly from user input and not from server data as it's not escaped.
         *
         * @private
         * @returns {string}
         */
        _computePrettyBody() {
            let prettyBody = '';
            for (const emoji of emojis) {
                const { unicode } = emoji;
                const regexp = new RegExp(
                    `(?:^|\\s|<[a-z]*>)(${unicode})(?=\\s|$|</[a-z]*>)`,
                    "g"
                );
                const originalBody = this.body;
                if (this.body) {
                    prettyBody = this.body.replace(
                        regexp,
                        ` <span class="o_mail_emoji">${unicode}</span> `
                    );
                }

                if (_.str.count(prettyBody, "o_mail_emoji") > 200) {
                    prettyBody = originalBody;
                }
            }
            // add anchor tags to urls
            return parseAndTransform(prettyBody, addLink);
        }

        /**
         * @private
         * @returns {mail.thread[]}
         */
        _computeThreads() {
            // const threads = [...this.serverChannels];
            const threads = []
            if (this.isReceived) {
                threads.push(this.env.messaging.received);
            }
            if (this.isSent) {
                threads.push(this.env.messaging.sent);
            }
            return [['replace', threads]];
        }

    }

    Mail.fields = {
        attachments: many2many('mail.attachment', {
            inverse: 'mails',
        }),
        original_attachments: many2many('mail.attachment', {
            inverse: 'original_mails',
        }),
        // author: many2one('mail.partner', {
        //     inverse: 'mailsAsAuthor',
        // }),
        /**
         * This value is meant to be returned by the server
         * (and has been sanitized before stored into db).
         * Do not use this value in a 't-raw' if the message has been created
         * directly from user input and not from server data as it's not escaped.
         */
        body: attr({
            default: "",
        }),
        // checkedMailCaches: many2many('fl_mail_client.mail_cache', {
        //     inverse: 'checkedMails',
        // }),
        date: attr({
            default: moment(),
        }),
        create_date: attr(),
        server_received_datetime: attr(),
        sent_datetime: attr(),
        state: attr(),
        failure_reason: attr(),
        original_subject: attr(),
        original_email_from: attr(),
        original_body: attr({
            default: ""
        }),
        direction: attr(),
        /**
         * States the time elapsed since date up to now.
         */
        dateFromNow: attr({
            compute: '_computeDateFromNow',
            dependencies: [
                'date',
            ],
        }),
        email_from: attr(),
        email_to: attr(),
        email_cc: attr(),
        reply_to: attr(),
        id: attr(),
        /**
         * Determine whether the message has to be considered empty or not.
         *
         * An empty message has no text, no attachment and no tracking value.
         */
        isEmpty: attr({
            compute: '_computeIsEmpty',
            dependencies: [
                // 'attachments',
                'body',
                'subtype_description',
                'tracking_value_ids',
            ],
        }),
        messaging: many2one('mail.messaging', {
            compute: '_computeMessaging',
        }),
        messagingReceived: many2one('mail.thread', {
            related: 'messaging.received',
        }),
        messagingSent: many2one('mail.thread', {
            related: 'messaging.sent',
        }),
        moderation_status: attr(),
        /**
         * This value is meant to be based on field body which is
         * returned by the server (and has been sanitized before stored into db).
         * Do not use this value in a 't-raw' if the message has been created
         * directly from user input and not from server data as it's not escaped.
         */
        prettyBody: attr({
            compute: '_computePrettyBody',
            dependencies: ['body'],
        }),
        subject: attr(),
        subtype_description: attr(),
        subtype_id: attr(),
        isReceived: attr({
            default: false,
        }),
        isSent: attr({
            default: false,
        }),
        /**
         * All threads that this message is linked to. This field is read-only.
         */
        threads: many2many('mail.thread', {
            compute: '_computeThreads',
            dependencies: [
                'isReceived',
                'isSent',
                // 'messagingHistory',
                // 'messagingInbox',
                'messagingReceived',
                'messagingSent',
                // 'messagingModeration',
                // 'messagingStarred',
                // 'originThread',
                // 'serverChannels',
            ],
            inverse: 'mails',
        }),
        tracking_value_ids: attr({
            default: [],
        }),
        /**
         * All channels containing this mail on the server.
         * Equivalent of python field `channel_ids`.
         */
        serverChannels: many2many('mail.thread', {
            inverse: 'mailsAsServerChannel',
        }),
    };

    Mail.modelName = 'fl_mail_client.mail';

    return Mail;
}

registerNewModel('fl_mail_client.mail', factory);

});
