odoo.define('fl_mail_client/static/src/components/mail_list/mail_list.js', function (require) {
'use strict';

const components = {
    Mail: require('fl_mail_client/static/src/components/mail/mail.js'),
};

/****
 *
 * It applies the MessageList component concept to mail.mail object
 *
*****/
const useRefs = require('mail/static/src/component_hooks/use_refs/use_refs.js');
const useRenderedValues = require('mail/static/src/component_hooks/use_rendered_values/use_rendered_values.js');
const useShouldUpdateBasedOnProps = require('mail/static/src/component_hooks/use_should_update_based_on_props/use_should_update_based_on_props.js');
const useStore = require('mail/static/src/component_hooks/use_store/use_store.js');

const { Component } = owl;
const { useRef } = owl.hooks;

class MailList extends Component {

    /**
     * @override
     */
    constructor(...args) {
        super(...args);
        useShouldUpdateBasedOnProps();
        useStore(props => {
            const threadView = this.env.models['mail.thread_view'].get(props.threadViewLocalId);
            const thread = threadView ? threadView.thread : undefined;
            const mailCache = threadView ? threadView.mailCache : undefined;
            return {
                // isDeviceMobile: this.env.messaging.device.isMobile,
                thread,
                mailCache,
                mailCacheIsAllHistoryLoaded: mailCache && mailCache.isAllHistoryLoaded,
                mailCacheIsLoaded: mailCache && mailCache.isLoaded,
                mailCacheIsLoadingMore: mailCache && mailCache.isLoadingMore,
                mailCacheLastMail: mailCache && mailCache.lastMail,
                mailCacheOrderedMails: mailCache ? mailCache.orderedMails : [],
                // threadIsTemporary: thread && thread.isTemporary,
                // threadMainCache: thread && thread.mainCache,
                // threadMailAfterNewMailSeparator: thread && thread.mailAfterNewMailSeparator,
                // threadViewComponentHintList: threadView ? threadView.componentHintList : [],
                // threadViewNonEmptyMailsLength: threadView && threadView.nonEmptyMails.length,
            };
        }, {
            compareDepth: {
                mailCacheOrderedMails: 1,
            },
        });
        this._getRefs = useRefs();

        this._loadMoreRef = useRef('loadMore');

        this._onScrollThrottled = _.throttle(this._onScrollThrottled.bind(this), 100);

        /**
         * State used by the component at the time of the render. Useful to
         * properly handle async code.
         */
        this._lastRenderedValues = useRenderedValues(() => {
            const threadView = this.threadView;
            const thread = threadView && threadView.thread;
            const mailCache = threadView && threadView.mailCache;
            return {
                // componentHintList: threadView ? [...threadView.componentHintList] : [],
                // hasAutoScrollOnMailReceived: threadView && threadView.hasAutoScrollOnMailReceived,
                // hasScrollAdjust: this.props.hasScrollAdjust,
                // mainCache: thread && thread.mainCache,
                order: this.props.order,
                orderedMails: mailCache ? [...mailCache.orderedMails] : [],
                thread,
                mailCache,
                mailCacheInitialScrollHeight: threadView && threadView.mailCacheInitialScrollHeight,
                mailCacheInitialScrollPosition: threadView && threadView.mailCacheInitialScrollPosition,
                threadView,
                threadViewer: threadView && threadView.threadViewer,
            };
        });
        // useUpdate must be defined after useRenderedValues to guarantee proper
        // call order
        // useUpdate({ func: () => this._update() });
    }


    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @param {integer} mailId
     * @returns {mail/static/src/components/mail/mail.js|undefined}
    **/
    mailRefFromId(mailId) {
        return this.mailRefs.find(ref => ref.mail.id === mailId);
    }

    /**
     * Get list of sub-components Mail, ordered based on prop `order`
     * (ASC/DESC).
     *
     * The asynchronous nature of OWL rendering pipeline may reveal disparity
     * between knowledgeable state of store between components. Use this getter
     * with extreme caution!
     *
     * Let's illustrate the disparity with a small example:
     *
     * - Suppose this component is aware of ordered (record) mails with
     *   following IDs: [1, 2, 3, 4, 5], and each (sub-component) mails map
     * each of these records.
     * - Now let's assume a change in store that translate to ordered (record)
     *   mails with following IDs: [2, 3, 4, 5, 6].
     * - Because store changes trigger component re-rendering by their "depth"
     *   (i.e. from parents to children), this component may be aware of
     *   [2, 3, 4, 5, 6] but not yet sub-components, so that some (component)
     *   mails should be destroyed but aren't yet (the ref with mail ID 1)
     *   and some do not exist yet (no ref with mail ID 6).
     *
     * @returns {mail/static/src/components/mail/mail.js[]}
    */
    get mailRefs() {
        const { order } = this._lastRenderedValues();
        const refs = this._getRefs();
        const ascOrderedMailRefs = Object.entries(refs)
            .filter(([refId, ref]) => (
                    // Mail refs have mail local id as ref id, and mail
                    // local ids contain name of model 'mail.mail'.
                    refId.includes(this.env.models['mail.mail'].modelName) &&
                    // Component that should be destroyed but haven't just yet.
                    ref.mail
                )
            )
            .map(([refId, ref]) => ref)
            .sort((ref1, ref2) => (ref1.mail.id < ref2.mail.id ? -1 : 1));

        if (order === 'desc') {
            return ascOrderedMailRefs.reverse();
        }
        return ascOrderedMailRefs;
    }

    /**
     * @returns {mail.mail[]}
    */
    get orderedMails() {
        /**
         * La condizione è stata messa per evitare che venga generato un errore js nel seguente flusso:
         * - l'utente è nella vista "Comunicazioni"
         * - attiva uno qualsiasi dei filtri di ricerca
         * - crea la bozza di un protocollo partendo da una mail
         * - elimina la bozza di protocollo create
         * - ritorna nella vista "Comunicazioni" passando per il menù delle App e non dal breadcrumb
         * TODO: il fix in questione è un workaround momentaneo per evitare il blocco della vista
         */
        if (this.threadView.mailCache === undefined) {
            return [];
        }
        const mailCache = this.threadView.mailCache;

        this.props.order = 'desc';
        if (this.props.order === 'desc') {
            return [...mailCache.orderedMails].reverse();
        }
        return mailCache.orderedMails;
    }

    /**
     * @param {integer} value
    **/
    setScrollTop(value) {
        if (this._getScrollableElement().scrollTop === value) {
            return;
        }
        this._isLastScrollProgrammatic = true;
        this._getScrollableElement().scrollTop = value;
    }

    /**
     * @returns {mail.thread_view}
     */
    get threadView() {
        return this.env.models['mail.thread_view'].get(this.props.threadViewLocalId);
    }

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
    **/
    _checkMostRecentMailIsVisible() {
        const {
            mainCache,
            mailCache,
            threadView,
        } = this._lastRenderedValues();
        if (!threadView || !threadView.exists()) {
            return;
        }
        const lastMailIsVisible =
            mailCache &&
            this.mostRecentMailRef &&
            mailCache === mainCache &&
            this.mostRecentMailRef.isPartiallyVisible();
        if (lastMailIsVisible) {
            threadView.handleVisibleMail(this.mostRecentMailRef.mail);
        }
    }

     /**
     * @param {fl_mail_client.mail} mail
     * @returns {string}
     */
    getDateDay(mail) {
        var mail_date = mail.create_date;
        if (mail.direction == 'in' && mail.server_received_datetime) {
            mail_date = mail.server_received_datetime;
        }
        if (mail.direction == 'out' && mail.sent_datetime) {
            mail_date = mail.sent_datetime;
        }
        if (mail_date.format('YYYY-MM-DD') === moment().format('YYYY-MM-DD')) {
            return this.env._t("Today");
        } else if (
            mail_date.format('YYYY-MM-DD') === moment()
                .subtract(1, 'days')
                .format('YYYY-MM-DD')
        ) {
            return this.env._t("Yesterday");
        }
        return mail_date.format('LL');
    }


    /**
     * @private
     * @returns {Element|undefined} Scrollable Element
    **/
    _getScrollableElement() {
        if (this.props.getScrollableElement) {
            return this.props.getScrollableElement();
        } else {
            return this.el;
        }
    }

    /**
     * @private
     */
    _loadMore() {
        const { mailCache } = this._lastRenderedValues();
        if (!mailCache || !mailCache.exists()) {
            return;
        }
        mailCache.loadMoreMails();
    }

    /**
     * @private
     * @returns {boolean}
     */
    _isLoadMoreVisible() {
        const loadMore = this._loadMoreRef.el;
        if (!loadMore) {
            return false;
        }
        const loadMoreRect = loadMore.getBoundingClientRect();
        const elRect = this._getScrollableElement().getBoundingClientRect();
        const isInvisible = loadMoreRect.top > elRect.bottom || loadMoreRect.bottom < elRect.top;
        return !isInvisible;
    }

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} ev
    **/
    _onClickLoadMore(ev) {
        ev.preventDefault();
        this._loadMore();
    }

    /**
     * @private
     * @param {ScrollEvent} ev
     */
    onScroll(ev) {
        this._onScrollThrottled(ev);
    }

    /**
     * @private
     * @param {ScrollEvent} ev
     */
    _onScrollThrottled(ev) {
        const {
            order,
            orderedMails,
            thread,
            mailCache,
            threadView,
            threadViewer,
        } = this._lastRenderedValues();
        if (!this._getScrollableElement()) {
            // could be unmounted in the meantime (due to throttled behavior)
            return;
        }
        const scrollTop = this._getScrollableElement().scrollTop;
        this.env.messagingBus.trigger('o-component-message-list-scrolled', {
            orderedMails,
            scrollTop,
            thread,
            threadViewer,
        });
        if (threadViewer && threadViewer.exists()) {
            threadViewer.saveMailCacheScrollHeightAsInitial(this._getScrollableElement().scrollHeight, mailCache);
            threadViewer.saveMailCacheScrollPositionsAsInitial(scrollTop, mailCache);
        }
        if (!this._isLastScrollProgrammatic && this._isLoadMoreVisible()) {
            this._loadMore();
        }
        this._checkMostRecentMailIsVisible();
        this._isLastScrollProgrammatic = false;
    }
}

Object.assign(MailList, {
    components,
    defaultProps: {
        order: 'desc',
    },
    props: {
        /**
         * Function returns the exact scrollable element from the parent
         * to manage proper scroll heights which affects the load more mails.
         */
        order: {
            type: String,
            validate: prop => ['asc', 'desc'].includes(prop),
        },
        selectedMailLocalId: {
            type: String,
            optional: true,
        },
        threadViewLocalId: String,
    },
    template: 'fl_mail_client.MailList',
});

return MailList;

});
