import frappe


def get_item_access_conditions(user):
    if not user:
        return None

    # Administrator dapat melihat semua item, abaikan batasan departemen
    if user == "Administrator":
        return None

    # Dapatkan Employee DocType untuk pengguna yang sedang login
    employee = frappe.db.get_value("Employee", {"user_id": user}, ["department"], as_dict=True)

    # Jika pengguna bukan karyawan atau tidak memiliki departemen,
    # kembalikan kondisi yang tidak mengizinkan akses ke item apa pun
    if not employee or not employee.get("department"):
        return "`tabItem`.`name` IS NULL"

    # Dapatkan daftar Department Item Group untuk departemen ini
    department_item_groups_docs = frappe.get_list(
        "Department Item Group",
        filters={"department": employee.department},
        fields=["name"] # Hanya perlu nama untuk mengambil dokumen lengkap
    )

    item_group_names = []
    if department_item_groups_docs:
        for doc_name in department_item_groups_docs:
            # Ambil dokumen lengkap Department Item Group
            dig_doc = frappe.get_doc("Department Item Group", doc_name.name)
            # Iterasi melalui child table item_groups
            for item_group_item in dig_doc.item_groups:
                item_group_names.append(item_group_item.item_group)

    if not item_group_names:
        # Jika tidak ada Item Group yang diizinkan untuk departemen ini,
        # kembalikan kondisi yang tidak mengizinkan akses ke item apa pun
        return "`tabItem`.`name` IS NULL"

    # Kembalikan kondisi untuk memfilter Item berdasarkan Item Group yang diizinkan
    # Pastikan nama grup di-escape dengan benar untuk SQL
    escaped_item_group_names = [frappe.db.escape(name) for name in item_group_names]
    sql_condition = "`tabItem`.`item_group` IN ({})".format(", ".join(escaped_item_group_names))
    return sql_condition