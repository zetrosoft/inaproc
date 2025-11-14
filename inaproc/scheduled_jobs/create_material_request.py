import frappe
from frappe.utils import getdate

def create_material_requests_and_notify():
    today = getdate()
    
    # List to hold items that need to be requested
    items_for_mr = []

    # Dapatkan semua Item yang relevan dan boleh dibeli
    # Filter berdasarkan is_purchase_item = 1
    items = frappe.get_list("Item", 
        filters={"is_stock_item": 1, "is_purchase_item": 1, "has_variants": 0}, 
        fields=["name", "item_code", "projected_qty", "custom_calculated_min_qty", "custom_calculated_max_qty"]
    )

    for item in items:
        projected_qty = item.projected_qty or 0
        calculated_min_qty = item.custom_calculated_min_qty or 0
        calculated_max_qty = item.custom_calculated_max_qty or 0

        if projected_qty < calculated_min_qty:
            qty_to_request = calculated_max_qty - projected_qty

            if qty_to_request > 0:
                # Tentukan target warehouse
                target_warehouse = None
                
                # Query langsung ke DocType Item Default
                item_default_entry = frappe.get_list("Item Default", 
                    filters={"parent": item.item_code}, # Filter berdasarkan nama item saat ini
                    fields=["default_warehouse"],
                    limit=1,# Hanya perlu satu entri
                    ignore_permissions=True
                )
                
                
                if item_default_entry and item_default_entry[0].default_warehouse:
                    target_warehouse = item_default_entry[0].default_warehouse
                
                if not target_warehouse:
                    target_warehouse = "Persediaan Bahan Baku - PSTS" # Default jika tidak ditemukan

                items_for_mr.append({
                    "item_code": item.item_code,
                    "qty": qty_to_request,
                    "warehouse": target_warehouse
                })
                print(f"{item.item_code} - {target_warehouse}")
                
    if items_for_mr:
        # Buat satu Material Request untuk semua item yang terkumpul
        material_request = frappe.new_doc("Material Request")
        material_request.material_request_type = "Purchase"
        material_request.request_type = "Gudang" # Sesuai permintaan user
        material_request.schedule_date = today
        
        for mr_item_data in items_for_mr:
            material_request.append("items", mr_item_data)
        
        try:
            material_request.insert(ignore_permissions=True)
            
            # Tambahkan komentar bahwa dokumen ini dibuat otomatis
            material_request.add_comment(
                "Info",
                "Dokumen ini dibuat secara otomatis oleh sistem karena stok mencapai level minimum untuk beberapa item."
            )
            
            material_request.submit()
            
            frappe.logger("inaproc").info(f"Material Request Created: Material Request {material_request.name} created for {len(items_for_mr)} items.")

            # Kirim Notifikasi
            send_reorder_notification(items_for_mr, material_request.name)

        except Exception as e:
            frappe.log_error(f"Error creating Material Request for multiple items: {e}", "Material Request Creation Error")

def send_reorder_notification(items_for_mr, material_request_name): # Changed signature
    # Definisikan peran yang akan menerima notifikasi
    target_roles = [
        "Purchase Manager", "Purchase User", 
        "Stock Manager", "Stock User",
        "Production Manager", "Production User"
    ]

    # Dapatkan semua user yang memiliki salah satu dari peran tersebut
    users_with_role = frappe.get_all("Has Role", 
        filters={"role": ["in", target_roles], "parenttype": "User"},
        fields=["parent"],
        distinct=True
    )
    
    user_names = [d.parent for d in users_with_role]

    if not user_names:
        frappe.logger("inaproc").warning(f"No users found for roles {target_roles} to send notification for Material Request {material_request_name}.")
        return

    # Dapatkan email dari user tersebut
    recipients_docs = frappe.get_all("User", filters={"name": ["in", user_names], "enabled": 1}, fields=["email"])
    recipients = [d.email for d in recipients_docs if d.email] # Corrected list comprehension

    if not recipients:
        frappe.logger("inaproc").warning(f"Found users but no valid emails for roles {target_roles} to send notification for Material Request {material_request_name}.")
        return

    # Buat daftar item untuk pesan notifikasi
    item_list_html = "<ul>"
    for item_data in items_for_mr:
        item_list_html += f"<li>{item_data['item_code']} (Qty: {item_data['qty']})</li>"
    item_list_html += "</ul>"

    subject = f"[Otomatis] Permintaan Material Baru: {material_request_name}"
    message = (f"Ini adalah notifikasi otomatis.\n\n"
               f"Sistem telah membuat Permintaan Material baru ({material_request_name}) karena stok beberapa item berada di bawah batas minimum.\n\n"
               f"<b>Detail Item yang Diminta:</b>\n"
               f"{item_list_html}\n"
               f"Silakan tinjau Permintaan Material pada link berikut:\n"
               f"<a href='{frappe.utils.get_url(f'/app/material-request/{material_request_name}')}'>Lihat Dokumen: {material_request_name}</a>\n\n"
               f"Terima kasih.")

    # Kirim Notifikasi In-app
    frappe.send_notification(
        recipients=user_names,
        subject=subject,
        type="Alert",
        doctype="Material Request",
        docname=material_request_name,
        message=message
    )

    # Kirim Notifikasi Email (masih dikomentari sesuai permintaan sebelumnya)
    # frappe.sendmail(
    #     recipients=recipients,
    #     subject=subject,
    #     content=message,
    #     now=True # Kirim segera
    # )

    frappe.logger("inaproc").info(f"Re-order Notification Sent: Notification sent for Material Request {material_request_name} to {', '.join(recipients)}")
