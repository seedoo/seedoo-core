openerp.seedoo_protocollo = function(instance) {

    // Models for which we'll hide create and duplicate buttons
    var MODELS_TO_HIDE = ['protocollo.protocollo'];
    var tab_selector = 'div[class="dati-protocollo-container"]';

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

        save: function(data) {
            res = this._super.apply(this, arguments);
            $(tab_selector).each(function(i, tab) {
                var inv = $(tab).find('.oe_form_invalid')
                if(inv.length > 0){
                    $(tab).find("h4").addClass('oe_form_accordion_tab_invalid');
                    var acc_content = $(tab).find(".accordion-content")
                    if (acc_content.css("display") == "none")
                        acc_content.slideToggle('fast');
                    // $(this).addClass("accordion-selected");

                }
                else{
                    $(tab).find("h4").removeClass('oe_form_accordion_tab_invalid');
                }
            });
            return res;
        },

    });

};