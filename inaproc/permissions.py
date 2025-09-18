import frappe


def get_item_access_conditions(user):
    if not user:
        return None

    # Dapatkan Employee DocType untuk pengguna yang sedang login
    employee = frappe.db.get_value("Employee", {"user_id": user}, ["department"], as_dict=True)

    if not employee or not employee.department:
        # Jika pengguna bukan karyawan atau tidak memiliki departemen,
        # kembalikan kondisi yang tidak mengizinkan akses ke item apa pun
        return {"name": "IS NULL"}

    # Dapatkan daftar Item Group yang diizinkan untuk departemen ini
    allowed_item_groups = frappe.get_list(
        "Item Group Access",
        filters={"department": employee.department},
        fields=["item_group"]
    )

    if not allowed_item_groups:
        # Jika tidak ada Item Group yang diizinkan untuk departemen ini,
        # kembalikan kondisi yang tidak mengizinkan akses ke item apa pun
        return {"name": "IS NULL"}

    # Ekstrak nama Item Group dari hasil query
    item_group_names = [d.item_group for d in allowed_item_groups]

    # Kembalikan kondisi untuk memfilter Item berdasarkan Item Group yang diizinkan
    return {
        "Item": {
            "item_group": ["in", item_group_names]
        }
    }
