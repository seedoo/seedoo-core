odoo.define('fl_mail_client/static/src/models/mail_cache/mail_cache.js', function (require) {
'use strict';

const { registerNewModel } = require('mail/static/src/model/model_core.js');
const { attr, many2many, many2one, one2many } = require('mail/static/src/model/model_field.js');

function factory(dependencies) {

    class MailCache extends dependencies['mail.model'] {

        //----------------------------------------------------------------------
        // Public
        //----------------------------------------------------------------------

        /**
         * @returns {fl_mail_client.mail[]|undefined}
         */
        async loadMoreMails() {
            if (this.isAllHistoryLoaded || this.isLoading) {
                return;
            }
            if (!this.isLoaded) {
                this.update({ isCacheRefreshRequested: true });
                return;
            }
            this.update({ isLoadingMore: true });
            const mailIds = this.fetchedMails.map(mail => mail.id);
            const limit = 30;
            const fetchedMails = await this.async(() => this._loadMails({
                extraDomain: [['id', '<', Math.min(...mailIds)]],
                limit,
            }));
            this.update({ isLoadingMore: false });
            if (fetchedMails.length < limit) {
                this.update({ isAllHistoryLoaded: true });
            }

            for (const threadView of this.threadViews) {
                threadView.addComponentHint('more-messages-loaded', { fetchedMails });
            }
            return fetchedMails;
        }

        /**
         * @returns {fl_mail_client.mail[]|undefined}
         */
        async loadNewMails() {
            if (this.isLoading) {
                return;
            }
            if (!this.isLoaded) {
                this.update({ isCacheRefreshRequested: true });
                return;
            }
            const mailIds = this.fetchedMails.map(mail => mail.id);
            const fetchedMails = this._loadMails({
                extraDomain: [['id', '>', Math.max(...mailIds)]],
                limit: false,
            });
            for (const threadView of this.threadViews) {
                threadView.addComponentHint('new-messages-loaded', { fetchedMails });
            }
            return fetchedMails;
        }

        //----------------------------------------------------------------------
        // Private
        //----------------------------------------------------------------------

        /**
         * @override
         */
        static _createRecordLocalId(data) {
            const {
                stringifiedDomain = '[]',
                thread: [[commandInsert, thread]],
            } = data;
            return `${this.modelName}_[${thread.localId}]_<${stringifiedDomain}>`;
        }

        /**
         * @private
         */
        _computeCheckedMails() {
            const messagesWithoutCheckbox = this.checkedMails.filter(
                mail => !mail.hasCheckbox
            );
            return [['unlink', mailsWithoutCheckbox]];
        }

        /**
         * @private
         * @returns {fl_mail_client.mail[]}
         */
        _computeFetchedMails() {
            if (!this.thread) {
                return [['unlink-all']];
            }
            const toUnlinkMails = [];
            for (const mail of this.fetchedMails) {
                if (!this.thread.mails.includes(mail)) {
                    toUnlinkMessages.push(mail);
                }
            }
            return [['unlink', toUnlinkMails]];
        }

        /**
         * @private
         * @returns {fl_mail_client.mail|undefined}
         */
        _computeLastFetchedMail() {
            const {
                length: l,
                [l - 1]: lastFetchedMail,
            } = this.orderedFetchedMails;
            if (!lastFetchedMail) {
                return [['unlink']];
            }
            return [['link', lastFetchedMail]];
        }

        /**
         * @private
         * @returns {fl_mail_client.mail|undefined}
         */
        _computeLastMail() {
            const {
                length: l,
                [l - 1]: lastMail,
            } = this.orderedMails;
            if (!lastMail) {
                return [['unlink']];
            }
            return [['link', lastMail]];
        }

        /**
         * @private
         * @returns {fl_mail_client.mail[]}
         */
        _computeMails() {
            if (!this.thread) {
                return [['unlink-all']];
            }
            let mails = this.fetchedMails;
            if (this.stringifiedDomain !== '[]') {
                return [['replace', mails]];
            }
            // main cache: adjust with newer messages
            let newerMails;
            if (!this.lastFetchedMail) {
                newerMails = this.thread.mails;
            } else {
                newerMails = this.thread.mails.filter(mail =>
                    mail.id > this.lastFetchedMail.id
                );
            }
            mails = mails.concat(newerMails);
            return [['replace', mails]];
        }

        /**
         *
         * @private
         * @returns {fl_mail_client.mail[]}
         */
        _computeNonEmptyMails() {
            return [['replace', this.mails.filter(mail => !mail.isEmpty)]];
        }

        /**
         * @private
         * @returns {fl_mail_client.mail[]}
         */
        _computeOrderedFetchedMails() {
            return [['replace', this.fetchedMails.sort((m1, m2) => this._compareMails(m1, m2))]];
        }

        /**
         * @private
         * @returns {fl_mail_client.mail[]}
         */
        _computeOrderedMails() {
            return [['replace', this.mails.sort((m1, m2) => this._compareMails(m1, m2))]];
        }

        _compareMails(m1, m2) {
            if (m1.direction=='in' && m2.direction=='in' && m1.server_received_datetime && m2.server_received_datetime) {
                return m1.server_received_datetime < m2.server_received_datetime ? -1 : 1;
            } else if (m1.direction=='out' && m2.direction=='out' && m1.sent_datetime && m2.sent_datetime) {
                return m1.sent_datetime < m2.sent_datetime ? -1 : 1;
            } else {
                return m1.id < m2.id ? -1 : 1;
            }
        }

        /**
         * @private
         * @returns {boolean}
         */
        _computeHasToLoadMails() {
            if (!this.thread) {
                // happens during destroy or compute executed in wrong order
                return false;
            }
            const wasCacheRefreshRequested = this.isCacheRefreshRequested;
            // mark hint as processed
            if (this.isCacheRefreshRequested) {
                this.update({ isCacheRefreshRequested: false });
            }
            if (this.thread.isTemporary) {
                // temporary threads don't exist on the server
                return false;
            }
            if (!wasCacheRefreshRequested && this.threadViews.length === 0) {
                // don't load mail that won't be used
                return false;
            }
            if (this.isLoading) {
                // avoid duplicate RPC
                return false;
            }
            if (!wasCacheRefreshRequested && this.isLoaded) {
                // avoid duplicate RPC
                return false;
            }
            const isMainCache = this.thread.mainCache === this;
            if (isMainCache && this.isLoaded) {
                // Ignore request on the main cache if it is already loaded or
                // loading. Indeed the main cache is automatically sync with
                // server updates already, so there is never a need to refresh
                // it past the first time.
                return false;
            }
            return true;
        }

        /**
         * @private
         * @returns {fl_mail_client.mail[]}
         */
        _computeUncheckedMails() {
            return [['replace', this.mails.filter(
                mail => mail.hasCheckbox && !this.checkedMails.includes(mail)
            )]];
        }

        /**
         * @private
         * @param {Array} domain
         * @returns {Array}
         */
        _extendMailDomain(domain) {
            const thread = this.thread;

            if (thread === this.env.messaging.received) {
                return domain.concat([
                    ['direction', '=', 'in'],
                ]);
            }

            if (thread === this.env.messaging.sent) {
                return domain.concat([
                    ['direction', '=', 'out'],
                ]);
            }

            return [];
        }

        /**
         * @private
         * @param {Object} [param0={}]
         * @param {Array[]} [param0.extraDomain]
         * @param {integer} [param0.limit=30]
         * @returns {fl_mail_client.mail[]}
         */
        async _loadMails({ extraDomain, limit = 30 } = {}) {
            if (this.thread.id !== "mailreceived" && this.thread.id !== "mailsent") {
                return [];
            }
            this.update({ isLoading: true });
            const searchDomain = JSON.parse(this.stringifiedDomain);
            let domain = searchDomain.length ? searchDomain : [];

            domain = this._extendMailDomain(domain);
            if (extraDomain) {
                domain = extraDomain.concat(domain);
            }

            const context = this.env.session.user_context;
            const moderated_channel_ids = this.thread.moderation
                ? [this.thread.id]
                : undefined;
            const mails = await this.async(() =>
                this.env.models['fl_mail_client.mail'].performRpcMailFetch(
                    domain,
                    limit,
                    moderated_channel_ids,
                    context,
                )
            );
            this.update({
                fetchedMails: [['link', mails]],
                isLoaded: true,
                isLoading: false,
            });
            if (!extraDomain && mails.length < limit) {
                this.update({ isAllHistoryLoaded: true });
            }
            this.env.messagingBus.trigger('o-thread-cache-loaded-mails', {
                fetchedMails: mails,
                mailCache: this,
            });
            return mails;
        }

        /**
         * Calls "mark all as read" when this thread becomes displayed in a
         * view (which is notified by `isMarkAllAsReadRequested` being `true`),
         * but delays the call until some other conditions are met, such as the
         * mails being loaded.
         * The reason to wait until mails are loaded is to avoid a race
         * condition because "mark all as read" will change the state of the
         * mails in parallel to fetch reading them.
         *
         * @private
         */
        _onChangeMarkAllAsRead() {
            if (
                !this.isMarkAllAsReadRequested ||
                !this.thread ||
                !this.thread.mainCache ||
                !this.isLoaded ||
                this.isLoading
            ) {
                // wait for change of state before deciding what to do
                return;
            }
            this.update({ isMarkAllAsReadRequested: false });
            if (
                this.thread.isTemporary ||
                this.thread.model === 'mail.box' ||
                this.thread.mainCache !== this ||
                this.threadViews.length === 0
            ) {
                // ignore the request
                return;
            }
            this.env.models['fl_mail_client.mail'].markAllAsRead([
                ['model', '=', this.thread.model],
                ['res_id', '=', this.thread.id],
            ]);
        }

        /**
         * Loads this thread cache, by fetching the most recent mails in this
         * conversation.
         *
         * @private
         */
        _onHasToLoadMailsChanged() {
            if (!this.hasToLoadMails) {
                return;
            }
            this._loadMails().then(fetchedMails => {
                for (const threadView of this.threadViews) {
                    threadView.addComponentHint('mails-loaded', { fetchedMails });
                }
            });
        }

        /**
         * Handles change of mails on this thread cache. This is useful to
         * refresh non-main caches that are currently displayed when the main
         * cache receives updates. This is necessary because only the main cache
         * is aware of changes in real time.
         */
        _onMailsChanged() {
            if (!this.thread) {
                return;
            }
            if (this.thread.mainCache !== this) {
                return;
            }
            for (const threadView of this.thread.threadViews) {
                if (threadView.mailCache) {
                    threadView.mailCache.update({ isCacheRefreshRequested: true });
                }
            }
        }

    }

    MailCache.fields = {
        /**
         * List of mails that have been fetched by this cache.
         *
         * This DOES NOT necessarily includes all mails linked to this thread
         * cache (@see mails field for that): it just contains list
         * of successive mails that have been explicitly fetched by this
         * cache. For all non-main caches, this corresponds to all mails.
         * For the main cache, however, mails received from longpolling
         * should be displayed on main cache but they have not been explicitly
         * fetched by cache, so they ARE NOT in this list (at least, not until a
         * fetch on this thread cache contains this mail).
         *
         * The distinction between mails and fetched mails is important
         * to manage "holes" in mail list, while still allowing to display
         * new mails on main cache of thread in real-time.
         */
        fetchedMails: many2many('fl_mail_client.mail', {
            // adjust with mails unlinked from thread
            compute: '_computeFetchedMails',
            dependencies: ['threadMails'],
        }),
        /**
         * Determines whether `this` should load initial mails. This field is
         * computed and should be considered read-only.
         * @see `isCacheRefreshRequested` to request manual refresh of mails.
         */
        hasToLoadMails: attr({
            compute: '_computeHasToLoadMails',
            dependencies: [
                'isCacheRefreshRequested',
                'isLoaded',
                'isLoading',
                'thread',
                'threadIsTemporary',
                'threadMainCache',
                'threadViews',
            ],
        }),
        isAllHistoryLoaded: attr({
            default: false,
        }),
        isLoaded: attr({
            default: false,
        }),
        isLoading: attr({
            default: false,
        }),
        isLoadingMore: attr({
            default: false,
        }),
        /**
         * Determines whether `this` should consider refreshing its mails.
         * This field is a hint that may or may not lead to an actual refresh.
         * @see `hasToLoadMails`
         */
        isCacheRefreshRequested: attr({
            default: false,
        }),
        /**
         * Determines whether this cache should consider calling "mark all as
         * read" on this thread.
         *
         * This field is a hint that may or may not lead to an actual call.
         * @see `_onChangeMarkAllAsRead`
         */
        isMarkAllAsReadRequested: attr({
            default: false,
        }),
        /**
         * Last mail that has been fetched by this thread cache.
         *
         * This DOES NOT necessarily mean the last mail linked to this thread
         * cache (@see lastMail field for that). @see fetchedMails field
         * for a deeper explanation about "fetched" mails.
         */
        lastFetchedMail: many2one('fl_mail_client.mail', {
            compute: '_computeLastFetchedMail',
            dependencies: ['orderedFetchedMails'],
        }),
        lastMail: many2one('fl_mail_client.mail', {
            compute: '_computeLastMail',
            dependencies: ['orderedMails'],
        }),
        // mailsCheckboxes: attr({
        //     related: 'mails.hasCheckbox',
        // }),
        /**
         * List of mails linked to this cache.
         */
        mails: many2many('fl_mail_client.mail', {
            compute: '_computeMails',
            dependencies: [
                'fetchedMails',
                'threadMails',
            ],
        }),
        /**
         * IsEmpty trait of all mails.
         * Serves as compute dependency.
         */
        mailsAreEmpty: attr({
            related: 'mails.isEmpty'
        }),
        /**
         * List of non empty mails linked to this cache.
         */
        nonEmptyMails: many2many('fl_mail_client.mail', {
            compute: '_computeNonEmptyMails',
            dependencies: [
                'mails',
                'mailsAreEmpty',
            ],
        }),
        /**
         * Not a real field, used to trigger its compute method when one of the
         * dependencies changes.
         */
        onChangeMarkAllAsRead: attr({
            compute: '_onChangeMarkAllAsRead',
            dependencies: [
                'isLoaded',
                'isLoading',
                'isMarkAllAsReadRequested',
                'thread',
                'threadIsTemporary',
                'threadMainCache',
                'threadModel',
                'threadViews',
            ],
        }),
        /**
         * Loads initial mails from `this`.
         * This is not a "real" field, its compute function is used to trigger
         * the load of mails at the right time.
         */
        onHasToLoadMailsChanged: attr({
            compute: '_onHasToLoadMailsChanged',
            dependencies: [
                'hasToLoadMails',
            ],
        }),
        /**
         * Not a real field, used to trigger `_onMailsChanged` when one of
         * the dependencies changes.
         */
        onMailsChanged: attr({
            compute: '_onMailsChanged',
            dependencies: [
                'mails',
                'thread',
                'threadMainCache',
            ],
        }),
        /**
         * Ordered list of mails that have been fetched by this cache.
         *
         * This DOES NOT necessarily includes all mails linked to this thread
         * cache (@see orderedMails field for that). @see fetchedMails
         * field for deeper explanation about "fetched" mails.
         */
        orderedFetchedMails: many2many('fl_mail_client.mail', {
            compute: '_computeOrderedFetchedMails',
            dependencies: ['fetchedMails'],
        }),
        /**
         * Ordered list of mails linked to this cache.
         */
        orderedMails: many2many('fl_mail_client.mail', {
            compute: '_computeOrderedMails',
            dependencies: ['mails'],
        }),
        stringifiedDomain: attr({
            default: '[]',
        }),
        thread: many2one('mail.thread', {
            inverse: 'mail_caches',
        }),
        /**
         * Serves as compute dependency.
         */
        threadIsTemporary: attr({
            related: 'thread.isTemporary',
        }),
        /**
         * Serves as compute dependency.
         */
        threadMainCache: many2one('mail.thread_cache', {
            related: 'thread.mainCache',
        }),

        threadMails: many2many('fl_mail_client.mail', {
            related: 'thread.mails',
        }),
        /**
         * Serves as compute dependency.
         */
        threadModel: attr({
            related: 'thread.model',
        }),
        /**
         * States the 'mail.thread_view' that are currently displaying `this`.
         */
        threadViews: one2many('mail.thread_view', {
            inverse: 'mailCache',
        }),
    };

    MailCache.modelName = 'fl_mail_client.mail_cache';

    return MailCache;
}

registerNewModel('fl_mail_client.mail_cache', factory);

});
