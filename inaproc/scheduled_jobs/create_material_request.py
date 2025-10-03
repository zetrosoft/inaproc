import frappe
from frappe.utils import getdate

def create_material_requests_and_notify():
    today = getdate()

    # Dapatkan semua Item yang relevan
    items = frappe.get_list("Item", filters={"custom_inventory_section": 1}, fields=["name", "item_code", "projected_qty", "custom_calculated_min_qty", "custom_calculated_max_qty"])

    for item in items:
        projected_qty = item.projected_qty or 0
        calculated_min_qty = item.custom_calculated_min_qty or 0
        calculated_max_qty = item.custom_calculated_max_qty or 0

        if projected_qty < calculated_min_qty:
            qty_to_request = calculated_max_qty - projected_qty

            if qty_to_request > 0:
                # 1. Buat Material Request
                material_request = frappe.new_doc("Material Request")
                material_request.material_request_type = "Purchase"
                material_request.schedule_date = today
                material_request.append("items", {
                    "item_code": item.item_code,
                    "qty": qty_to_request,
                    "warehouse": frappe.db.get_single_value("Stock Settings", "default_warehouse") # Ambil default warehouse
                })
                try:
                    material_request.insert()
                    material_request.submit()
                    frappe.db.commit()
                    frappe.log_simple("Material Request Created", f"Material Request {material_request.name} created for {item.item_code} with qty {qty_to_request}")

                    # 2. Kirim Notifikasi
                    send_reorder_notification(item, qty_to_request, material_request.name)

                except Exception as e:
                    frappe.log_error(f"Error creating Material Request for {item.item_code}: {e}", "Material Request Creation Error")

def send_reorder_notification(item, qty_to_request, material_request_name):
    # Dapatkan Manajer Departemen Item
    department_manager_emails = []
    item_department = frappe.db.get_value("Item", item.name, "department") # Asumsi ada field department di Item
    if item_department:
        department_manager = frappe.get_list("Employee", filters={"department": item_department, "designation": "Department Manager"}, fields=["user_id"])
        for dm in department_manager:
            if dm.user_id: department_manager_emails.append(frappe.db.get_value("User", dm.user_id, "email"))

    # Dapatkan Pengguna dengan peran Purchasing User dan Purchasing Manager
    purchasing_user_emails = frappe.get_list("User", filters={"roles": ["like", "%Purchasing User%"]}, fields=["email"])
    purchasing_manager_emails = frappe.get_list("User", filters={"roles": ["like", "%Purchasing Manager%"]}, fields=["email"])

    recipients = list(set(department_manager_emails + [u.email for u in purchasing_user_emails] + [u.email for u in purchasing_manager_emails]))
    recipients = [r for r in recipients if r] # Filter out None or empty emails

    if not recipients: return # Tidak ada penerima, jangan kirim notifikasi

    subject = f"Re-order Alert: Material Request for {item.item_code}"
    message = f"Halo,\n\nSistem telah membuat Permintaan Material baru untuk item {item.item_code} karena stok di bawah batas minimum.\n\nDetail Permintaan:\nItem Code: {item.item_code}\nJumlah Diminta: {qty_to_request}\nMaterial Request ID: {material_request_name}\n\nSilakan tinjau Permintaan Material ini: {frappe.utils.get_url(f'/app/material-request/{material_request_name}')}\n\nTerima kasih."

    # Kirim Notifikasi In-app
    for recipient_email in recipients:
        user_id = frappe.db.get_value("User", {"email": recipient_email}, "name")
        if user_id:
            frappe.send_notification(
                recipients=[user_id],
                subject=subject,
                message=message,
                doctype="Material Request",
                name=material_request_name,
                # email_content=message, # Untuk notifikasi email
                # email_args={"attachments": []}
            )

    # Kirim Notifikasi Email
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        content=message,
        now=True # Kirim segera
    )

    frappe.log_simple("Re-order Notification Sent", f"Notification sent for {item.item_code} to {', '.join(recipients)}")
