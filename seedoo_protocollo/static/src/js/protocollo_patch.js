openerp.seedoo_protocollo = function(instance) {

    // Models for which we'll hide create and duplicate buttons
    var MODELS_TO_HIDE = ['protocollo.protocollo'];

    // Hide the save button on form views
    instance.web.FormView.include({
        load_form: function(data) {
            var self = this;

            var ret = this._super.apply(this, arguments);
            var res_model = this.dataset.model;
            if ($.inArray(res_model, MODELS_TO_HIDE) != -1) {
                //Limitare ai protocolli Registrati
                //this.$buttons.find('button.oe_form_button_edit').remove();
            };
            return ret;
        },
    });

};