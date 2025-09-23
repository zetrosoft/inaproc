import frappe
from frappe.utils import getdate
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice as original_erpnext_make_purchase_invoice

@frappe.whitelist()
def custom_make_purchase_invoice(source_name, target_doc=None, args=None):
    """
    Mengganti make_purchase_invoice standar untuk menambahkan logika termin pembayaran kustom.
    """
    frappe.log_error("STARTING: custom_make_purchase_invoice called!") # Log awal

    try:
        # Panggil fungsi ERPNext asli make_purchase_invoice
        mapped_pi = original_erpnext_make_purchase_invoice(source_name, target_doc, args)

        frappe.log_error(f"SUCCESS: Original function returned mapped_pi: {mapped_pi.name}")

        # Dapatkan dokumen Purchase Order sumber
        source_po = frappe.get_doc("Purchase Order", source_name,ignore_permissions=True)

        # Salin juga Payment Term Template
        mapped_pi.payment_terms_template = source_po.payment_terms_template

        # Logika penyalinan manual...
        frappe.log_error("Processing payment schedule copy.")

        mapped_pi.set("payment_schedule", [])  # Clear existing terms if any

        if source_po.payment_schedule:
            for term in source_po.payment_schedule:
                new_term = mapped_pi.append("payment_schedule", {})
                new_term.payment_term = term.payment_term
                new_term.description = term.description
                new_term.due_date = term.due_date
                new_term.invoice_portion = term.invoice_portion
                new_term.payment_amount = term.payment_amount
                new_term.custom_is_active = term.get("custom_is_active", 0)

        frappe.log_error("Payment schedule copied. Attempting to return modified PI.")

        return mapped_pi
        
    except frappe.exceptions.PermissionError as e:
        # Menangkap error izin secara spesifik
        frappe.log_error(str(e), "Permission Error in custom_make_purchase_invoice")
        # Melempar ulang error dengan pesan yang sama
        raise e
    except Exception as e:
        # Menangkap error lain
        frappe.log_error(frappe.get_traceback(), "General Error in custom_make_purchase_invoice")
        # Melemparkan error yang lebih umum jika bukan masalah izin
        frappe.throw(f"An unexpected error occurred: {str(e)}")
        
    
