frappe.ui.form.on('Project', {
    refresh(frm) {
        frm.trigger('calculate_remaining_funds');
        if (!frm.is_new()) {
            frm.add_custom_button(__('View Activities'), function() {
                frappe.set_route('List', 'Activity', { project: frm.doc.name });
            }, __('Project Links'));
            frm.add_custom_button(__('View Tasks'), function() {
                frappe.set_route('List', 'Task', { project: frm.doc.name });
            }, __('Project Links'));
            if (frm.doc.custom_linked_baseline_survey) {
                frm.add_custom_button(__('Baseline Survey'), function() {
                    frappe.set_route('Form', 'Baseline Survey', frm.doc.custom_linked_baseline_survey);
                }, __('Linked Forms'));
            }
            if (frm.doc.custom_linked_field_tracking_form) {
                frm.add_custom_button(__('Field Tracking Form'), function() {
                    frappe.set_route('Form', 'Feedback Survey', frm.doc.custom_linked_field_tracking_form);
                }, __('Linked Forms'));
            }
        }
    },
    custom_budget(frm) {
        frm.trigger('calculate_remaining_funds');
    },
    custom_actual_amount_spent(frm) {
        frm.trigger('calculate_remaining_funds');
    },
    calculate_remaining_funds(frm) {
        let budget = flt(frm.doc.custom_budget || frm.doc.estimated_costing || 0);
        let actual = flt(frm.doc.custom_actual_amount_spent || 0);
        let remaining = budget - actual;
        frm.set_value('custom_remaining_funds', remaining);
    }
});

frappe.ui.form.on('Project Activity', {
    activities_add(frm, cdt, cdn) {
        // Default values for new activity row
    }
});
