frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        const perms = frappe.perm.get_perm('Delivery Note');
        const is_reader = perms && perms.read && !perms.write;

        if (frm.doc.docstatus === 0 && frm.doc.custom_qc_validation_summary && is_reader) {
            frappe.msgprint({
                title: __('Ringkasan Validasi QC'),
                message: frm.doc.custom_qc_validation_summary,
                indicator: 'orange',
                wide: true
            });
        }
    }
});
