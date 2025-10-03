// Copyright (c) 2025, Bijak Technology and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Reorder Level Monitoring"] = {
	"filters": [
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Popover for Actual Stock
		if (column.id == "actual_stock_display" && data.actual_stock_popover) {
			let popover_data = JSON.parse(data.actual_stock_popover);
			if (popover_data.length > 0) {
				let popover_html = "<ul class='list-unstyled'>";
				popover_data.forEach(d => {
					popover_html += `<li>${d.warehouse}: <b>${d.actual_qty}</b></li>`;
				});
				popover_html += "</ul>";
				value = `<span class="indicator-pill blue" data-popover-content='${popover_html}'>${value}</span>`;
			}
		}

		// Popover for Material Requests
		if (column.id == "mr_display" && data.mr_popover) {
			let popover_data = JSON.parse(data.mr_popover);
			if (popover_data.length > 0) {
				let popover_html = "<ul class='list-unstyled'>";
				popover_data.forEach(d => {
					popover_html += `<li>${d.parent}: <b>${d.qty}</b></li>`;
				});
				popover_html += "</ul>";
				value = `<span class="indicator-pill orange" data-popover-content='${popover_html}'>${value}</span>`;
			}
		}

		// Popover for Purchase Orders
		if (column.id == "po_display" && data.po_popover) {
			let popover_data = JSON.parse(data.po_popover);
			if (popover_data.length > 0) {
				let popover_html = "<ul class='list-unstyled'>";
				popover_data.forEach(d => {
					popover_html += `<li><b>${d.po_id}</b><br>Supplier: ${d.supplier}<br>ETA: ${d.eta} (${d.eta_lead_time} hari) | Qty: ${d.qty}</li>`;
				});
				popover_html += "</ul>";
				value = `<span class="indicator-pill green" data-popover-content='${popover_html}'>${value}</span>`;
			}
		}

		return value;
	},
	"onload": function(report) {
		report.page.body.on("mouseenter", ".indicator-pill", function() {
			const content = $(this).data("popover-content");
			$(this).popover({
				content: content,
				trigger: "manual",
				html: true,
				placement: "bottom",
				animation: false
			}).popover("show");
		});

		report.page.body.on("mouseleave", ".indicator-pill", function() {
			$(this).popover("hide");
		});
	}
};
