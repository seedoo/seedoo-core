/* This file is part of Seedoo.  The COPYRIGHT file at the top level of
this module contains the full copyright notices and license terms. */

openerp.web_pdf_widget = function(instance)
 {

    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var _lt = instance.web._lt;
     instance.web_pdf_widget.FieldBinaryPdf = instance.web.form.FieldBinary.extend({
        template: 'pdfviewer',
        initialize_content: function() {
            this._super();
            this.max_upload_size = 120 * 1024 * 1024; // 120Mo
        },
        render_value: function() {
            var self = this;
            var url;
            if (this.get('value') && !instance.web.form.is_bin_size(this.get('value'))) {
                var blob = b64toBlob(this.get('value'), 'application/pdf');
                var blobUrl = URL.createObjectURL(blob);
                url = blobUrl;
            } else if (this.get('value')) {
                var id = JSON.stringify(this.view.datarecord.id || null);
                var field = this.name;
                url = this.session.url('/web/binary/pdf', {
                                            model: this.view.dataset.model,
                                            id: id,
                                            field: field,
                                            t: (new Date().getTime()),
                });
            } else {
                var field = this.name;
                url = this.session.url('/web/binary/pdf', {
                                            model: this.view.dataset.model,
                                            field: field,
                                            t: (new Date().getTime()),

            });
            }
            var $preview= self.$el.find('.pdfviewer_media');
            var $view = $('<object data="'+url+'" type="application/pdf" width="100%" height="100%"></object>')
            width_n = "100%";
            height_n = "1200";
            $view.css('width',width_n);
            $view.css('height',height_n);
            $preview.empty();
            $preview.append($view);
        },
        on_file_uploaded_and_valid: function(size, name, content_type, file_base64) {
            this.internal_set_value(file_base64);
            this.binary_value = true;
            this.render_value();
            this.set_filename(name);
        },
        on_clear: function() {
            this._super.apply(this, arguments);
            this.render_value();
            this.set_filename('');
        },
    });

    function b64toBlob(b64Data, contentType) {
        contentType = contentType || '';
        var sliceSize = 1024;

        var byteCharacters = atob(b64Data);
        var byteArrays = [];

        for (var offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            var slice = byteCharacters.slice(offset, offset + sliceSize);

            var byteNumbers = new Array(slice.length);
            for (var i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            var byteArray = new Uint8Array(byteNumbers);

            byteArrays.push(byteArray);
        }

        var blob = new Blob(byteArrays, {type: contentType});
        return blob;
    }


    instance.web.form.widgets.add('pdfviewer', 'instance.web_pdf_widget.FieldBinaryPdf');


};


