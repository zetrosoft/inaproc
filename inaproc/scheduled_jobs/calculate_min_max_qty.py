import frappe
from frappe.utils import add_months, flt, getdate


def get_bom_material_for_production(bom_item_code, qty_to_produce=1.0, raw_materials=None):
    """
    Recursively explodes a BOM to get the flat list of raw materials required.
    """
    if raw_materials is None:
        raw_materials = {}

    # Find the active, default BOM for the item. If not, any active one.
    bom_name = frappe.db.get_value("BOM", {"item": bom_item_code, "is_active": 1, "is_default": 1})
    if not bom_name:
        bom_name = frappe.db.get_value("BOM", {"item": bom_item_code, "is_active": 1})

    if not bom_name:
        # If there's no BOM, it's treated as a raw material itself.
        is_stock_item = frappe.db.get_value("Item", bom_item_code, "is_stock_item")
        if is_stock_item:
            raw_materials[bom_item_code] = raw_materials.get(bom_item_code, 0) + flt(qty_to_produce)
        return raw_materials

    # Get items from the BOM
    bom_items = frappe.get_all("BOM Item",
        filters={"parent": bom_name},
        fields=["item_code", "stock_qty", "bom_no"] # bom_no indicates if the item is a sub-assembly
    )

    for item in bom_items:
        required_qty = flt(item.stock_qty) * flt(qty_to_produce)

        # If the component has its own BOM (it's a sub-assembly), recurse.
        if item.bom_no:
            get_bom_material_for_production(item.item_code, required_qty, raw_materials)
        else:
            # It's a raw material, add it to the dictionary.
            raw_materials[item.item_code] = raw_materials.get(item.item_code, 0) + required_qty

    return raw_materials

def calculate_min_max_quantities():
    """
    Calculates and updates the minimum and maximum inventory quantities for items
    based on historical sales data and BOM explosion.
    Sets default min/max for items without sales history.
    """
    today = getdate()
    three_months_ago = add_months(today, -3)

    item_demands = {}

    # 1. Calculate sales demand for finished goods and derived demand for raw materials.
    #    This part populates item_demands only for items that had sales.
    finished_goods_with_bom = frappe.get_list("Item",
        filters={"is_stock_item": 1, "default_bom": ["!=", ""]},
        fields=["name", "item_code"]
    )

    for fg_item in finished_goods_with_bom:
        sales_qty = frappe.db.sql("""
            SELECT SUM(t1.qty)
            FROM `tabSales Invoice Item` t1
            JOIN `tabSales Invoice` t2 ON t1.parent = t2.name
            WHERE t1.item_code = %s
              AND t2.docstatus = 1
              AND t2.posting_date >= %s
        """, (fg_item.item_code, three_months_ago))[0][0] or 0

        total_sales_qty = flt(sales_qty)

        if total_sales_qty > 0:
            item_demands[fg_item.item_code] = item_demands.get(fg_item.item_code, 0) + total_sales_qty
            required_materials = get_bom_material_for_production(fg_item.item_code, total_sales_qty)
            for material, qty in required_materials.items():
                item_demands[material] = item_demands.get(material, 0) + qty

    # 2. Get ALL stock items to ensure all are processed, even those without sales history.
    all_stock_items = frappe.get_list("Item",
        filters={"is_stock_item": 1},
        fields=["item_code", "custom_safety_stock", "custom_lead_time"]
    )

    processed_item_count = 0
    for item in all_stock_items:
        item_code = item.item_code
        total_demand = item_demands.get(item_code, 0) # Get demand if it exists, otherwise 0.

        try:
            safety_stock = flt(item.get("custom_safety_stock", 0))
            lead_time = flt(item.get("custom_lead_time", 0))

            calculated_min_qty = 0
            calculated_max_qty = 0

            if total_demand > 0:
                # Calculate based on demand
                average_demand = total_demand / 3.0 # Average over 3 months
                calculated_min_qty = (average_demand * lead_time) + safety_stock
                calculated_max_qty = calculated_min_qty * 2
            else:
                # Default values if no sales history for this item
                calculated_min_qty = 5
                calculated_max_qty = 10

            # Update the Item document using frappe.db.set_value for efficiency.
            frappe.db.set_value("Item", item_code, {
                "custom_calculated_min_qty": calculated_min_qty,
                "custom_calculated_max_qty": calculated_max_qty
            }, update_modified=False) # Avoid updating 'modified' timestamp if not strictly necessary
            processed_item_count += 1

        except Exception as e:
            frappe.log_error(f"Error processing item {item_code} for min/max calculation: {e}", "Min/Max Calculation")
            continue

    frappe.logger("inaproc").info(f"Min/Max Quantities Calculated: Processed {processed_item_count} items successfully.")
