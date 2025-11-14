import frappe

def update_item_purchase_sales_flags():
    """
    Memperbarui flag allow_purchase dan allow_sales untuk DocType Item
    berdasarkan Item Group-nya.

    Skenario:
    - Item Group "Persediaan Barang Jadi" dan "Waste":
        - allow_purchase = 0
        - allow_sales = 1
    - Item Group lainnya:
        - allow_purchase = 1
        - allow_sales = 0
    """
    frappe.set_user("Administrator") # Pastikan script berjalan dengan izin Administrator

    # Ambil semua Item yang merupakan item stok
    items = frappe.get_list("Item", 
        filters={"is_stock_item": 1}, 
        fields=["name", "item_group", "is_purchase_item", "is_sales_item"]
    )

    updated_count = 0
    frappe.msgprint("Memulai pembaruan flag is_purchase_item dan is_sales_item untuk Item.") # Initial message

    for item_data in items:
        item_name = item_data.name
        item_group = item_data.item_group
        
        new_is_purchase_item = None
        new_is_sales_item = None

        # Tentukan nilai baru berdasarkan Item Group
        if item_group in ["Persediaan Barang Jadi", "Waste"]:
            new_is_purchase_item = 0
            new_is_sales_item = 1
        elif item_group == "Persediaan Barang Dalam Proses":
            new_is_purchase_item = 0
            new_is_sales_item = 0
        else:
            new_is_purchase_item = 1
            new_is_sales_item = 0
        
        # Hanya perbarui jika ada perubahan nilai untuk menghindari penulisan yang tidak perlu
        if (item_data.is_purchase_item != new_is_purchase_item or 
            item_data.is_sales_item != new_is_sales_item):
            
            try:
                frappe.db.set_value("Item", item_name, {
                    "is_purchase_item": new_is_purchase_item,
                    "is_sales_item": new_is_sales_item
                }, update_modified=False) # update_modified=False agar tidak mengubah timestamp modifikasi
                updated_count += 1
                frappe.logger("inaproc").info(f"Diperbarui Item {item_name}: item_group='{item_group}', is_purchase_item={new_is_purchase_item}, is_sales_item={new_is_sales_item}")
            except Exception as e:
                frappe.log_error(f"Gagal memperbarui Item {item_name}: {e}", "Update Item Flags")

    frappe.db.commit() # Commit semua perubahan ke database
    final_message = f"Selesai memperbarui flag is_purchase_item dan is_sales_item. Total item diperbarui: {updated_count}."
    if updated_count == 0:
        final_message += " Tidak ada item yang memerlukan pembaruan atau kondisi tidak terpenuhi."
    frappe.msgprint(final_message) # Final message
    frappe.logger("inaproc").info(final_message) # Keep logger for server-side logs
