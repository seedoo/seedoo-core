odoo.define('fl_mail_client/static/src/models/partner/partner.js', function (require) {
    'use strict';
    const {
        attr
    } = require('mail/static/src/model/model_field.js');
    const {
        registerClassPatchModel,
        registerFieldPatchModel,
    } = require('mail/static/src/model/model_core.js');

registerFieldPatchModel('mail.partner', 'fl_mail_client_mail/static/src/models/partner/partner.js', {
    is_fl_mail_reader_writer: attr(),
    has_compose_permission: attr(),
});

registerClassPatchModel('mail.partner', 'mail/static/src/models/partner/partner.js', {

/**
 * @override
 */
convertData(data) {
    const data2 = this._super(data);
    if ('is_fl_mail_reader_writer' in data) {
        data2.is_fl_mail_reader_writer = data.is_fl_mail_reader_writer;
    }
    if ('has_compose_permission' in data) {
        data2.has_compose_permission = data.has_compose_permission;
    }
    return data2;
}
});

});