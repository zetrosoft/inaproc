import base64
import io

import frappe
import pyqrcode


def add_qr_to_context(doc, method, print_settings=None):
    url = frappe.utils.get_url_to_form(doc.doctype, doc.name)

    try:
        qr = pyqrcode.create(url)
        buffer = io.BytesIO()
        qr.png(buffer, scale=6)

        png_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        doc.custom_qr_code = f'<img src="data:image/png;base64,{png_data}" />'
    except Exception:
        error_message = frappe.get_traceback()
        frappe.log_error(error_message, "Inaproc QR Code Generation Failed")
        doc.custom_qr_code = ""


def get_linked_address(link_doctype, link_name):
    """
    Mengambil alamat utama yang tertaut ke sebuah dokumen secara dinamis.
    Prioritas Pencarian:
    1. Untuk 'Company': Alamat dengan flag 'is_your_company_address'.
    2. Untuk lainnya: Alamat dengan tipe 'Billing'.
    3. Jika tidak ada: Alamat pertama yang tertaut.
    """
    base_filters = [
        ["Dynamic Link", "link_doctype", "=", link_doctype],
        ["Dynamic Link", "link_name", "=", link_name],
    ]

    # 1. Define priority filters
    priority_filters = list(base_filters)
    if link_doctype == 'Company':
        priority_filters.append(["is_your_company_address", "=", 1])
    else:
        priority_filters.append(["address_type", "=", "Billing"])

    # 2. Try to find address with priority filters
    address_name = frappe.db.get_value("Address", priority_filters, "name")

    # 3. If not found, try to find ANY linked address (fallback)
    if not address_name:
        address_name = frappe.db.get_value("Address", base_filters, "name")

    if not address_name:
        return None

    address_doc = frappe.get_doc("Address", address_name)

    # Format alamat secara manual
    parts = [
        address_doc.address_line1,
        address_doc.address_line2,
        address_doc.city,
        address_doc.state,
        address_doc.pincode,
        address_doc.country,
    ]
    formatted_address = ", ".join(filter(None, parts))

    address_data = address_doc.as_dict()
    address_data['formatted_address'] = formatted_address

    return address_data


def add_all_linked_addresses_to_context(doc, method, print_settings=None):
    # Daftar field yang kemungkinan memiliki alamat tertaut
    fields_to_check = ["customer", "supplier", "company"]

    for field in fields_to_check:
        if doc.get(field):
            link_doctype = field.capitalize()
            link_name = doc.get(field)

            address = get_linked_address(link_doctype, link_name)

            if address:
                doc.set(f"custom_{field}_address", address)
