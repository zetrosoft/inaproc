
'''
Skrip untuk migrasi Satuan (UOM) ke database Frappe.
'''

import frappe


def migrate_uoms():
    print("Memulai migrasi UOM...")

    # Daftar UOM unik dari PDF
    # Format: (nama_uom, harus_bilangan_bulat)
    uom_list = [
        ("Pcs", 1),
        ("Gram", 0),
        ("Liter", 0),
        ("Kg", 0),
        ("Set", 1),
        ("Roll", 1),
        ("Box", 1),
        ("ml", 0),
        ("Lembar", 1),
        ("Dus", 1),
        ("Meter", 0),
        ("Tabung", 1),
    ]

    for uom_name, is_whole_number in uom_list:
        if not frappe.db.exists("UOM", uom_name):
            try:
                doc = frappe.get_doc({
                    "doctype": "UOM",
                    "uom_name": uom_name,
                    "must_be_whole_number": is_whole_number
                })
                doc.insert(ignore_permissions=True)
                print(f"Berhasil membuat UOM: ''{uom_name}''")
            except Exception as e:
                print(f"Error saat membuat UOM ''{uom_name}'': {e}")
        else:
            print(f"UOM ''{uom_name}'' sudah ada, proses dilewati.")

    frappe.db.commit()
    print("\nMigrasi UOM selesai.")

if __name__ == "__main__":
    migrate_uoms()
