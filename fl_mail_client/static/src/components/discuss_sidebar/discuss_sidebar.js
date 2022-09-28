odoo.define('fl_mail_client/static/src/components/discuss_sidebar/discuss_sidebar.js', function (require) {
'use strict';

const components = {
    DiscussSidebar: require('mail/static/src/components/discuss_sidebar/discuss_sidebar.js'),
};

const { patch } = require('web.utils');

patch(components.DiscussSidebar, 'fl_mail_client/static/src/components/discuss_sidebar/discuss_sidebar.js', {


        /**
         * Return the list of maillist.
         *
         * @returns {mail.thread[]}
         */
        getMailListSidebarItems() {
            const res = this.env.models['mail.thread']
                .all(thread =>
                    thread.isPinned &&
                    thread.model === 'mail.box' &&
                    thread.id.startsWith('mail')
                );
            return res;
        },

        /**
         * Called when clicking on Mail compose menu item.
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onClickMailCompose(ev) {
            ev.stopPropagation();
            return this.env.bus.trigger('do-action', {
                action: 'fl_mail_client.action_wizard_mail_compose_message_form',
                options: {
                    additional_context: {
                        mail_compose_message: true,
                    },
                },
            });
        }


    });
});