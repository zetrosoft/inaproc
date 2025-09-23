app_name = "inaproc"
app_title = "Inaproc"
app_publisher = "Bijak Technology"
app_description = "Custom inventory management"
app_email = "support@bijaktechnology.com"
app_license = "mit"

fixtures = ["Client Script", "Custom Item Hierarchy"]

# ... (other hooks from original file) ...

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
