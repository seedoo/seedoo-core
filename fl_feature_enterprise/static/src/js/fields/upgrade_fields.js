odoo.define('fl_feature_enterprise.fl_upgrade_widgets', function (require) {
"use strict";

/**
 *  The upgrade widgets are intended to be used in config settings.
 *  When checked, an upgrade popup is showed to the user.
 */

var AbstractField = require('web.AbstractField');
var basic_fields = require('web.basic_fields');
var core = require('web.core');
var Dialog = require('web.Dialog');
var field_registry = require('web.field_registry');
var framework = require('web.framework');
var relational_fields = require('web.relational_fields');

var _t = core._t;
var QWeb = core.qweb;

var FieldBoolean = basic_fields.FieldBoolean;
var FieldRadio = relational_fields.FieldRadio;


/**
 * Mixin that defines the common functions shared between Boolean and Radio
 * upgrade widgets
 */
var AbstractFieldUpgrade = {
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Redirects the user to the upgrade page
     *
     * @private
     * @returns {Promise}
     */
    _confirmUpgrade: function () {
        window.open("https://www.flosslab.com/", "_blank");
    },
    /**
     * This function is meant to be overridden to insert the 'Enterprise' label
     * JQuery node at the right place.
     *
     * @abstract
     * @private
     * @param {jQuery} $enterpriseLabel the 'Enterprise' label to insert
     */
    _insertEnterpriseLabel: function ($enterpriseLabel) {},
    /**
     * Opens the Upgrade dialog.
     *
     * @private
     * @returns {Dialog} the instance of the opened Dialog
     */
    _openDialog: function () {
        var message = $(QWeb.render('FLEnterpriseUpgrade'));

        var buttons = [
            {
                text: _t("Vai al sito"),
                classes: 'btn-primary',
                close: true,
                click: this._confirmUpgrade.bind(this),
            },
            {
                text: _t("Annulla"),
                close: true,
            },
        ];

        return new Dialog(this, {
            size: 'medium',
            buttons: buttons,
            $content: $('<div>', {
                html: message,
            }),
            title: _t("Versione Enterprise"),
        }).open();
    },

};

var FLUpgradeBoolean = FieldBoolean.extend(AbstractFieldUpgrade, {
    supportedFieldTypes: [],
    events: _.extend({}, AbstractField.prototype.events, {
        'click input': '_onInputClicked',
    }),
    /**
     * Re-renders the widget with the label
     *
     * @param {jQuery} $label
     */
    renderWithLabel: function ($label) {
        this.$label = $label;
        this._render();
    },

    _onInputClicked: function (event) {
        self = this
        this._setValue(!this.value)
        this._rpc({
                model: 'ir.module.module',
                method: 'show_dialog_on_checkbox_click',
                args: [[this.name]],
            })
            .then(function (result) {
                if ($(event.currentTarget).prop("checked") && result === true) {
                    self._openDialog().on('closed', self, self._resetValue.bind(self));
                }
            });

    },


    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _resetValue: function () {
        this.$input.prop("checked", false).change();
        this._setValue(false)
    },
});

field_registry
    .add('fl_upgrade_boolean', FLUpgradeBoolean)

});
