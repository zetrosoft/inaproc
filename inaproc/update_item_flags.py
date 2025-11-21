import frappe


def update_item_purchase_sales_flags():
    """
    Memperbarui flag allow_purchase, allow_sales, dan pengaturan QC untuk DocType Item
    berdasarkan Item Group-nya.
    """
    frappe.set_user("Administrator")

    # Ambil semua Item yang merupakan item stok beserta field QC
    items = frappe.get_list("Item",
        filters={"is_stock_item": 1},
        fields=[
            "name", "item_group", "is_purchase_item", "is_sales_item",
            "inspection_required_before_purchase", "inspection_required_on_manufacture",
            "inspection_required_before_delivery", "quality_inspection_template"
        ]
    )

    updated_count = 0
    frappe.msgprint("Memulai pembaruan flag dan pengaturan QC untuk Item.")

    # Cek keberadaan template sebelum loop untuk efisiensi
    template_bahan_baku = "QC Bahan Baku Makanan"
    template_barang_jadi = "QC Makanan Ringan Si Umang"
    bahan_baku_exists = frappe.db.exists("Quality Inspection Template", template_bahan_baku)
    barang_jadi_exists = frappe.db.exists("Quality Inspection Template", template_barang_jadi)

    for item_data in items:
        item_name = item_data.name
        item_group = item_data.item_group

        # Inisialisasi nilai baru
        update_dict = {}

        # Tentukan nilai baru berdasarkan Item Group
        if item_group == "Persediaan Bahan Baku":
            update_dict = {
                "is_purchase_item": 1,
                "is_sales_item": 0,
                "inspection_required_before_purchase": 1,
                "inspection_required_on_manufacture": 0,
                "inspection_required_before_delivery": 0,
            }
            if bahan_baku_exists:
                update_dict["quality_inspection_template"] = template_bahan_baku

        elif item_group == "Persediaan Barang Jadi":
            update_dict = {
                "is_purchase_item": 0,
                "is_sales_item": 1,
                "inspection_required_before_purchase": 0,
                "inspection_required_on_manufacture": 1,
                "inspection_required_before_delivery": 1,
            }
            if barang_jadi_exists:
                update_dict["quality_inspection_template"] = template_barang_jadi

        elif item_group == "Waste":
            update_dict = {"is_purchase_item": 0, "is_sales_item": 1}

        elif item_group == "Persediaan Barang Dalam Proses":
            update_dict = {"is_purchase_item": 0, "is_sales_item": 0}

        else: # Untuk grup lain seperti Bahan Baku
            update_dict = {
                "is_purchase_item": 1,
                "is_sales_item": 0,
                "inspection_required_before_purchase": 0,
                "inspection_required_on_manufacture": 0,
                "inspection_required_before_delivery": 0,
            }

        # Cek apakah ada perubahan nilai sebelum melakukan update
        is_changed = False
        for key, value in update_dict.items():
            if item_data.get(key) != value:
                is_changed = True
                break

        if is_changed:
            try:
                frappe.db.set_value("Item", item_name, update_dict, update_modified=False)
                updated_count += 1
                frappe.logger("inaproc").info(f"Diperbarui Item {item_name}: {update_dict}")
            except Exception as e:
                frappe.log_error(f"Gagal memperbarui Item {item_name}: {e}", "Update Item Flags")

    frappe.db.commit()
    final_message = f"Selesai memperbarui flag dan pengaturan QC. Total item diperbarui: {updated_count}."
    if updated_count == 0:
        final_message += " Tidak ada item yang memerlukan pembaruan."
    frappe.msgprint(final_message)
    frappe.logger("inaproc").info(final_message)
