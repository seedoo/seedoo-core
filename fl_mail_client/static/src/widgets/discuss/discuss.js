odoo.define('fl_mail_client/static/src/widgets/discuss/discuss.js', function (require) {
    'use strict';

    const components = {
        DiscussSidebar: require('mail/static/src/widgets/discuss/discuss.js'),
    };

    const { patch } = require('web.utils');
    const rpc = require('web.rpc');

    patch(components.DiscussSidebar, 'fl_mail_client/static/src/widgets/discuss/discuss.js', {

        /**
         * @override
         * si estende la function di start per recuperare l'id della vista di ricerca che è stata creata dal modulo
         * fl_mail_client
         */
        start: async function () {
            await this._super(...arguments);
            if (!this.mailSearchReceivedViewId) {
                let mailSearchReceivedViewId;
                await rpc.query({
                    model: 'ir.model.data',
                    method: 'xmlid_to_res_model_res_id',
                    args: ['fl_mail_client.view_mail_mail_search_received'],
                }).then(function (data) {
                    mailSearchReceivedViewId = data[1];
                });
                this.mailSearchReceivedViewId = mailSearchReceivedViewId;
            }
            if (!this.mailSearchSentViewId) {
                let mailSearchSentViewId;
                await rpc.query({
                    model: 'ir.model.data',
                    method: 'xmlid_to_res_model_res_id',
                    args: ['fl_mail_client.view_mail_mail_search_sent'],
                }).then(function (data) {
                    mailSearchSentViewId = data[1];
                });
                this.mailSearchSentViewId = mailSearchSentViewId;
            }
        },

        /**
         * @override
         * @private
         * si estende la function per intercettare l'evento di click sui vari menu item presenti nella sidebar in modo
         * da poter verificare ed eventualmente caricare la corretta vista di ricerca
         */
        _pushStateActionManager() {
            this._super(...arguments);
            this._reloadSearchView();
        },

        /**
         * @private
         * la function si occupa di caricare la vista di ricerca corretta a seconda del thread selezionato: se il thread
         * è box_mailreceived o box_mailsent allora si carica la vista di ricerca delle mail altrimenti non si imposta
         * nessuna vista di ricerca e automaticamente si prenderà quella di default per il modello message
         */
        _reloadSearchView: async function () {
            if (this.discuss.activeId==='mail.box_mailreceived') {
                this.viewId = this.mailSearchReceivedViewId;
                this.searchModelConfig.modelName = 'mail.mail';
            } else if (this.discuss.activeId==='mail.box_mailsent') {
                this.viewId = this.mailSearchSentViewId;
                this.searchModelConfig.modelName = 'mail.mail';
            } else {
                if (this.searchModelConfig.modelName == 'mail.message') {
                    return;
                }
                this.viewId = undefined;
                this.searchModelConfig.modelName = 'mail.message';
            }
            if (this.hasControlPanel) {
                this._controlPanelWrapper.destroy();
            }
            await this.willStart();
            await this.start();
            this.on_attach_callback();
        }

    });
});