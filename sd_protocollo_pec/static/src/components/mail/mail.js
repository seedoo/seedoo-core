odoo.define('sd_protocollo_pec/static/src/components/mail/mail.js', function (require) {
    'use strict';

    const components = {
        Mail: require('fl_mail_client/static/src/components/mail/mail.js'),
    };

    const {patch} = require('web.utils');

    patch(components.Mail, 'sd_protocollo_pec/static/src/components/mail/mail.js', {

        state_mail_protocol_action() {
            if (["mail_da_protocollare", "bozza_da_protocollare", "protocollata"].includes(this.mail.protocollo_action)) {
                return [
                    ["mail_da_protocollare", this.env._t("Protocol to do")],
                    ["bozza_da_protocollare", this.env._t("Protocol draft")],
                    ["protocollata", this.env._t("Protocol done")],
                ];
            } else if (["non_protocollata", "non_protocollabile"].includes(this.mail.protocollo_action)) {
                return [
                    ["non_protocollata", this.env._t("Protocol not done")],
                    ["non_protocollabile", this.env._t("Protocol not to do")],
                ];
            }

        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {MouseEvent} ev
         */
        async _onClickButtonProtocol(ev) {
            ev.stopPropagation();
            this.mail.update({button_crea_bozza_protocollo_invisible: true});
            const call_action = await this.rpc({
                model: 'mail.mail',
                method: "get_call_wizard_condition",
                args: [this.mail.id],
            });
            if (call_action === true) {
                let action = await this.rpc({
                    'model': 'mail.mail',
                    'method': 'protocollo_crea_da_mail_action',
                    'args': [this.mail.id],
                    'kwargs': {}
                });
                return this.env.bus.trigger('do-action', {
                    action: action,
                    options: {
                        on_close: async () => {
                            let mail_read = await this.rpc({
                                'model': 'mail.mail',
                                'method': 'read',
                                'args': [this.mail.id, ['button_crea_bozza_protocollo_invisible']],
                                'kwargs': {}
                            });
                            this.mail.update({
                                button_crea_bozza_protocollo_invisible: mail_read[0].button_crea_bozza_protocollo_invisible
                            });
                        }
                    }
                });
            }
            else {
                const protocollo = await this.rpc({
                    'model': 'mail.mail',
                    'method': 'protocollo_crea_da_mail_action',
                    'args': [this.mail.id],
                    'kwargs': {}
                });
                const action = {
                    type: 'ir.actions.act_window',
                    name: this.env._t("Protocol"),
                    res_model: 'sd.protocollo.protocollo',
                    view_mode: 'form',
                    views: [[false, 'form']],
                    target: 'current',
                    res_id: protocollo["res_id"],
                };
                return this.env.bus.trigger('do-action', {
                    action,
                    options: {
                        on_close: async () => {
                            let mail_read = await this.rpc({
                                'model': 'mail.mail',
                                'method': 'read',
                                'args': [this.mail.id, ['button_crea_bozza_protocollo_invisible']],
                                'kwargs': {}
                            });
                            this.mail.update({
                                button_crea_bozza_protocollo_invisible: mail_read[0].button_crea_bozza_protocollo_invisible
                            });
                        }
                    },
                });
            }
        },

        async _onClickButtonNotToProtocol(ev) {
            ev.stopPropagation();
            await this.rpc({
                model: 'mail.mail',
                method: "non_protocollare_mail_action",
                args: [this.mail.id],
            });
            this.mail.update({button_non_protocollare_invisible: true});
        },

        async _onClickButtonRestoreFromNotRegistered(ev) {
            ev.stopPropagation();
            await this.rpc({
                model: 'mail.mail',
                method: "ripristina_da_non_protocollata_action",
                args: [this.mail.id],
            });
            this.mail.update({button_ripristina_da_non_protocollata_invisible: true});
        },

        async _onClickButtonRestoreFromRegistered(ev) {
            ev.stopPropagation();
            await this.rpc({
                model: 'mail.mail',
                method: "ripristina_da_protocollata_action",
                args: [this.mail.id],
            });
            this.mail.update({button_ripristina_da_protocollata_invisible: true});
        },



    });

});