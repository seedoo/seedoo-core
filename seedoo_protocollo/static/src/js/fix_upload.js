openerp.seedoo_protocollo = function(instance) {

    instance.web.form.FieldBinary.include({
        template: 'fieldBinary',

        init: function(field_manager, node) {
            var self = this;
            this._super(field_manager, node);
            this.binary_value = false;
            this.useFileAPI = !!window.FileReader;
            try {
                this.max_file_size = parse_human_size(this.options.max_file_size);
            } catch(e) {
                this.max_file_size = 0;
            }

            if (!this.useFileAPI) {
                this.fileupload_id = _.uniqueId('oe_fileupload');
                $(window).on(this.fileupload_id, function() {
                    var args = [].slice.call(arguments).slice(1);
                    self.on_file_uploaded.apply(self, args);
                });
            }
        },

        initialize_content: function() {
            this._super();

            var self = this;
            $('.taballegati input.oe_form_binary_file').on('change', function(e) {
                /**
                 * Si modifica il valore del campo per forzare l'evento di change nella lista. Infatti, quando si
                 * aggiunge una nuova riga al tree, il campo binary rimane valorizzato con i valori della vecchia riga
                 * e di conseguenza non viene attivato l'evento di change. Se tale evento non viene scaturito, il campo
                 * rimane vuoto e non viene data indicazione all'utente sul problema verificatosi.
                 **/
                $(this).val('');
                self.on_file_change(e);
            });
        },

        on_file_change: function(e) {
            var self = this;
            var file_node = e.target;
            if ((this.useFileAPI && file_node.files.length) || (!this.useFileAPI && $(file_node).val() !== '')) {
                if (this.useFileAPI) {
                    var file = file_node.files[0];
                    if (this.max_file_size && file.size > this.max_file_size) {
                        var msg = _t("The selected file exceed the maximum file size of %s.");
                        instance.webclient.notification.warn(_t("File upload"), _.str.sprintf(msg, instance.web.human_size(this.max_file_size)));
                        return false;
                    }
                    var filereader = new FileReader();
                    filereader.readAsDataURL(file);
                    filereader.onloadend = function(upload) {
                        var data = upload.target.result;
                        data = data.split(',')[1];
                        self.on_file_uploaded(file.size, file.name, file.type, data);
                    };
                } else {
                    this.$el.find('form.oe_form_binary_form input[name=session_id]').val(this.session.session_id);
                    this.$el.find('form.oe_form_binary_form').submit();
                }
                this.$el.find('.oe_form_binary_progress').show();
                this.$el.find('.oe_form_binary').hide();
            }
        }
    });




};

function parse_human_size(size) {
    var units = "bkmgtpezy".split('');
    var parsed = size.toString().match(/^([0-9\.,]*)(\s*)?([a-z]{1,2})?$/i);
    if (parsed === null) {
        throw("Could not parse: " + size);
    }
    var amount = parseFloat(parsed[1].replace(',', '.'));
    if (isNaN(amount) || !isFinite(amount)) {
        throw("Invalid amount: " + size);
    }
    var unit = parsed[3] ? parsed[3][0].toLowerCase() : '';
    var index = units.indexOf(unit);
    if (unit && index === -1) {
        throw("Invalid unit: " + size);
    }
    if (index > 0) {
        amount = amount * Math.pow(1024, index);
    }
    return amount;
}

