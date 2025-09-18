
'''
Skrip untuk memperbarui default warehouse pada Item yang sudah ada.
'''

import frappe


def update_item_defaults():
    print("Memulai pembaruan default warehouse untuk Item...")

    company_name = "PT. SIUMANG TEMAN SUKSES"

    # Pemetaan akronim ke nama gudang grup yang diinginkan (sama seperti di migrate_warehouses.py)
    akronim_to_group_warehouse_map = {
        "INV": "Gudang RMPN",
        "FGH": "Finished Good",
        "WST": "Gudang Waste",
        "WIP": "Gudang Work In Process",
        "AST": "Gudang Umum",
        "ALL": "All Warehouses" # Untuk grup induk Item Group
    }

    # Dapatkan nama lengkap gudang induk utama (All Warehouses - PSTS)
    all_warehouses_group_name_raw = "All Warehouses"
    all_warehouses_group_name_full = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": all_warehouses_group_name_raw, "company": company_name},
        "name"
    )

    if not all_warehouses_group_name_full:
        print(f"ERROR: Gudang Induk Utama '{all_warehouses_group_name_raw}' tidak ditemukan. Tidak dapat mengatur default warehouse.")
        return

    # Dapatkan semua Item
    items = frappe.get_list("Item", fields=["name", "item_group"])

    for item_data in items:
        item_name = item_data["name"]
        item_group_name = item_data["item_group"]

        try:
            # Dapatkan dokumen Item
            item_doc = frappe.get_doc("Item", item_name)

            # Dapatkan akronim dari Item Group
            akronim_prefix = frappe.db.get_value("Item Group", item_group_name, "akronim")
            if not akronim_prefix:
                print(f"Peringatan: Akronim tidak ditemukan untuk Item Group '{item_group_name}' pada Item '{item_name}'. Default warehouse tidak diatur.")
                continue

            # Tentukan Gudang Default
            default_warehouse_name_raw = None
            # Jika Item Group bukan grup induk dan memiliki akronim yang valid
            if item_group_name != "All Item Groups" and akronim_prefix in akronim_to_group_warehouse_map:
                default_warehouse_name_raw = item_group_name # Nama gudang leaf sama dengan Item Group

                # Dapatkan nama lengkap gudang leaf
                full_default_warehouse_name = frappe.db.get_value(
                    "Warehouse",
                    {"warehouse_name": default_warehouse_name_raw, "company": company_name},
                    "name"
                )

                if not full_default_warehouse_name:
                    print(f"Peringatan: Gudang default '{default_warehouse_name_raw}' untuk Item Group '{item_group_name}' tidak ditemukan. Default warehouse tidak diatur untuk Item '{item_name}'.")
                    continue # Lanjutkan ke item berikutnya
            else:
                print(f"Peringatan: Item Group '{item_group_name}' tidak memiliki gudang default yang sesuai. Default warehouse tidak diatur untuk Item '{item_name}'.")
                continue # Lanjutkan ke item berikutnya

            # Hapus item_defaults yang sudah ada
            item_doc.item_defaults = []

            # Tambahkan Item Default baru
            item_doc.append("item_defaults", {
                "company": company_name,
                "default_warehouse": full_default_warehouse_name
            })

            item_doc.save(ignore_permissions=True)
            print(f"Berhasil memperbarui Item '{item_name}' dengan default warehouse: '{full_default_warehouse_name}'")

        except Exception as e:
            print(f"Terjadi error saat memperbarui Item '{item_name}': {e}")

    frappe.db.commit()
    print("\nPembaruan default warehouse untuk Item selesai.")

if __name__ == "__main__":
    update_item_defaults()
