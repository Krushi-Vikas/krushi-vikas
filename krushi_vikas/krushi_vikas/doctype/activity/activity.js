frappe.ui.form.on('Activity', {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('View Tasks'), function() {
                frappe.set_route('List', 'Task', { custom_activity: frm.doc.name });
            }, __('Actions'));
            frm.add_custom_button(__('New Task under this Activity'), function() {
                frappe.new_doc('Task', {
                    project: frm.doc.project,
                    custom_activity: frm.doc.name
                });
            }, __('Actions'));
        }
    }
});
