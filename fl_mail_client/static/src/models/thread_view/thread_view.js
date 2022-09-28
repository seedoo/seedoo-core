odoo.define('fl_mail_client/static/src/models/thread_view/thread_view.js', function (require) {
    'use strict';

    const {
        registerClassPatchModel,
        registerInstancePatchModel,
        registerFieldPatchModel
    } = require('mail/static/src/model/model_core.js');

    const { clear } = require('mail/static/src/model/model_field_command.js');
    const {attr, many2one, one2one, one2many} = require('mail/static/src/model/model_field.js');

    registerInstancePatchModel('mail.thread_view', 'mail/static/src/models/thread_view/thread_view.js', {
            /**
         * @private
         * @returns {integer|undefined}
         */
        _computeMailCacheInitialScrollHeight() {
            if (!this.mailCache) {
                return clear();
            }
            const mailCacheInitialScrollHeight = this.mailCacheInitialScrollHeights[this.mailCache.localId];
            if (mailCacheInitialScrollHeight !== undefined) {
                return mailCacheInitialScrollHeight;
            }
            return clear();
        },

        /**
         * @private
         * @returns {integer|undefined}
         */
        _computeMailCacheInitialScrollPosition() {
            if (!this.mailCache) {
                return clear();
            }
            const mailCacheInitialScrollPosition = this.mailCacheInitialScrollPositions[this.mailCache.localId];
            if (mailCacheInitialScrollPosition !== undefined) {
                return mailCacheInitialScrollPosition;
            }
            return clear();
        }
    });

    registerFieldPatchModel('mail.thread_view', 'mail/static/src/models/thread_view/thread_view.js', {
        /**
         * States the `fl_mail_client.mail_cache` currently displayed by `this`.
         */
        mailCache: many2one('fl_mail_client.mail_cache', {
            inverse: 'threadViews',
            related: 'threadViewer.mailCache',
        }),
        /**
         * List of saved initial scroll heights of mail caches.
         */
        mailCacheInitialScrollHeights: attr({
            default: {},
            related: 'threadViewer.mailCacheInitialScrollHeights',
        }),
        /**
         * List of saved initial scroll positions of mail caches.
         */
        mailCacheInitialScrollPositions: attr({
            default: {},
            related: 'threadViewer.mailCacheInitialScrollPositions',
        }),
        mailCacheInitialScrollHeight: attr({
            compute: '_computeMailCacheInitialScrollHeight',
            dependencies: [
                'mailCache',
                'mailCacheInitialScrollHeights',
            ],
        }),
        mailCacheInitialScrollPosition: attr({
            compute: '_computeMailCacheInitialScrollPosition',
            dependencies: [
                'mailCache',
                'mailCacheInitialScrollPositions',
            ],
        }),
    });

});
