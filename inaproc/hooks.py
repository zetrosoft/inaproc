app_name = "inaproc"
app_title = "Inaproc"
app_publisher = "Bijak Technology"
app_description = "Custom inventory management"
app_email = "support@bijaktechnology.com"
app_license = "mit"

fixtures = ["Custom Field", "Print Format"]

scheduler_events = {
    "daily": [
        "inaproc.scheduled_jobs.calculate_min_max_qty.calculate_min_max_quantities",
        "inaproc.scheduled_jobs.create_material_request.create_material_requests_and_notify"
    ]
}

# ... (other hooks from original file) ...

doctype_js = {
    "Purchase Order": "public/js/purchase_order.js"
}

doc_events = {
    "Purchase Order": {
        "before_print": [
            "inaproc.utils.add_qr_to_context",
            "inaproc.utils.add_all_linked_addresses_to_context"
        ]
    },
    "Sales Order": {
        "before_print": "inaproc.utils.add_all_linked_addresses_to_context"
    },
    "Delivery Note": {
        "before_print": "inaproc.utils.add_all_linked_addresses_to_context"
    }
}

permission_query_conditions = {
 	"Item": "inaproc.permissions.get_item_access_conditions",
}

override_doctype_class = {
	"Item": "inaproc.overrides.item.CustomItem"
}

# Overriding Methods
# ------------------------------
override_whitelisted_methods = {
    "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice": 
    "inaproc.payment_terms_logic.custom_make_purchase_invoice"
}
