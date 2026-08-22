frappe.ui.form.on('Project Goal', {
    refresh: function(frm) {
        const ach = frm.doc.actual_completion_pct || 0;
        let color = ach >= 75 ? 'green' : (ach >= 40 ? 'orange' : 'blue');
        frm.page.set_indicator(`${ach.toFixed(1)}% Goal Achieved`, color);

        frm.add_custom_button(__('Recalculate Progress'), function() {
            frm.save();
        }, __('Actions'));
    }
});

frappe.ui.form.on('Project Objective', {
    weightage: function(frm, cdt, cdn) {
        validate_weightage_sum(frm);
    }
});

function validate_weightage_sum(frm) {
    let total = 0;
    (frm.doc.objectives || []).forEach(row => {
        total += (row.weightage || 0);
    });
    if (total > 100) {
        frappe.msgprint({
            title: __('Weightage Alert'),
            indicator: 'orange',
            message: __('Total objectives weightage exceeds 100% (Current total: {0}%)', [total])
        });
    }
}
