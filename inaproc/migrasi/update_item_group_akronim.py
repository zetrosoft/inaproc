
'''
Skrip untuk memperbarui custom field 'akronim' pada Item Group yang sudah ada.
'''

import frappe


def update_akronim_for_item_groups():
    print("Memulai pembaruan field 'akronim' pada Item Group...")

    # Dapatkan semua Item Group
    item_groups = frappe.get_list("Item Group", fields=["name", "akronim"])

    for group in item_groups:
        group_name = group["name"]
        current_akronim = group.get("akronim")

        # Hanya update jika akronim belum diatur atau berbeda
        if current_akronim != "INV":
            try:
                doc = frappe.get_doc("Item Group", group_name)
                doc.akronim = "INV"
                doc.save(ignore_permissions=True)
                print(f"Berhasil memperbarui Item Group '{group_name}' dengan akronim: INV")
            except Exception as e:
                print(f"Gagal memperbarui Item Group '{group_name}': {e}")
        else:
            print(f"Item Group '{group_name}' sudah memiliki akronim INV, dilewati.")

    frappe.db.commit()
    print("\nPembaruan akronim Item Group selesai.")

if __name__ == "__main__":
    update_akronim_for_item_groups()

