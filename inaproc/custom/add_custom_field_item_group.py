'''
Skrip untuk menambahkan custom field 'akronim' ke Doctype Item Group.
'''

import frappe


def add_custom_field():
    doctype_name = "Item Group"
    field_name = "akronim"

    # Periksa apakah field sudah ada
    if frappe.db.exists("Custom Field", {"dt": doctype_name, "fieldname": field_name}):
        print(f"Custom Field ''{field_name}'' sudah ada di Doctype ''{doctype_name}''.")
        return

    try:
        # Buat dan simpan Custom Field baru
        frappe.make_custom_field(
            doctype_name,
            {
                "fieldname": field_name,
                "label": "Akronim",
                "fieldtype": "Data",
                "insert_after": "item_group_name", # Posisi field di form
                "no_copy": 1,
            }
        )
        print(f"Berhasil menambahkan Custom Field ''{field_name}'' ke Doctype ''{doctype_name}''.")
        frappe.db.commit()

    except Exception as e:
        print(f"Gagal menambahkan custom field: {e}")

if __name__ == "__main__":
    add_custom_field()
