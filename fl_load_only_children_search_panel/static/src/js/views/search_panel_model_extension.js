odoo.define("fl_load_only_children_search_panel/static/src/js/views/search_panel_model_extension.js", function (require) {
    "use strict";

    const ActionModel = require("web/static/src/js/views/action_model.js");
    const SearchPanelModelExtensionDisableChildof = require("fl_disable_childof_search_panel/static/src/js/views/search_panel_model_extension.js");
    var pyUtils = require('web.py_utils');

    /**
     * @property {{ sections: Map<number, Section> }} state
     * @extends ActionModel.Extension
     */
    class SearchPanelModelExtensionLoadOnlyChildren extends SearchPanelModelExtensionDisableChildof {

        /**
         * Adds a section in this.state.sections for each visible field found in the search panel arch.
         * Extend the function to set loadOnlyChildrenOnexpand value get by load_only_children_onexpand option.
         * @private
         */
        _createSectionsFromArch() {
            super._createSectionsFromArch();
            this.config.archNodes.forEach(({ attrs, tag }, index) => {
                if (tag !== "field" || attrs.invisible === "1") {
                    return;
                }
                const options = attrs.options ? pyUtils.py_eval(attrs.options) : {};
                if (!options.load_only_children_onexpand) {
                    return;
                }
                for (const section of this.state.sections.values()) {
                    if (section.fieldName !== attrs.name || section.type !== 'category') {
                        continue;
                    }
                    section.loadOnlyChildrenOnexpand = options.load_only_children_onexpand;
                    section.loadOnlyChildrenOnexpandDisplayName = options.load_only_children_onexpand_display_name;
                    break;
                }
            });
        }

        /**
         * @override
         */
        async callLoad(params) {
            const searchDomain = this._getExternalDomain();
            params.searchDomainChanged = (
                JSON.stringify(this.searchDomain) !== JSON.stringify(searchDomain)
            );
            if (!this.shouldLoad && !this.initialStateImport) {
                /******************************************************************************************************/
                const isFetchable = (section) => section.enableCounters ||
                    (params.searchDomainChanged && !section.expand) ||
                    (section.loadOnlyChildrenOnexpand && section.expanded);
                /******************************************************************************************************/
                this.categoriesToLoad = this.categories.filter(isFetchable);
                this.filtersToLoad = this.filters.filter(isFetchable);
                this.shouldLoad = params.searchDomainChanged ||
                    Boolean(this.categoriesToLoad.length + this.filtersToLoad.length);
            }
            this.searchDomain = searchDomain;
            this.initialStateImport = false;
            await super.callLoad(params);
        }

        /**
         * Fetches values for each category at startup. At reload a category is only fetched if needed.
         * @private
         * @param {Category[]} categories
         * @returns {Promise} resolved when all categories have been fetched
         */
        async _fetchCategories(categories) {
            const filterDomain = this._getFilterDomain();
            for (let category of categories) {
                await this._fetchCategory(category, filterDomain);
            }
        }

        async _fetchCategory(category, filterDomain) {
            const result = await this.env.services.rpc({
                method: "search_panel_select_range",
                model: this.config.modelName,
                args: [category.fieldName],
                kwargs: {
                    category_domain: this._getCategoryDomain(category.id),
                    enable_counters: category.enableCounters,
                    expand: category.expand,
                    filter_domain: filterDomain,
                    hierarchize: category.hierarchize,
                    limit: category.limit,
                    search_domain: this.searchDomain,
                    /**********************************************************************************************/
                    load_only_children_onexpand: category.loadOnlyChildrenOnexpand,
                    load_only_children_onexpand_display_name: category.loadOnlyChildrenOnexpandDisplayName,
                    active_value_id: category.activeValueId,
                    /**********************************************************************************************/
                },
            });
            /******************************************************************************************************/
            // this._createCategoryTree(category.id, result);
            if (category.loadOnlyChildrenOnexpand) {
                this._createCategoryTreeLevel(category.id, category.activeValueId, result);
            } else {
                this._createCategoryTree(category.id, result);
            }
            /******************************************************************************************************/
        }

        /**
         * @private
         * @param {string} sectionId
         * @param {integer} activeId
         * @param {Object} result
         */
        _createCategoryTreeLevel(sectionId, activeId, result) {
            const category = this.state.sections.get(sectionId);
            if (category.values.get(activeId)) {
                category.values.get(activeId).childrenIds = [];
            }

            let { error_msg, parent_field: parentField, values, } = result;
            if (error_msg) {
                category.errorMsg = error_msg;
                values = [];
            }
            if (category.hierarchize) {
                category.parentField = parentField;
            }
            for (const value of values) {
                let childrenIds = [];
                if (category.values.get(value.id)) {
                    childrenIds = category.values.get(value.id).childrenIds;
                }
                category.values.set(
                    value.id,
                    Object.assign({}, value, {
                        childrenIds: childrenIds,
                        parentId: value[parentField] || false,
                    })
                );
            }
            for (const value of values) {
                const { parentId } = category.values.get(value.id);
                if (parentId && category.values.has(parentId)) {
                    category.values.get(parentId).childrenIds.push(value.id);
                }
            }
            // collect rootIds
            if (!('rootIds' in category)) {
                category.rootIds = [false];
                for (const value of values) {
                    const { parentId } = category.values.get(value.id);
                    if (!parentId) {
                        category.rootIds.push(value.id);
                    }
                }
                // Set active value
                category.activeValueId = false;
            }
        }

    }

    ActionModel.registry.add("SearchPanel", SearchPanelModelExtensionLoadOnlyChildren, 30);

    return SearchPanelModelExtensionLoadOnlyChildren;
});