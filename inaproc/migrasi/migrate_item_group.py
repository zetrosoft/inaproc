'''
Skrip untuk migrasi Item Group ke database Frappe, membaca akronim dari CSV.
'''

import csv

import frappe

CSV_FILE_PATH = "/Users/user/Projects/custom-siumang/Material master.csv"

def migrate_item_groups_with_akronim():
    print("Memulai migrasi Item Group dengan akronim dari CSV...")

    item_group_data = {}
    try:
        with open(CSV_FILE_PATH, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                kategori_barang = row.get('Kategori Barang', '').strip()
                jenis_barang = row.get('Jenis Barang', '').strip()
                if kategori_barang and jenis_barang:
                    item_group_data[kategori_barang] = jenis_barang
    except FileNotFoundError:
        print(f"ERROR: File CSV tidak ditemukan di '{CSV_FILE_PATH}'")
        return
    except Exception as e:
        print(f"Terjadi error saat membaca file CSV: {e}")
        return

    # Tambahkan grup induk jika belum ada di CSV (atau jika ingin memastikan)
    if "All Item Groups" not in item_group_data:
        item_group_data["All Item Groups"] = "ALL" # Default akronim untuk root

    # Urutkan data agar grup induk diproses terlebih dahulu
    sorted_groups = sorted(item_group_data.items(), key=lambda item: 0 if item[0] == "All Item Groups" else 1)

    for group_name, akronim_value in sorted_groups:
        parent_item_group = None
        if group_name != "All Item Groups":
            parent_item_group = "All Item Groups"

        if not frappe.db.exists("Item Group", group_name):
            try:
                doc = frappe.get_doc({
                    "doctype": "Item Group",
                    "item_group_name": group_name,
                    "is_group": 1,
                    "parent_item_group": parent_item_group,
                    "akronim": akronim_value # Set akronim dari CSV
                })
                doc.insert(ignore_permissions=True)
                print(f"Berhasil membuat Item Group: ''{group_name}'' dengan akronim ''{akronim_value}''")
            except Exception as e:
                print(f"Gagal membuat Item Group ''{group_name}'': {e}")
        else:
            # Jika grup sudah ada, update akronimnya
            try:
                doc = frappe.get_doc("Item Group", group_name)
                if doc.akronim != akronim_value:
                    doc.akronim = akronim_value
                    doc.save(ignore_permissions=True)
                    print(f"Berhasil memperbarui akronim Item Group ''{group_name}'' menjadi ''{akronim_value}''")
                else:
                    print(f"Item Group ''{group_name}'' sudah ada dan akronim sudah benar, dilewati.")
            except Exception as e:
                print(f"Gagal memperbarui Item Group ''{group_name}'': {e}")

    # Rebuild tree structure setelah semua parent diatur
    try:
        from frappe.utils.nestedset import rebuild_tree
        rebuild_tree("Item Group", "parent_item_group")
        frappe.db.commit()
        print("\nStruktur pohon (tree) Item Group berhasil dibangun ulang.")
    except Exception as e:
        print(f"\nError saat membangun ulang struktur pohon Item Group: {e}")

    frappe.db.commit()
    print("\nMigrasi Item Group selesai.")

if __name__ == "__main__":
    migrate_item_groups_with_akronim()
