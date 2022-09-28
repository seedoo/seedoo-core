odoo.define('sd_protocollo_pec/static/src/models/messaging_notification_handler/messaging_notification_handler.js', function (require) {
    'use strict';

    const { registerInstancePatchModel } = require('mail/static/src/model/model_core.js');

    registerInstancePatchModel('mail.messaging_notification_handler', 'sd_protocollo_pec/static/src/models/messaging_notification_handler/messaging_notification_handler.js', {

        async _beforeLoadMail(data, hintType) {
            if (hintType == 'mail-received') {
                const mailsData = await this.env.services.rpc({
                    'model': 'mail.mail',
                    'method': 'read',
                    'args': [data.id, [
                        'button_crea_bozza_protocollo_invisible',
                        'button_non_protocollare_invisible',
                        'button_ripristina_da_non_protocollata_invisible',
                        'button_ripristina_da_protocollata_invisible',
                    ]],
                    'kwargs': {}
                });
                data.button_crea_bozza_protocollo_invisible = mailsData[0].button_crea_bozza_protocollo_invisible;
                data.button_non_protocollare_invisible = mailsData[0].button_non_protocollare_invisible;
                data.button_ripristina_da_non_protocollata_invisible = mailsData[0].button_ripristina_da_non_protocollata_invisible;
                data.button_ripristina_da_protocollata_invisible = mailsData[0].button_ripristina_da_protocollata_invisible;
            }
        }

    });

});