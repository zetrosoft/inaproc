import frappe
from frappe.utils.csvutils import make_csv


@frappe.whitelist()
def get_stock_reconciliation_template_data(warehouse):
    if not warehouse:
        frappe.throw("Warehouse harus ditentukan.")

    # Dapatkan semua item dengan kuantitas positif di gudang yang ditentukan
    bins = frappe.get_list(
        "Bin",
        filters={"warehouse": warehouse, "actual_qty": (">", 0)},
        fields=["item_code", "actual_qty"]
    )

    if not bins:
        frappe.throw(f"Tidak ada item dengan stok di gudang '{warehouse}'.")

    # Siapkan header untuk spreadsheet
    headers = ["Item Code", "System Quantity", "Physical Quantity", "Warehouse"]
    data = [headers]

    # Isi data
    for b in bins:
        data.append([
            b.item_code,
            b.actual_qty,
            "",  # Kolom kosong untuk Physical Quantity
            warehouse
        ])

    # Mengembalikan data dalam format yang bisa diunduh sebagai CSV
    # Frappe akan menangani konversi ke CSV/XLSX jika dipanggil dari client script
    return data

@frappe.whitelist()
def get_items_for_tree_view():
    items = frappe.get_list(
        "Item",
        filters={"disabled": 0}, # Hanya item yang tidak dinonaktifkan
        fields=["name", "item_name", "item_group"]
    )
    return items

@frappe.whitelist()
def get_item_groups_for_tree_view():
    item_groups = frappe.get_list(
        "Item Group",
        fields=["name", "parent_item_group", "is_group"]
    )
    return item_groups
