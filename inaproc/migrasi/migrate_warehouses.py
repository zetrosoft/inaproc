'''
Skrip untuk migrasi Gudang (Warehouse) berdasarkan Item Group dan akronimnya.
'''

import frappe


def migrate_warehouses():
    print("Memulai migrasi Gudang berdasarkan akronim...")

    company_name = "PT. SIUMANG TEMAN SUKSES" # Nama perusahaan untuk field 'company'
    all_warehouses_group_name_raw = "All Warehouses" # Nama gudang induk utama yang kita inginkan

    # Pemetaan akronim ke nama gudang grup yang diinginkan
    akronim_to_group_warehouse_map = {
        "INV": "Gudang RMPN",
        "FGH": "Finished Good",
        "WST": "Gudang Waste",
        "WIP": "Gudang Work In Process",
        "AST": "Gudang Umum",
        "ALL": "All Warehouses" # Untuk grup induk Item Group, tidak digunakan sebagai nama gudang fisik
    }

    # --- FASE 1: Buat Gudang Induk Utama ---
    all_warehouses_group_name_full = None
    # Coba dapatkan nama lengkap gudang induk jika sudah ada
    existing_main_warehouse_full_name = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": all_warehouses_group_name_raw, "company": company_name},
        "name"
    )

    if existing_main_warehouse_full_name:
        all_warehouses_group_name_full = existing_main_warehouse_full_name
        print(f"Gudang Induk Utama ''{all_warehouses_group_name_full}'' sudah ada.")
    else:
        try:
            doc = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": all_warehouses_group_name_raw,
                "company": company_name,
                "is_group": 1,
                "parent_warehouse": None,
            })
            doc.insert(ignore_permissions=True)
            all_warehouses_group_name_full = doc.name # Dapatkan nama lengkap yang dibuat Frappe
            print(f"Berhasil membuat Gudang Induk Utama: ''{all_warehouses_group_name_full}''")
            frappe.db.commit() # Commit setelah membuat induk
        except Exception as e:
            print(f"Gagal membuat Gudang Induk Utama ''{all_warehouses_group_name_raw}'': {e}")
            return # Hentikan jika gudang induk gagal dibuat

    if not all_warehouses_group_name_full:
        print("ERROR: Nama lengkap gudang induk tidak dapat ditentukan. Migrasi dibatalkan.")
        return

    # --- FASE 2: Buat Gudang Grup berdasarkan Akronim ---
    # Dapatkan semua Item Group beserta akronimnya
    item_groups_with_akronim = frappe.get_list("Item Group", fields=["name", "akronim"])

    # Kumpulkan akronim unik yang akan menjadi gudang grup
    unique_akronims_from_groups = set()
    for ig in item_groups_with_akronim:
        akronim = ig.get("akronim")
        if akronim and akronim != "ALL": # ALL adalah akronim untuk All Item Groups
            unique_akronims_from_groups.add(akronim)

    # Dictionary untuk menyimpan nama lengkap gudang grup akronim
    akronim_full_warehouse_names = {}

    for akronim in unique_akronims_from_groups:
        group_warehouse_name_raw = akronim_to_group_warehouse_map.get(akronim)
        if not group_warehouse_name_raw:
            print(f"Peringatan: Akronim ''{akronim}'' tidak memiliki pemetaan nama gudang grup. Dilewati.")
            continue

        group_warehouse_name_full = None
        # Coba dapatkan nama lengkap gudang grup jika sudah ada
        existing_group_warehouse_full_name = frappe.db.get_value(
            "Warehouse",
            {"warehouse_name": group_warehouse_name_raw, "company": company_name},
            "name"
        )

        if existing_group_warehouse_full_name:
            group_warehouse_name_full = existing_group_warehouse_full_name
            print(f"Gudang Grup ''{group_warehouse_name_full}'' sudah ada.")
        else:
            try:
                doc = frappe.get_doc({
                    "doctype": "Warehouse",
                    "warehouse_name": group_warehouse_name_raw,
                    "company": company_name,
                    "is_group": 1, # Ini adalah gudang grup
                    "parent_warehouse": all_warehouses_group_name_full, # Gunakan nama lengkap induk
                })
                doc.insert(ignore_permissions=True)
                group_warehouse_name_full = doc.name # Dapatkan nama lengkap yang dibuat Frappe
                print(f"Berhasil membuat Gudang Grup: ''{group_warehouse_name_full}'' (Akronim: ''{akronim}'')")
            except Exception as e:
                print(f"Gagal membuat Gudang Grup ''{group_warehouse_name_raw}'' (Akronim: ''{akronim}'') : {e}")

        if group_warehouse_name_full:
            akronim_full_warehouse_names[akronim] = group_warehouse_name_full

    frappe.db.commit() # Commit setelah membuat semua gudang grup

    # --- FASE 3: Buat Gudang Leaf berdasarkan Item Group ---
    for item_group in item_groups_with_akronim:
        item_group_name = item_group["name"]
        akronim = item_group.get("akronim")

        # Lewati Item Group induk atau yang tidak memiliki akronim valid
        if item_group_name == "All Item Groups" or not akronim or akronim not in akronim_to_group_warehouse_map:
            continue

        warehouse_name_raw = item_group_name # Nama gudang leaf sama dengan Item Group

        # Dapatkan nama lengkap parent gudang grup dari dictionary
        parent_group_warehouse_name_full = akronim_full_warehouse_names.get(akronim)

        if not parent_group_warehouse_name_full:
            print(f"ERROR: Parent Gudang Grup tidak ditemukan di dictionary untuk Item Group ''{item_group_name}'' (Akronim: ''{akronim}''). Gudang Leaf ''{warehouse_name_raw}'' dilewati.")
            continue

        # Coba dapatkan nama lengkap gudang leaf jika sudah ada
        existing_leaf_warehouse_full_name = frappe.db.get_value(
            "Warehouse",
            {"warehouse_name": warehouse_name_raw, "company": company_name},
            "name"
        )

        if existing_leaf_warehouse_full_name:
            print(f"Gudang Leaf ''{existing_leaf_warehouse_full_name}'' sudah ada, dilewati.")
        else:
            try:
                doc = frappe.get_doc({
                    "doctype": "Warehouse",
                    "warehouse_name": warehouse_name_raw,
                    "company": company_name,
                    "is_group": 0, # Ini adalah gudang leaf
                    "parent_warehouse": parent_group_warehouse_name_full, # Gunakan nama lengkap parent
                })
                doc.insert(ignore_permissions=True)
                print(f"Berhasil membuat Gudang Leaf: ''{doc.name}'' (Parent: ''{parent_group_warehouse_name_full}'')")
            except Exception as e:
                print(f"Gagal membuat Gudang Leaf ''{warehouse_name_raw}'' (Parent: ''{parent_group_warehouse_name_full}'') : {e}")

    # Rebuild tree structure untuk Warehouse
    try:
        from frappe.utils.nestedset import rebuild_tree
        rebuild_tree("Warehouse", "parent_warehouse")
        frappe.db.commit()
        print("\nStruktur pohon (tree) Warehouse berhasil dibangun ulang.")
    except Exception as e:
        print(f"\nError saat membangun ulang struktur pohon Warehouse: {e}")

    frappe.db.commit()
    print("\nMigrasi Gudang selesai.")

if __name__ == "__main__":
    migrate_warehouses()
