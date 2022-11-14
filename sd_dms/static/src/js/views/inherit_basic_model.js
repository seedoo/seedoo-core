odoo.define('sd_dms.BasicModel', function (require) {
    "use strict";

    var BasicModel = require('web.BasicModel');

    BasicModel.include({
        /**
         * When one needs to create a record from scratch, a not so simple process
         * needs to be done:
         * - call the /default_get route to get default values
         * - fetch all relational data
         * - apply all onchanges if necessary
         * - fetch all relational data
         *
         * This method tries to optimize the process as much as possible.  Also,
         * it is quite horrible and should be refactored at some point.
         *
         * @private
         * @param {any} params
         * @param {string} modelName model name
         * @param {boolean} [params.allowWarning=false] if true, the default record
         *   operation can complete, even if a warning is raised
         * @param {Object} params.context the context for the new record
         * @param {Object} params.fieldsInfo contains the fieldInfo of each view,
         *   for each field
         * @param {Object} params.fields contains the description of each field
         * @param {Object} params.context the context for the new record
         * @param {string} params.viewType the key in fieldsInfo of the fields to load
         * @returns {Promise<string>} resolves to the id for the created resource
         */
        async _makeDefaultRecord(modelName, params) {
            this._makeDefaultRecordField(params, 'folder_id');
            return await this._super.apply(this, arguments);
        },

        /**
         * Set in context the default value to field name using the value selected in search panel.
         *
         * @param {Object} params
         * @param {string} fieldName field name
         * @private
         */
        _makeDefaultRecordField(params, fieldName) {
            const fieldNameDefault = 'default_' + fieldName;
            const fieldNameDefaultSearchPanel = 'search_panel_default_' + fieldName;
            const case1 = 'context' in params && !(fieldNameDefault in params.context);
            const case2 = 'context' in params && (fieldNameDefault in params.context) &&
                (fieldNameDefaultSearchPanel in params.context) &&
                (params.context[fieldNameDefault] == params.context[fieldNameDefaultSearchPanel]);
            if (case1 || case2) {
                const activeValueId = this._getSearchPanelActiveValueId(fieldName);
                params.context[fieldNameDefaultSearchPanel] = activeValueId;
                params.context[fieldNameDefault] = activeValueId;
            }
        },

        _getSearchPanelActiveValueId(fieldName) {
            const sections = this._getSections();
            if (sections == null) {
                return null;
            }
            for (const section of sections) {
               const category = section[1];
               if ('type' in category && category.type=='category' &&
                   'fieldName' in category && category.fieldName==fieldName &&
                   'activeValueId' in category
               ) {
                   return category.activeValueId;
               }
            }
            return null;
        },

        _getSections() {
            const searchModel = this._getSearchModel();
            if (searchModel == null) {
                return null;
            }
            for (const extension of searchModel.extensions) {
                for (const extensionComponent of extension) {
                    if (('state' in extensionComponent) && ('sections' in extensionComponent.state)) {
                        return extensionComponent.state.sections;
                    }
                }
            }
            if ('externalState' in searchModel && 'SearchPanelModelExtensionLoadOnlyChildren' in searchModel.externalState) {
                return searchModel.externalState.SearchPanelModelExtensionLoadOnlyChildren.sections;
            }
            return null;
        },

        _getSearchModel() {
            let searchModel = null;
            if ('__parentedParent' in this) {
                if ('__parentedChildren' in this.__parentedParent) {
                    searchModel = this._getParentedChildrenSearchModel(this.__parentedParent.__parentedChildren);
                }
                if ((searchModel == null) && ('__parentedParent' in this.__parentedParent) && ('__parentedChildren' in this.__parentedParent.__parentedParent)) {
                    searchModel = this._getParentedChildrenSearchModel(this.__parentedParent.__parentedParent.__parentedChildren);
                }
            }
            return searchModel;
        },

        _getParentedChildrenSearchModel(parentedChildrenList) {
            for (const children of parentedChildrenList) {
                if (!('searchModel' in children) || !('extensions' in children.searchModel)) {
                    continue;
                }
                return children.searchModel;
            }
            return null;
        },


        /**
         * Do a /search_read to get data for a list resource.  This does a
         * /search_read because the data may not be static (for ex, a list view).
         *
         * @param {Object} list
         * @returns {Promise}
         */
        _searchReadUngroupedList: function (list) {
            var self = this;
            var fieldNames = list.getFieldNames();
            var prom;
            if (list.__data) {
                // the data have already been fetched (alongside the groups by the
                // call to 'web_read_group'), so we can bypass the search_read
                // But the web_read_group returns the rawGroupBy field's value, which may not be present
                // in the view. So we filter it out.
                const fieldNameSet = new Set(fieldNames);
                fieldNameSet.add("id"); // don't filter out the id
                list.__data.records.forEach(record =>
                    Object.keys(record)
                        .filter(fieldName => !fieldNameSet.has(fieldName))
                        .forEach(fieldName => delete record[fieldName]));
                prom = Promise.resolve(list.__data);
            } else {
                // Permette il caricamento di un domain solo al caricamento della vista
                var domain = list.domain
                var promDefaultFolder;
                var hasProm = false;
                if (list.model === "sd.dms.document" && "default_search_panel_custom_folder" in this.loadParams.context) {
                    hasProm = true
                    let uid = this.loadParams.context.uid
                    let defaultFolder;
                    promDefaultFolder = self._rpc({
                        model: "res.users",
                        method: "get_default_folder_for_documents",
                        args: [[uid]],
                    })
                    delete this.loadParams.context["default_search_panel_custom_folder"]
                }
                if (hasProm) {
                    return promDefaultFolder.then(function (result) {
                        domain.push(["folder_id", "=", result["folder_id"]])
                        prom = self._rpc({
                            route: '/web/dataset/search_read',
                            model: list.model,
                            fields: fieldNames,
                            context: _.extend({}, list.getContext(), {bin_size: true}),
                            domain: list.domain || [],
                            limit: list.limit,
                            offset: list.loadMoreOffset + list.offset,
                            orderBy: list.orderedBy,
                        })
                        return prom.then(function (result) {
                            return self._resolveProm(self, list, result, fieldNames)
                        });

                    });
                } else {
                    prom = self._rpc({
                        route: '/web/dataset/search_read',
                        model: list.model,
                        fields: fieldNames,
                        context: _.extend({}, list.getContext(), {bin_size: true}),
                        domain: list.domain || [],
                        limit: list.limit,
                        offset: list.loadMoreOffset + list.offset,
                        orderBy: list.orderedBy,
                    })
                }
            }

            return prom.then(function (result) {
                return self._resolveProm(self, list, result, fieldNames)
            });
        },

        _resolveProm: function (self, list, result, fieldNames) {
                delete list.__data;
                list.count = result.length;
                var ids = _.pluck(result.records, 'id');
                var data = _.map(result.records, function (record) {
                    var dataPoint = self._makeDataPoint({
                        context: list.context,
                        data: record,
                        fields: list.fields,
                        fieldsInfo: list.fieldsInfo,
                        modelName: list.model,
                        parentID: list.id,
                        viewType: list.viewType,
                    });

                    // add many2one records
                    self._parseServerData(fieldNames, dataPoint, dataPoint.data);
                    return dataPoint.id;
                });
                if (list.loadMoreOffset) {
                    list.data = list.data.concat(data);
                    list.res_ids = list.res_ids.concat(ids);
                } else {
                    list.data = data;
                    list.res_ids = ids;
                }
                self._updateParentResIDs(list);
                return list;
        }

    });

});