odoo.define('sd_protocollo_pec/static/src/models/mail/mail.js', function (require) {
    'use strict';

    const {
        registerClassPatchModel,
        registerFieldPatchModel,
    } = require('mail/static/src/model/model_core.js');
    const { attr } = require('mail/static/src/model/model_field.js');

    registerClassPatchModel('fl_mail_client.mail', 'sd_protocollo_pec/static/src/models/mail/mail.js', {

        //----------------------------------------------------------------------
        // Public
        //----------------------------------------------------------------------

        /**
         * @override
         */
        convertData(data) {
            const data2 = this._super(data);

            if ('button_crea_bozza_protocollo_invisible' in data) {
                data2.button_crea_bozza_protocollo_invisible = data.button_crea_bozza_protocollo_invisible;
            }

            if ('button_non_protocollare_invisible' in data) {
                data2.button_non_protocollare_invisible = data.button_non_protocollare_invisible;
            }

            if ('button_ripristina_da_non_protocollata_invisible' in data) {
                data2.button_ripristina_da_non_protocollata_invisible = data.button_ripristina_da_non_protocollata_invisible;
            }


            if ('button_ripristina_da_protocollata_invisible' in data) {
                data2.button_ripristina_da_protocollata_invisible = data.button_ripristina_da_protocollata_invisible;
            }

            if ('protocollo_action' in data) {
                data2.protocollo_action = data.protocollo_action;
            }

            return data2;
        },

    });

    registerFieldPatchModel('fl_mail_client.mail', 'sd_protocollo_pec/static/src/models/mail/mail.js', {

        button_crea_bozza_protocollo_invisible: attr({
            default: true,
        }),
        button_non_protocollare_invisible: attr({
            default: true,
        }),

        button_ripristina_da_non_protocollata_invisible: attr({
            default: true,
        }),

        button_ripristina_da_protocollata_invisible: attr({
            default: true,
        }),
        protocollo_action: attr(),
    });

});