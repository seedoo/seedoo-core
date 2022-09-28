odoo.define('fl_mail_client/static/src/components/discuss_sidebar_item/discuss_sidebar_item.js', function (require) {
'use strict';

const components = {
    DiscussSidebarItem: require('mail/static/src/components/discuss_sidebar_item/discuss_sidebar_item.js'),
};

const { patch } = require('web.utils');

patch(components.DiscussSidebarItem, 'fl_mail_client/static/src/components/discuss_sidebar_item/discuss_sidebar_item.js', {

        /**
         * @private
         * @param {MouseEvent} ev
         */
        _onClick(ev) {
            // il domain della ricerca deve essere resettato se almeno uno dei seguenti due casi è vero:
            // - caso1: sì clicca sull'item 'mail.box_mailreceived' e il thread corrente è diverso da 'mailreceived'
            // - caso2: sì clicca sull'item 'mail.box_mailsent' e il thread corrente è diverso da 'mailsent'
            let caso1 = this.discuss.activeId=='mail.box_mailreceived' && this.thread.id!='mailreceived';
            let caso2 = this.discuss.activeId=='mail.box_mailsent' && this.thread.id!='mailsent';
            if (caso1 || caso2) {
                this.discuss.update({
                    stringifiedDomain: '[]'
                });
            }
            // si impostano a 0 i contatori dei menù
            if (this.thread.id === 'mailreceived') {
                this.env.messaging.received.update({counter: 0});
            }
            if (this.thread.id === 'mailsent') {
                this.env.messaging.sent.update({counter: 0});
            }
            return this._super(...arguments);
        }

    });
});