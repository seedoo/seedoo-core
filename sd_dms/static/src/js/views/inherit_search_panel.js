odoo.define('sd_dms/static/src/js/views/search_panel.js', function (require) {
'use strict';


var rpc = require("web.rpc");
const components = {
    SearchPanel: require("web/static/src/js/views/search_panel.js"),
};

const { patch } = require('web.utils');

patch(components.SearchPanel, 'sd_dms/static/src/js/views/search_panel.js', {

        async willStart() {
            this._expandDefaultValue();
            this._updateActiveValues();

            // Imposta lato client un default value per il search_panel
            const sections = this.model.get("sections")

            let uid = this.env.__proto__.__proto__.session.uid
            let defaultFolder;
            await rpc.query({
                model: 'res.users',
                method: 'get_default_folder_for_documents',
                args: [[uid]],
            }).then((result) => defaultFolder = result);

            for (const section of sections) {
                if (section.fieldName === "folder_id") {
                    await this._toggleCategory(section, section.values.get(defaultFolder["folder_id"]))
                }
            }
        }

    });
});