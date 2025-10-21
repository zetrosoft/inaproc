frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        // --- Logic to show/hide Print button ---
        if (frm.doc.docstatus === 1) { // Only show print button if PO is Submitted (docstatus 1)
            frm.add_custom_button(__('Print'), function() {
                frm.print_doc();
            }, __('Print'));
        } else {
            frm.remove_custom_button(__('Print'), __('Print'));
        }

        // REQUIREMENT 1: Tampilkan/Sembunyikan Tombol Unggah berdasarkan status
        frm.toggle_display('custom_upload_support_doc', frm.doc.docstatus === 0);

        // REQUIREMENT 2: Selalu expand section Dokumen Pendukung (DOM METHOD)
        setTimeout(() => {
            const section = frm.get_field('custom_po_support_docs_section');
            // Periksa apakah section ada dan dalam keadaan tertutup
            if (section && $(section.wrapper).hasClass('collapsed')) {
                // Jika ya, simulasikan klik untuk membukanya
                $(section.section_head).trigger('click');
            }
        }, 150); // Jeda singkat untuk memastikan render standar Frappe selesai

        // --- Grid Formatter for Preview (SIMPLE LINK) ---
        frm.fields_dict['custom_po_support_docs_table'].grid.update_docfield_property(
            'file_name', 'format', (value, doc) => {
                if (doc && doc.file_url) {
                    return `<a href="${doc.file_url}" target="_blank">${doc.file_name}</a>`;
                } else {
                    return value;
                }
            }
        );
        frm.refresh_field('custom_po_support_docs_table');
    },

    custom_upload_support_doc: function(frm) {
        // --- Custom Upload Logic (tetap sama) ---
        if (frm.is_new()) {
            frappe.msgprint(__("Silakan simpan dokumen terlebih dahulu sebelum mengunggah file."));
            return;
        }

        new frappe.ui.FileUploader({
            doctype: frm.doctype,
            docname: frm.docname,
            on_success: (file_doc) => {
                if (file_doc) {
                    frm.add_child('custom_po_support_docs_table', {
                        file_name: file_doc.file_name,
                        file_url: file_doc.file_url
                    });
                    frm.refresh_field('custom_po_support_docs_table');
                    frappe.show_alert({
                        message: __('Dokumen "{0}" berhasil diunggah. Jangan lupa simpan Purchase Order ini.', [file_doc.file_name]),
                        indicator: 'green'
                    });
                }
            }
        });
    }
});