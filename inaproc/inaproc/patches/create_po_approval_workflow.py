import frappe

def execute():
    # Ensure required roles exist
    roles_to_create = ["Purchase User", "Purchase Manager", "Purchase Master Manager"]
    for role_name in roles_to_create:
        if not frappe.db.exists("Role", role_name):
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.insert(ignore_permissions=True)
            frappe.db.commit()
            frappe.msgprint(f"Role '{role_name}' created.")
        else:
            frappe.msgprint(f"Role '{role_name}' already exists.")

    if not frappe.db.exists("Workflow", "Purchase Order Approval"):
        workflow = frappe.new_doc("Workflow")
        workflow.name = "Purchase Order Approval"
        workflow.document_type = "Purchase Order"
        workflow.is_active = 1
        workflow.workflow_state_field = "workflow_state" # Custom field untuk menyimpan status workflow

        # States (Status)
        workflow.append("states", {
            "state": "Draft",
            "allow_edit": "All",
            "doc_status": "0" # Draft
        })
        workflow.append("states", {
            "state": "Pending Approval (Purchase Manager)",
            "allow_edit": "", # Corrected
            "doc_status": "0" # Tetap Draft sampai Approved
        })
        workflow.append("states", {
            "state": "Pending Approval (Purchase Master Manager)",
            "allow_edit": "", # Corrected
            "doc_status": "0"
        })
        workflow.append("states", {
            "state": "Approved",
            "allow_edit": "", # Corrected
            "doc_status": "1" # Submitted
        })
        workflow.append("states", {
            "state": "Rejected",
            "allow_edit": "", # Corrected
            "doc_status": "2" # Cancelled
        })

        # Transitions (Transisi antar Status)
        # 1. Draft -> Pending Approval (Purchase Manager)
        workflow.append("transitions", {
            "state": "Draft",
            "action": "Submit",
            "next_state": "Pending Approval (Purchase Manager)",
            "allowed_roles": ["Purchase User"],
            "allow_self_approval": 0
        })
        # 2. Pending Approval (Purchase Manager) -> Approved (jika nilai <= 10 Juta)
        workflow.append("transitions", {
            "state": "Pending Approval (Purchase Manager)",
            "action": "Approve",
            "next_state": "Approved",
            "allowed_roles": ["Purchase Manager"],
            "condition": "doc.grand_total <= 10000000", # Kondisi langsung
            "allow_self_approval": 0
        })
        # 3. Pending Approval (Purchase Manager) -> Pending Approval (Purchase Master Manager) (jika nilai > 10 Juta)
        workflow.append("transitions", {
            "state": "Pending Approval (Purchase Manager)",
            "action": "Approve",
            "next_state": "Pending Approval (Purchase Master Manager)",
            "allowed_roles": ["Purchase Manager"],
            "condition": "doc.grand_total > 10000000", # Kondisi langsung
            "allow_self_approval": 0
        })
        # 4. Pending Approval (Purchase Manager) -> Rejected
        workflow.append("transitions", {
            "state": "Pending Approval (Purchase Manager)",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed_roles": ["Purchase Manager"],
            "allow_self_approval": 0
        })
        # 5. Pending Approval (Purchase Master Manager) -> Approved
        workflow.append("transitions", {
            "state": "Pending Approval (Purchase Master Manager)",
            "action": "Approve",
            "next_state": "Approved",
            "allowed_roles": ["Purchase Master Manager"],
            "allow_self_approval": 0
        })
        # 6. Pending Approval (Purchase Master Manager) -> Rejected
        workflow.append("transitions", {
            "state": "Pending Approval (Purchase Master Manager)",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed_roles": ["Purchase Master Manager"],
            "allow_self_approval": 0
        })

        workflow.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.msgprint("Purchase Order Approval Workflow created successfully.")
    else:
        frappe.msgprint("Purchase Order Approval Workflow already exists.")

    # Tambahkan custom field 'workflow_state' ke Purchase Order jika belum ada
    if not frappe.db.exists("Custom Field", {"dt": "Purchase Order", "fieldname": "workflow_state"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Purchase Order"
        custom_field.fieldname = "workflow_state"
        custom_field.label = "Workflow State"
        custom_field.fieldtype = "Data"
        custom_field.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.msgprint("Custom Field 'workflow_state' added to Purchase Order.")