frappe.ui.form.on('Department Item Group', {
    refresh: function(frm) {
        // Sembunyikan child table default
        frm.toggle_display('item_groups', false);

        // Tambahkan area kustom untuk checkbox di bawah field department
        if (!frm.item_group_checkbox_container) {
            frm.item_group_checkbox_container = $('<div class="form-group">\n                <label class="control-label">Allowed Item Groups</label>\n                <div class="control-value" id="item_group_checkbox_area"></div>\n            </div>').insertAfter(frm.get_field('department').wrapper);
        }

        // Tampilkan/Sembunyikan area checkbox item group berdasarkan keberadaan departemen
        if (frm.doc.department) {
            $('#item_group_checkbox_area').closest('.form-group').show();
            load_item_group_checkboxes(frm);
        } else {
            $('#item_group_checkbox_area').closest('.form-group').hide();
            $('#item_group_checkbox_area').empty();
        }

        // Set custom query for department field to exclude "All Departments"
        frm.set_query('department', function() {
            return {
                filters: {
                    'name': ['!=', 'All Departments']
                }
            };
        });
    },

    department: function(frm) {
        // Muat ulang checkbox ketika departemen berubah
        if (frm.doc.department) {
            $('#item_group_checkbox_area').closest('.form-group').show();
            load_item_group_checkboxes(frm);
        } else {
            $('#item_group_checkbox_area').closest('.form-group').hide();
            $('#item_group_checkbox_area').empty();
        }
    }
});

function load_item_group_checkboxes(frm) {
    $('#item_group_checkbox_area').empty(); // Kosongkan area checkbox

    if (!frm.doc.department) {
        return; // Jangan tampilkan jika departemen belum dipilih
    }

    frappe.run_serially([
        () => {
            // Ambil semua Item Group yang ada di sistem beserta jumlah itemnya dan akronim
            // Kecualikan "All Item Groups"
            return frappe.db.get_list('Item Group', {
                fields: ['name', 'akronim'],
                filters: {
                    'name': ['!=', 'All Item Groups']
                },
                order_by: 'name asc'
            }).then(item_groups => {
                let html = '';
                const existing_item_groups = (frm.doc.item_groups || []).map(d => d.item_group);

                // Fetch item counts for each item group
                return frappe.call({
                    method: "inaproc.inaproc.doctype.department_item_group.department_item_group.get_item_counts_for_item_groups",
                    args: {
                        item_group_names: item_groups.map(ig => ig.name)
                    },
                    callback: function(r) {
                        if (r.message) {
                            const item_counts = r.message || {};
                            item_groups.forEach(item_group => {
                                const is_checked = existing_item_groups.includes(item_group.name) ? 'checked' : '';
                                const item_count = item_counts[item_group.name] || 0;
                                const akronim_display = item_group.akronim ? ` (${item_group.akronim})` : '';
                                html += `\n                                    <div class="checkbox">\n                                        <label>\n                                            <input type="checkbox" data-item-group="${item_group.name}" ${is_checked}>\n                                            ${item_group.name}${akronim_display} <span class="badge badge-success">${item_count} <small>items</small></span>\n                                        </label>\n                                    </div>\n                                `;
                            });
                            $('#item_group_checkbox_area').html(html);
                        } else if (r.exc) {
                            frappe.msgprint(__("Error fetching item counts: {0}", [r.exc]));
                        }
                    },
                    error: function(r) {
                        frappe.msgprint(__("Server error fetching item counts: {0}", [r.responseJSON.exc]));
                    }
                });
            });
        },
        () => {
            // Tambahkan event listener untuk checkbox
            $('#item_group_checkbox_area input[type="checkbox"]').on('change', function() {
                const item_group_name = $(this).data('item-group');
                if ($(this).is(':checked')) {
                    // Tambahkan ke child table jika dicentang
                    frm.add_child('item_groups', {
                        item_group: item_group_name
                    });
                } else {
                    // Hapus dari child table jika tidak dicentang
                    frm.doc.item_groups = frm.doc.item_groups.filter(d => d.item_group !== item_group_name);
                }
                frm.refresh_field('item_groups'); // Refresh child table (meskipun disembunyikan)
            });
        }
    ]);
}