/** ********************************************************************************
    Copyright 2020-2022 Flosslab S.r.l.
    Copyright 2017-2019 MuK IT GmbH
    License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
 **********************************************************************************/

odoo.define('fl_web_preview.utils', function (require) {
"use strict";

var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;

var isUrl = function(string) {
	var protocol = string.match(/^(?:\w+:)?\/\/(\S+)$/);
	if (protocol && protocol[1]) {
		var localHost = (/^localhost[\:?\d]*(?:[^\:?\d]\S*)?$/).test(protocol[1]);
		var nonLocalHost = (/^localhost[\:?\d]*(?:[^\:?\d]\S*)?$/).test(protocol[1]);
		return !!(localHost || nonLocalHost);
	}
	return false;
}

var parseText2Html= function(text) {
    return text
        .replace(/((?:https?|ftp):\/\/[\S]+)/g,'<a href="$1">$1</a> ')
        .replace(/[\n\r]/g,'<br/>');
}

var closedRange = function(start, end) { 
	return _.range(start, end + 1);
}

var partitionPageList = function(pages, page, size) {
	if (!size || size < 5) {
		throw "The size must be at least 5 to partition the list.";
	}
	var sideSize = size < 9 ? 1 : 2;
	var leftSize = (size - sideSize * 2 - 3) >> 1;
	var rightSize = (size - sideSize * 2 - 2) >> 1;
	if (pages <= size) {
		return closedRange(1, pages);
	}
    if (page <= size - sideSize - 1 - rightSize) {
    	return closedRange(1, size - sideSize - 1)
    		.concat([false])
    		.concat(closedRange(pages - sideSize + 1, pages));
    }
    if (page >= pages - sideSize - 1 - rightSize) {
    	return closedRange(1, sideSize)
    		.concat([false])
    		.concat(closedRange(pages - sideSize - 1 - rightSize - leftSize, pages));
    }
    return closedRange(1, sideSize)
	    .concat([false])
	    .concat(closedRange(page - leftSize, page + rightSize))
	    .concat([false])
	    .concat(closedRange(pages - sideSize + 1, pages));
}

return {
	isUrl: isUrl,
	closedRange: closedRange,
	parseText2Html: parseText2Html,
	partitionPageList: partitionPageList,
};

});