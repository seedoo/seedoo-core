odoo.define('fl_mail_client/static/src/models/thread_view/thread_viewer.js', function (require) {
    'use strict';

    const {
        registerInstancePatchModel,
        registerFieldPatchModel
    } = require('mail/static/src/model/model_core.js');

    const {attr, many2one} = require('mail/static/src/model/model_field.js');

    registerInstancePatchModel('mail.thread_viewer', 'fl_mail_client/static/src/models/thread_view/thread_viewer.js', {

        //----------------------------------------------------------------------
        // Public
        //----------------------------------------------------------------------

        /**
         * @param {integer} scrollHeight
         * @param {fl_mail_client.mail_cache} mailCache
         */
        saveMailCacheScrollHeightAsInitial(scrollHeight, mailCache) {
            mailCache = mailCache || this.mailCache;
            if (!mailCache) {
                return;
            }
            this.update({
                mailCacheInitialScrollHeights: Object.assign({}, this.mailCacheInitialScrollHeights, {
                    [mailCache.localId]: scrollHeight,
                }),
            });
        },

        /**
         * @param {integer} scrollTop
         * @param {fl_mail_client.mail_cache} mailCache
         */
        saveMailCacheScrollPositionsAsInitial(scrollTop, mailCache) {
            mailCache = mailCache || this.mailCache;
            if (!mailCache) {
                return;
            }
            if (this.chatter) {
                // Initial scroll position is disabled for chatter because it is
                // too complex to handle correctly and less important
                // functionally.
                return;
            }
            this.update({
                mailCacheInitialScrollPositions: Object.assign({}, this.mailCacheInitialScrollPositions, {
                    [mailCache.localId]: scrollTop,
                }),
            });
        },

         /**
         * @private
         * @returns {fl_mail_client.mail_cache|undefined}
         */
        _computeMailCache() {
            if (!this.thread) {
                return [['unlink']];
            }
            return [['link', this.thread.mail_cache(this.stringifiedDomain)]];
        }

    });

    registerFieldPatchModel('mail.thread_viewer', 'fl_mail_client/static/src/models/thread_view/thread_viewer.js', {

        /**
         * States the `fl_mail_client.mail_cache` that should be displayed by `this`.
         */
        mailCache: many2one('fl_mail_client.mail_cache', {
            compute: '_computeMailCache',
            dependencies: [
                'stringifiedDomain',
                'thread',
            ],
        }),

        mailCacheInitialScrollHeights: attr({
            default: {},
        }),

        mailCacheInitialScrollPositions: attr({
            default: {},
        }),
    });

});
