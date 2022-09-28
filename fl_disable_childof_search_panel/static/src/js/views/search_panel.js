odoo.define('fl_disable_childof_search_panel/static/src/js/views/search_panel.js', function (require) {
'use strict';

const components = {
    SearchPanel: require("web/static/src/js/views/search_panel.js"),
};

const { patch } = require('web.utils');

patch(components.SearchPanel, 'fl_disable_childof_search_panel/static/src/js/views/search_panel.js', {

        /**
         * Prevent unnecessary calls to the model by ensuring a different category
         * is clicked.
         * @private
         * @param {Object} category
         * @param {Object} value
         */
        async _toggleCategory(category, value) {
            /**********************************************************************************************************/
            let expanded = true;
            //if (value.childrenIds.length) {
            if (value.childrenIds.length || 'children_count' in value) {
            /**********************************************************************************************************/
                const categoryState = this.state.expanded[category.id];
                if (categoryState[value.id] && category.activeValueId === value.id) {
                    delete categoryState[value.id];
                    /**************************************************************************************************/
                    expanded = false;
                    /**************************************************************************************************/
                } else {
                    categoryState[value.id] = true;
                    /**************************************************************************************************/
                    expanded = true;
                    /**************************************************************************************************/
                }
            }
            /**********************************************************************************************************/
            // if (category.activeValueId !== value.id) {
            //     this.state.active[category.id] = value.id;
            //     this.model.dispatch("toggleCategoryValue", category.id, value.id);
            // }
            this.state.active[category.id] = value.id;
            this.model.dispatch("toggleCategoryValue", category.id, value.id, expanded);
            /**********************************************************************************************************/
        }

    });
});