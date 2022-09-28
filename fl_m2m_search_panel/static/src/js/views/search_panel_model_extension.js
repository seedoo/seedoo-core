odoo.define("fl_m2m_search_panel/static/src/js/views/search_panel_model_extension.js", function (require) {
    "use strict";

    const ActionModel = require("web/static/src/js/views/action_model.js");
    const SearchPanelModelExtension = require("web/static/src/js/views/search_panel_model_extension.js");

    /**
     * @property {{ sections: Map<number, Section> }} state
     * @extends ActionModel.Extension
     */
    class SearchPanelModelExtensionM2m extends SearchPanelModelExtension {

        /**
         * Computes and returns the domain based on the current active
         * categories. If "excludedCategoryId" is provided, the category with
         * that id is not taken into account in the domain computation.
         * Ovverride the function to replace '=' with 'child_of' operator domain
         * if field type is many2many.
         * @override
         * @private
         * @param {string} [excludedCategoryId]
         * @returns {Array[]}
         */
        _getCategoryDomain (excludedCategoryId) {
            const domain = [];
            for (const category of this.categories) {
                if (
                    category.id === excludedCategoryId ||
                    !category.activeValueId
                ) {
                    continue;
                }
                const field = this.config.fields[category.fieldName];
                const operator =
                    (field.type === "many2one" || field.type === "many2many") && category.parentField ? "child_of" : "=";
                domain.push([
                    category.fieldName,
                    operator,
                    category.activeValueId,
                ]);
            }
            return domain;
        }

    }

    ActionModel.registry.add("SearchPanel", SearchPanelModelExtensionM2m, 30);

    return SearchPanelModelExtensionM2m;
});