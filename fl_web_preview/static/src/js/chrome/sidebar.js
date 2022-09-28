/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.Sidebar', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var pyUtils = require('web.py_utils');

var Context = require('web.Context');
var Sidebar = require('web.Sidebar');

var PreviewManager = require('fl_web_preview.PreviewManager');
var PreviewDialog = require('fl_web_preview.PreviewDialog');

var QWeb = core.qweb;
var _t = core._t;

Sidebar.include({
	events: _.extend({}, Sidebar.prototype.events, {
		'click .fl_web_preview_report': '_onReportPreview',
	}),
	_onReportPreview: function(event) {
        this.$('[data-toggle="tooltip"]').tooltip({delay: 0});
        var index = $(event.currentTarget).data('index');
        var item = this.items['print'][index];
        if (item.action) {
        	this.trigger_up('sidebar_data_asked', {
        		callback: function (env) {
        			var contextValues = {
                        active_id: env.activeIds[0],
                        active_ids: env.activeIds,
                        active_model: env.model,
                        active_domain: env.domain || [],
                    };
                    var context = pyUtils.eval('context', 
                    	new Context(env.context, contextValues)
                    );
                    this._rpc({
                        route: '/web/action/load',
                        params: {
                            action_id: item.action.id,
                            context: context,
                        },
                    }).done(function (result) {
                    	result.context = new Context(
                    		result.context || {}, contextValues
                    	).set_eval_context(context);
                        result.flags.new_window = true;
                    	result.flags = result.flags || {};
                    	if (result.report_type === 'qweb-pdf') {
                    		this.call('report', 'checkWkhtmltopdf').then(function (state) {
    			                if (state === 'upgrade' || state === 'ok') {
    			                	result.context = pyUtils.eval(
	                        			'context', result.context
	                        		);
    			                	this._callReportPreview(
    	                        		result, item.label,
    	                        		'pdf', 'application/pdf'
    	                        	);
    			                } else {
    	                        	this._callReportAction(result);
    			                }
                        	 }.bind(this));
                    	} else if (result.report_type === 'qweb-text') {
                    		result.context = pyUtils.eval(
                    			'context', result.context
                    		);
                    		this._callReportPreview(
                        		result, item.label,
                        		'text', 'text/plain'
                        	);
                        } else {
                        	this._callReportAction(result);
                        }
                    }.bind(this));
        		}.bind(this),
        	});
        }
        event.stopPropagation();
		event.preventDefault();
	},
	_callReportAction: function(action) {
		this.do_action(action, {
			on_close: function () {
				this.trigger_up('reload');
			}.bind(this),
		});
	},
	_callReportPreview: function(action, label, type, mimetype) {
        var reportUrls = {
            pdf: '/report/pdf/' + action.report_name,
            text: '/report/text/' + action.report_name,
        };
        if (_.isUndefined(action.data) || _.isNull(action.data) ||
            (_.isObject(action.data) && _.isEmpty(action.data))) {
            if (action.context.active_ids) {
                var activeIDsPath = '/' + action.context.active_ids.join(',');
                reportUrls = _.mapObject(reportUrls, function (value) {
                	return value += activeIDsPath;
                });
            }
        } else {
            var serializedOptionsPath = '?options=' + encodeURIComponent(JSON.stringify(action.data));
            serializedOptionsPath += '&context=' + encodeURIComponent(JSON.stringify(action.context));
            reportUrls = _.mapObject(reportUrls, function (value) {
            	return value += serializedOptionsPath;
            });
        }
        var url = session.url('/report/download', {
        	data: JSON.stringify([
        		reportUrls[type],
        		action.report_type
        	]),
        	token: core.csrf_token,
        });
        var preview = new PreviewDialog(
    		this, [{
    			url: url,
    			filename: label,
    			mimetype: mimetype,
    		}], 0
        );
        preview.appendTo($('body'));
	},
});

});
