import frappe
from frappe.model.document import Document

class DepartmentItemGroup(Document):
	pass

@frappe.whitelist()
def get_item_counts_for_item_groups(item_group_names):
    """
    Mengembalikan jumlah item untuk setiap grup item yang diberikan.
    """
    item_counts = {}
    if not isinstance(item_group_names, list):
        item_group_names = frappe.parse_json(item_group_names)

    if item_group_names:
        # Menggunakan frappe.db.sql untuk query langsung
        # Pastikan item_group_names di-escape dengan benar untuk mencegah SQL Injection
        escaped_item_group_names = [frappe.db.escape(name) for name in item_group_names]
        
        # Query untuk mendapatkan jumlah item per item_group
        # Menggunakan GROUP BY untuk menghitung item di setiap grup
        result = frappe.db.sql(
            """
            SELECT item_group, COUNT(name)
            FROM `tabItem`
            WHERE item_group IN ({})
            GROUP BY item_group
            """.format(", ".join(escaped_item_group_names)),
            as_dict=True
        )
        
        for row in result:
            item_counts[row.item_group] = row["COUNT(name)"]
            
    return item_counts