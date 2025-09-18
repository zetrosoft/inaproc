import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Item Tree View"
    context.item_groups = frappe.get_list("Item Group", fields=["name", "parent_item_group", "is_group"])
    context.items = frappe.get_list("Item", filters={"disabled": 0}, fields=["name", "item_name", "item_group"])
