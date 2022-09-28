odoo.define('fl_base.AbstractWebClient', function (require) {
    "use strict";

    var WebClient = require('web.AbstractWebClient');

    // Estensione del metodo _onDisplayWarning per evitare di chiamare il wizard di errore
    WebClient.include({
        _onDisplayWarning: function (e) {
            self = this
            const dataTypeArray = e.data.type.split(",");
            if (!(dataTypeArray.length > 1 && dataTypeArray[0] === 'action')) {
                this._super.apply(this, arguments);
            }
        }
    });

});
