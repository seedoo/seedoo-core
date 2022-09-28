odoo.define('fl_base.BasicModel', function (require) {
    "use strict";

    var BasicModel = require('web.BasicModel');

    // Estensione del metodo _performOnChange triggherato dall'onchange per poter restituire una action:
    // in python, lato onchange, sarà presente il solito warning con l'aggiunta al suo interno del type.
    // es. "type": "action,module.name_action_xml".  se presente ne viene fatto uno split e verrà restituita la action in
    // posizione dataSplit[1]
    BasicModel.include({
        async _performOnChange(record, fields, options = {}) {
            self = this
            var result = await this._super.apply(this, arguments);
            // verifica della presenza di un risultato
            if (result && result.warning && result.warning.type) {
                const dataTypeArray = result.warning.type.split(",");

                if (dataTypeArray.length > 1 && dataTypeArray[0] === 'action') {
                    this.save(record.id,{
                        "reload": true,
                        "savePoint": false
                    })
                    var parentForm = this.__parentedParent;
                    parentForm._disableButtons();
                    parentForm.saveRecord(parentForm.handle, {
                        stayInEdit: true,
                    }).then(
                         result => {
                            parentForm._enableButtons()
                            // Recupero del context
                            const ctxOptions = {full: true};
                            if (fields.length === 1) {
                                fields = fields[0];
                                ctxOptions.fieldName = fields;
                            }
                            var context = this._getContext(record, ctxOptions);
                            // chiamata rpc per mostrare la action
                            this._rpc({
                                route: '/web/action/load',
                                params: {
                                    action_id: dataTypeArray[1],
                                }
                            }).then(function (r) {
                                // aggiornamento del context e res_id con chiamata della action
                                r.context = context
                                r.res_id = self.eid;
                                return self.do_action(r,{
                                    on_close: function (result)
                                    {
                                        // reload del form una volta completata la action del wizard
                                        parentForm.reload();
                                    }
                                });
                            });
                        });
                }
            }
            return result;
        }
    });

});
