odoo.define('sd.protocollo.Dashboard', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var WebClient = require('web.web_client');
    const {Component} = owl;

    var _t = core._t;

    var SDProtocolloDashboard = AbstractAction.extend({
        hasControlPanel: true,
        events: {
            "click .sd-button": "_onClickKanbanButton",
            "click tr.o_odoo_model": "on_odoo_model",
        },


        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.set('title', action.name || _t('Dashboard'));
        },

        /**
         * @private
         * @param {MouseEvent} event
         */
        _onClickKanbanButton: function (event) {
            var self = this;
            var data = $(event.currentTarget).data();

            var parameters = {
                action_name: data.actionName || [],
                action_context: data.actionContext || [],
            }
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            return this._rpc({
                route: "/protocollo/dashboard/list",
                params: parameters,
            }).then(function (action) {
                self.do_action(action, options);
            });
        },

        /**
         * Refresh the DOM html
         *
         * @private
         * @param {string|html} dom
         */
        _refreshPageWithNewHtml: function (dom) {
            var $dom = $(dom);
            this.$el.html($dom);
        },

        /**
         *  Start è il metodo che viene chiamato dopo init, willStart
         *  Chiama il controller di odoo che restituisce il template valorizzato sotto forma di html
         */
        start: function () {
            var self = this;

            return self._rpc({
                route: "/protocollo/dashboard",
            }).then(function (response) {
                self._refreshPageWithNewHtml(response.html_content);
            });
        },

        // Breadcrumb navigation processing
        on_reverse_breadcrumb: function () {
            var self = this;
            WebClient.do_push_state({});
            self.start();
        },

    });

    core.action_registry.add('sd.protocollo.dashboard', SDProtocolloDashboard);

    return SDProtocolloDashboard;
});

