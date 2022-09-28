odoo.define("fl_disable_childof_search_panel/static/src/js/views/search_panel_model_extension.js", function (require) {
    "use strict";

    const ActionModel = require("web/static/src/js/views/action_model.js");
    const SearchPanelModelExtensionM2m = require("fl_m2m_search_panel/static/src/js/views/search_panel_model_extension.js");
    var pyUtils = require('web.py_utils');

    /**
     * @property {{ sections: Map<number, Section> }} state
     * @extends ActionModel.Extension
     */
    class SearchPanelModelExtensionDisableChildof extends SearchPanelModelExtensionM2m {

        /**
         * Adds a section in this.state.sections for each visible field found
         * in the search panel arch.
         * Extend the function to set disableChildofDomainOnexpand value get
         * by disable_childof_domain_onexpand option.
         * @private
         */
        _createSectionsFromArch() {
            super._createSectionsFromArch();
            this.config.archNodes.forEach(({ attrs, tag }, index) => {
                if (tag !== "field" || attrs.invisible === "1") {
                    return;
                }
                const options = attrs.options ? pyUtils.py_eval(attrs.options) : {};
                if (!options.disable_childof_domain_onexpand) {
                    return;
                }
                for (const section of this.state.sections.values()) {
                    if (section.fieldName !== attrs.name || section.type !== 'category') {
                        continue;
                    }
                    section.disableChildofDomainOnexpand = options.disable_childof_domain_onexpand;
                    break;
                }
            });
        }

        /**
         * Sets the active value id of a given category.
         * Ovverride the function to set if category is expanded
         *
         * @override
         * @param {number} sectionId
         * @param {number} valueId
         */
        toggleCategoryValue(sectionId, valueId, expanded) {
            const category = this.state.sections.get(sectionId);
            category.activeValueId = valueId;
            category.expanded = expanded;
        }

        /**
         * Computes and returns the domain based on the current active
         * categories. If "excludedCategoryId" is provided, the category with
         * that id is not taken into account in the domain computation.
         * Ovverride the function to replace 'child_of' with '=' operator domain
         * if disable_childof_domain_onexpand option is active and the item
         * of category tree is expanded.
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
                let disableChildof = false;
                for (const section of this.state.sections.values()) {
                    if (section.fieldName !== category.fieldName || section.type !== 'category' || !section.disableChildofDomainOnexpand) {
                        continue;
                    }
                    disableChildof = true;
                    break;
                }
                const fieldTypeCondition = (field.type === 'many2one' || field.type === 'many2many');
                const childOfCondition = !disableChildof || (disableChildof && !category.expanded);
                const operator = (fieldTypeCondition && category.parentField && childOfCondition) ? 'child_of' : '=';
                domain.push([
                    category.fieldName,
                    operator,
                    category.activeValueId,
                ]);
            }
            return domain;
        }

    }

    ActionModel.registry.add("SearchPanel", SearchPanelModelExtensionDisableChildof, 30);

    return SearchPanelModelExtensionDisableChildof;
});