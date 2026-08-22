frappe.ui.form.on('Concept Note', {
    refresh: function(frm) {
        // Set dynamic status indicator
        if (frm.doc.status === 'Approved') {
            frm.page.set_indicator('Approved', 'green');
            if (frm.doc.project) {
                frm.add_custom_button(__('View Spawned Project'), function() {
                    frappe.set_route('Form', 'Project', frm.doc.project);
                }, __('Project'));
            }
        } else if (frm.doc.status === 'Under Review') {
            frm.page.set_indicator('Under Review', 'orange');
        } else if (frm.doc.status === 'Rejected') {
            frm.page.set_indicator('Rejected', 'red');
        } else {
            frm.page.set_indicator('Draft', 'blue');
        }

        // Action buttons
        if (frm.doc.docstatus === 0 && frm.doc.status !== 'Approved') {
            frm.add_custom_button(__('Mark as Under Review'), function() {
                frm.set_value('status', 'Under Review');
                frm.save();
            }, __('Actions'));

            frm.add_custom_button(__('Approve & Spawn Project'), function() {
                frappe.confirm(
                    __('Are you sure you want to approve this Concept Note? This will create an official Project in the Proposal phase.'),
                    function() {
                        frm.set_value('status', 'Approved');
                        frm.save().then(() => {
                            frm.save('Submit');
                        });
                    }
                );
            }, __('Actions')).addClass('btn-primary');
        }
    }
});
