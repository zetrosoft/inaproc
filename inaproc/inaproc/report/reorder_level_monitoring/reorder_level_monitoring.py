# Copyright (c) 2025, Bijak Technology and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.permissions import get_valid_perms


def execute(filters=None):
    # 1. Define Columns
    columns = get_columns()

    # 2. Get Data
    data = get_data(filters)

    return columns, data

def get_columns():
    """Defines the columns for the report."""
    return [
        {"label": "Nama Item", "fieldname": "item_name", "fieldtype": "Link", "options": "Item", "width": 250},
        {"label": "UOM", "fieldname": "stock_uom", "fieldtype": "Data", "width": 100},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": "Stok Aktual", "fieldname": "actual_stock_display", "fieldtype": "Data", "width": 120},
        {"label": "Stok Aktual (Popover)", "fieldname": "actual_stock_popover", "fieldtype": "Data", "hidden": 1},
        {"label": "MR", "fieldname": "mr_display", "fieldtype": "Data", "width": 120},
        {"label": "MR (Popover)", "fieldname": "mr_popover", "fieldtype": "Data", "hidden": 1},
        {"label": "PO", "fieldname": "po_display", "fieldtype": "Data", "width": 120},
        {"label": "PO (Popover)", "fieldname": "po_popover", "fieldtype": "Data", "hidden": 1},
        {"label": "Lead Time", "fieldname": "lead_time", "fieldtype": "Int", "width": 100},
        {"label": "Min Qty", "fieldname": "min_qty", "fieldtype": "Float", "width": 100},
        {"label": "Max Qty", "fieldname": "max_qty", "fieldtype": "Float", "width": 100},
        {"label": "Reorder Level", "fieldname": "reorder_level", "fieldtype": "Float", "width": 120},
    ]

def get_data(filters):
    """Fetches and processes the data for the report."""
    conditions = ""
    today = frappe.utils.getdate()

    if filters.get("item_group"):
        conditions += f" AND item_group = '{filters.get('item_group')}'"

    permitted_item_groups = frappe.get_all("Item Group", filters={"is_group": 0})
    permitted_groups_list = [d.name for d in permitted_item_groups]

    if not permitted_groups_list:
        return []

    conditions += " AND item_group IN %(permitted_groups)s"

    items = frappe.get_list("Item",
        fields=["name", "item_name", "stock_uom", "projected_qty", "custom_calculated_min_qty", "custom_calculated_max_qty"],
        filters={"disabled": 0, "custom_inventory_section": 1},
        sql_conditions=conditions,
        sql_vars={"permitted_groups": tuple(permitted_groups_list)}
    )

    report_data = []
    for item in items:
        min_qty = item.get("custom_calculated_min_qty", 0)
        projected_qty = item.get("projected_qty", 0)

        status = "OK"
        if projected_qty < min_qty:
            status = "<b style='color:red;'>Perlu Pesan Ulang</b>"

        lead_times = frappe.get_all("Item Supplier", filters={"parent": item.name}, fields=["lead_time_days"])
        longest_lead_time = max([lt.get("lead_time_days", 0) for lt in lead_times]) if lead_times else 0

        stock_breakdown = frappe.get_all("Bin", filters={"item_code": item.name, "actual_qty": (">", 0)}, fields=["warehouse", "actual_qty"])
        total_actual_stock = sum(s.get("actual_qty", 0) for s in stock_breakdown)

        # Get Open Material Requests
        open_mrs = frappe.get_all("Material Request Item",
            filters={"item_code": item.name, "docstatus": 1, "status": ("!=", "Stopped"), "ordered_qty": ("<", "qty")},
            fields=["parent", "qty", "schedule_date"]
        )
        total_mr_qty = sum(mr.get("qty", 0) for mr in open_mrs)

        # Get Open Purchase Orders
        open_pos_raw = frappe.get_all("Purchase Order Item",
            filters={"item_code": item.name, "docstatus": 1, "received_qty": ("<", "qty")},
            parent_doctype="Purchase Order",
            fields=["parent", "supplier", "qty", "schedule_date"]
        )

        open_pos_details = []
        for po in open_pos_raw:
            eta_lead_time = (frappe.utils.getdate(po.schedule_date) - today).days if po.schedule_date else 'N/A'
            open_pos_details.append({
                "po_id": po.parent,
                "supplier": po.supplier,
                "qty": po.qty,
                "eta": po.schedule_date,
                "eta_lead_time": eta_lead_time
            })
        total_po_qty = sum(po.get("qty", 0) for po in open_pos_details)

        report_data.append({
            "item_name": item.name,
            "stock_uom": item.stock_uom,
            "status": status,
            "actual_stock_display": total_actual_stock,
            "actual_stock_popover": json.dumps(stock_breakdown or []),
            "mr_display": total_mr_qty,
            "mr_popover": json.dumps(open_mrs or []),
            "po_display": total_po_qty,
            "po_popover": json.dumps(open_pos_details or [], default=str),
            "lead_time": longest_lead_time,
            "min_qty": min_qty,
            "max_qty": item.get("custom_calculated_max_qty", 0),
            "reorder_level": min_qty,
        })

    return report_data
