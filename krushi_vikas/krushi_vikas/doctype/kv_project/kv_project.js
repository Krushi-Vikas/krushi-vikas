frappe.ui.form.on('KV Project', {
    refresh(frm) {
        frm.trigger('calc_remaining');
        if (!frm.is_new()) {
            frm.fields_dict.activities.grid.add_custom_button(__('New Task'), () => {
                const rows = frm.fields_dict.activities.grid.get_selected_children();
                if (!rows.length) return frappe.msgprint(__('Select an activity row first.'));
                const row = rows[0];
                if (!row.linked_activity) return frappe.msgprint(__('Save the project first.'));
                frappe.new_doc('Task', {
                    custom_activity: row.linked_activity,
                    custom_activity_owner: row.assignee,
                    status: 'Open'
                });
            });
            if (frm.doc.linked_baseline_survey) {
                frm.add_custom_button(__('Baseline Survey'), function() {
                    frappe.set_route('Form', 'Baseline Survey', frm.doc.linked_baseline_survey);
                }, __('Linked Forms'));
            }
            if (frm.doc.linked_field_tracking_form) {
                frm.add_custom_button(__('Field Tracking Form'), function() {
                    frappe.set_route('Form', 'Feedback Survey', frm.doc.linked_field_tracking_form);
                }, __('Linked Forms'));
            }
        }
    },
    budget(frm) {
        frm.trigger('calc_remaining');
    },
    actual_amount_spent(frm) {
        frm.trigger('calc_remaining');
    },
    calc_remaining(frm) {
        let b = flt(frm.doc.budget || 0);
        let s = flt(frm.doc.actual_amount_spent || 0);
        frm.set_value('remaining_funds', b - s);
    }
});
