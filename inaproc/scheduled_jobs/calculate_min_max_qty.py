import frappe
from frappe.utils import getdate, add_months, flt

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
    """
    today = getdate()
    three_months_ago = add_months(today, -3)
    
    item_demands = {}

    # 1. Get all relevant finished goods (items that are sold and have a BOM).
    finished_goods = frappe.get_list("Item", 
        filters={"is_stock_item": 1, "default_bom": ["!=", ""]}, 
        fields=["name", "item_code"]
    )

    # 2. Calculate sales demand for finished goods and derived demand for raw materials.
    for fg_item in finished_goods:
        # Get total sales quantity for the finished good in the last 3 months.
        sales_qty = frappe.db.sql("""
            SELECT SUM(qty)
            FROM `tabSales Invoice Item`
            WHERE item_code = %s
              AND docstatus = 1
              AND posting_date >= %s
        """, (fg_item.item_code, three_months_ago))[0][0] or 0
        
        total_sales_qty = flt(sales_qty)

        if total_sales_qty > 0:
            # Add finished good demand to the dictionary.
            item_demands[fg_item.item_code] = item_demands.get(fg_item.item_code, 0) + total_sales_qty

            # Explode BOM to find raw material requirements.
            required_materials = get_bom_material_for_production(fg_item.item_code, total_sales_qty)
            
            for material, qty in required_materials.items():
                item_demands[material] = item_demands.get(material, 0) + qty

    # 3. Calculate and update min/max quantities for all items with calculated demand.
    for item_code, total_demand in item_demands.items():
        if total_demand <= 0:
            continue

        try:
            # Get item-specific details (safety stock, lead time).
            item_doc = frappe.get_doc("Item", item_code)
            safety_stock = flt(item_doc.get("custom_safety_stock", 0))
            lead_time = flt(item_doc.get("custom_lead_time", 0))

            # Calculate average demand over the period (3 months).
            average_demand = total_demand / 3.0

            if total_demand > 0:
                calculated_min_qty = (average_demand * lead_time) + safety_stock
                calculated_max_qty = calculated_min_qty * 2  # Simple example: max is twice the min.
            else:
                # Default values if no sales history
                calculated_min_qty = 5  # Example default
                calculated_max_qty = 10 # Example default

            # Update the Item document.
            item_doc.custom_calculated_min_qty = calculated_min_qty
            item_doc.custom_calculated_max_qty = calculated_max_qty
            item_doc.save(ignore_permissions=True)
        except frappe.DoesNotExistError:
            frappe.log_error(f"Item {item_code} not found, skipping min/max calculation.", "Min/Max Calculation")
            continue


    frappe.db.commit()
    frappe.logger("inaproc").info(f"Min/Max Quantities Calculated: Processed {len(item_demands)} items successfully.")
    frappe.msgprint(f"Min/Max Quantities Calculated: Processed {len(item_demands)} items successfully.")
