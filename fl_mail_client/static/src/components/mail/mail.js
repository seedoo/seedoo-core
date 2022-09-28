odoo.define('fl_mail_client/static/src/components/mail/mail.js', function (require) {
'use strict';

/****
 *
 * It applies the Message component concept to mail.mail object
 *
*****/

const components = {
        AttachmentList: require('mail/static/src/components/attachment_list/attachment_list.js'),
};
const { Component, useState } = owl;
const { getLangDatetimeFormat } = require('web.time');
const useShouldUpdateBasedOnProps = require('mail/static/src/component_hooks/use_should_update_based_on_props/use_should_update_based_on_props.js');
const useStore = require('mail/static/src/component_hooks/use_store/use_store.js');
const useUpdate = require('mail/static/src/component_hooks/use_update/use_update.js');
const { useRef } = owl.hooks;

class Mail extends Component {

    /**
     * @override
     */
    constructor(...args) {
        super(...args);
        this.state = useState({
            isClicked: false,
        });
        useShouldUpdateBasedOnProps();
        useStore(props => {
            const mail = this.env.models['fl_mail_client.mail'].get(props.mailLocalId);
            const author = mail ? mail.author : undefined;
            const threadView = this.env.models['mail.thread_view'].get(props.threadViewLocalId);
            const thread = threadView ? threadView.thread : undefined;
            return {
                attachments: mail
                    ? mail.attachments.map(attachment => attachment.__state)
                    : [],
                author,
                mail: mail ? mail.__state : undefined,
                thread,
            }
        });
        useUpdate({ func: () => this._update() });

        /**
         * Value of the last rendered prettyBody. Useful to compare to new value
         * to decide if it has to be updated.
         */
        this._lastPrettyBody;
        /**
         * Reference to element containing the prettyBody. Useful to be able to
         * replace prettyBody with new value in JS (which is faster than t-raw).
         */
        this._prettyBodyRef = useRef('prettyBody');
    }

    /**
     * @returns {fl_mail_client.mail}
     */
    get mail() {
        return this.env.models['fl_mail_client.mail'].get(this.props.mailLocalId);
    }

    /**
     * Get the received date time of the mail at current user locale time.
     *
     * @returns {string}
     */
    get server_received_datetime_formatted() {
        return this.mail.server_received_datetime.format(getLangDatetimeFormat());
    }

    /**
     * Get the received sent date time of the mail at current user locale time.
     *
     * @returns {string}
     */
    get sent_datetime_formatted() {
        return this.mail.sent_datetime.format(getLangDatetimeFormat());
    }

    /**
     * Get state list for sent emails.
     *
     * @returns {list}
     */
    get state_out_list() {
        return [
            ['outgoing', this.env._t('Outgoing')],
            ['sent', this.env._t('Sent')],
            ['accepted', this.env._t('Accepted')],
            ['received', this.env._t('Received')],
            ['exception', this.env._t('Delivery Failed')],
            ['cancel', this.env._t('Cancelled')]
        ];
    }

    /**
     * @private
     */
    _update() {
        if (!this.mail) {
            return;
        }
        if (this._prettyBodyRef.el && this.mail.prettyBody !== this._lastPrettyBody) {
            this._prettyBodyRef.el.innerHTML = this.mail.prettyBody;
            this._lastPrettyBody = this.mail.prettyBody;
        }
    }

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onClick(ev) {
        this.el.querySelector('.o_Message_footer').classList.toggle("not_visible");

        $('.nav-pills a').click(function(){
            var tabs = document.querySelectorAll('.tab-content>.tab-pane');
            for (var k = 0; k < tabs.length; k++) {
                tabs[k].className = "tab-pane";
            }
            var linkTab = this.getAttribute("aria-controls");
            var tab = document.querySelectorAll('.tab-content>' + linkTab)[0];
            tab.className = "tab-pane active";
        })
    };
}

Object.assign(Mail, {
    components,
    defaultProps: {
    },
    props: {
        mailLocalId: String,
        threadViewLocalId: {
            type: String,
            optional: true,
        },
    },
    template: 'fl_mail_client.Mail',
});

return Mail;

});
