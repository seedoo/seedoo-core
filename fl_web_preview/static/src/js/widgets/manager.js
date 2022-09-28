/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.PreviewManager', function (require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var session = require('web.session');
var framework = require('web.framework');

var Widget = require('web.Widget');

var utils = require('fl_web_preview.utils');
var registry = require('fl_web_preview.registry');

var QWeb = core.qweb;
var _t = core._t;

var PreviewManager = Widget.extend({
    template: "fl_web_preview.PreviewManager",
	events: _.extend({}, Widget.prototype.events, {
		'click .fl_web_preview_previous a': '_onPreviousClick',
		'click .fl_web_preview_next a': '_onNextClick',
		'click .fl_web_preview_page a': '_onPageClick',
		'click .fl_web_preview_print': '_onPrintClick',
	}),
    jsLibs: [
        '/fl_web_preview/static/lib/printThis/printThis.js',
    ],
	files: [],
	init: function (parent, files, index) {
		this._super.apply(this, arguments);
		this.files = files;
		this.index = index;
		this.activeFile = files[index];
		this.pagerSize = 9;
	},
	willStart: function() { 
		return $.when(
			this._super.apply(this, arguments),
			ajax.loadLibs(this)
		);
    },
    start: function () {
        var res = this._super.apply(this, arguments);
    	if (!this.activeFile.filename) {
    		return;
		}
        this.$actions = this.$('.fl_web_preview_actions');
        this.$wrapper = this.$('.fl_web_preview_wrapper');
        this.$pager = this.$('.fl_web_preview_pager');
        this._render();
        return res; 
    }, 
    _render: function () {
        this._renderPreviewWithLoading();
        this._renderIndexPager();
        this._updateActions();
    },
    _renderPreviewWithLoading: function () {
    	var $loader = this._renderLoader();
    	this._destroyPreview();
    	this._renderPreview($loader);
    },
    _renderLoader: function () {
    	var $loader = $(QWeb.render('fl_web_preview.PreviewLoader', {
			loading_text: _t("Loading ..."),
			loading_text_00: _t("Loading"),
			loading_text_25: _t("Loading ."),
			loading_text_50: _t("Loading .."),
			loading_text_75: _t("Loading ..."),
		}));
    	this.$wrapper.html($loader);
    	return $loader;
    },
    _renderPreview: function (element) {
    	var PreviewWidget = undefined;
    	var mimetype = this.activeFile.mimetype;
    	var filename = this.activeFile.filename;
    	if (mimetype && registry.contains(mimetype)) {
    		PreviewWidget = registry.get(mimetype);
    	}
    	if (!PreviewWidget && filename) {
    		var extension = filename.toLowerCase().split('.').pop();
    		if (extension && registry.contains(extension)) {
        		PreviewWidget = registry.get(extension);
        	}
    	}
    	if (!PreviewWidget) {
    		PreviewWidget = registry.defaultPreview();
    	}
    	var content = new PreviewWidget(this, 
    		this.activeFile.url, mimetype, filename
    	);
    	content.replace(element);
    	this.activePreview = content;
    },
    _renderIndexPager: function () {
    	this.$pager.find('.pagination').empty();
    	if (this.files.length <= 1) {
    		this.$pager.hide();
    	} else {
    		var $previous = $("<li>", {
				'class': "page-item fl_web_preview_previous",
				'title': _t("Previous"),
			}).append($("<a>", {
				'class': "page-link",
				'href': "#",
				'html': '<i class="fa fa-angle-double-left" />',
			}));
        	var $next = $("<li>", {
				'class': "page-item fl_web_preview_next",
				'title': _t("Next"),
			}).append($("<a>", {
				'class': "page-link",
				'href': "#",
				'html': '<i class="fa fa-angle-double-right" />',
			}));
    		this.$pager.find('.pagination').append($previous);
    		this.$pager.find('.pagination').append($next);
    		var pageList = utils.partitionPageList(
				this.files.length,
				this.index + 1,
				this.pagerSize
    		);
    		_.each(pageList, function(page) {
    			var index = page && page - 1;
    			var $item = $("<li>", {
					'class': "page-item",
				});
    			if (!page) {
    				$item.addClass("disabled");
    			} else if (index === this.index) {
    				$item.addClass("active");
    			} else {
    				$item.addClass("fl_web_preview_page");
    			}
    			$item.append($("<a>", {
					'class': "page-link",
					'data-index': index,
					'text': page || '...',
					'href': "javascript:void(0)",
				}));
				$item.insertBefore($next);
    		}, this);
    		if (this.index === 0) {
    			$previous.addClass("disabled");
    			$next.removeClass("disabled");
        	} else if (this.index === this.files.length - 1) {
    			$previous.removeClass("disabled");
    			$next.addClass("disabled");
        	} else {
    			$previous.removeClass("disabled");
    			$next.removeClass("disabled");
        	}
    		this.$pager.show();
    	}
    }, 
    _updateActions: function () {
    	this.$actions.empty();
    	if (this.activePreview) {
    		if (this.activePreview.downloadable) {
        		this.$actions.append($("<a>", {
        			'class': "fl_web_preview_download",
        			'html': '<i class="fa fa-download" />',
    				'title': _t("Download"),
        			'href': this.activeFile.url,
        		}));
    		}
    		if (this.activePreview.printable) {
        		this.$actions.append($("<a>", {
        			'class': "fl_web_preview_print",
        			'html': '<i class="fa fa-print" />',
    				'title': _t("Print"),
        			'href': '#',
        		}));
    		}
    		_.each(this.activePreview.contentActions(), function(action) {
    			this.$actions.append(action);
    		}, this);
    	}
    },
    _destroyPreview: function () {
		if (this.activePreview) {
			this.activePreview.destroy();
		}
		this.activePreview = undefined;
    },
    _onPreviousClick: function(event) {
    	if (this.index > 0) {
    		this.index = this.index - 1;
    		this.activeFile = this.files[this.index];
            this._render();
    	}
        event.stopPropagation();
        event.preventDefault();
    },
    _onNextClick: function (event) {
    	if (this.index < this.files.length - 1) {
    		this.index = this.index + 1;
    		this.activeFile = this.files[this.index];
            this._render();
    	}
        event.stopPropagation();
        event.preventDefault();
    },
    _onPageClick: function(event) {
    	var $target = $(event.currentTarget);
    	var index = $target.data('index');
    	if (index >= 0 && index < this.files.length) {
    		this.index = index;
    		this.activeFile = this.files[this.index];
            this._render();
    	}
        event.stopPropagation();
        event.preventDefault();
    },
    _onPrintClick: function(event) {
    	var preview = this.activePreview;
    	var delay = preview.printDelay;
    	framework.blockUI();
    	setTimeout(function() {
    		framework.unblockUI();
    	}, delay|| 950);
    	this.$wrapper.printThis({
			importCSS: true,
			importStyle: true,
			printDelay: delay|| 950,
    	});
        event.stopPropagation();
        event.preventDefault();
    },
});

return PreviewManager;

});