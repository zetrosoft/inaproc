frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        // Cek jika user punya akses baca tapi tidak punya akses tulis
        const perms = frappe.perm.get_perm('Purchase Receipt');
        const is_reader = perms && perms.read && !perms.write;

        // Tampilkan popup jika:
        // 1. Dokumen masih draft (docstatus === 0)
        // 2. Field ringkasan validasi berisi data
        // 3. User adalah 'reader' (sesuai definisi di atas)
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
