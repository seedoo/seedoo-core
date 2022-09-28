odoo.define('fl_mail_client/static/src/components/thread_view/thread_view.js', function (require) {
'use strict';

/****
  * Extends ThreadView component to manage through Discuss, the MailList (a list of mail.mail object)
  * in a similar way to what was done with Messagelist
*****/

const components = {
    ThreadView: require('mail/static/src/components/thread_view/thread_view.js'),
    MailList: require('fl_mail_client/static/src/components/mail_list/mail_list.js'),
};

Object.assign(components.ThreadView.components, {
    MailList: components.MailList,
});


});
