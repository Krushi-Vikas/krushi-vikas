frappe.ui.form.on('KRE', {
    refresh: function(frm) {
        // Set dynamic indicator badge
        const pct = frm.doc.achievement_pct || 0;
        let color = 'red';
        if (pct >= 80) {
            color = 'green';
        } else if (pct >= 40) {
            color = 'orange';
        }
        frm.page.set_indicator(`${pct.toFixed(1)}% Achieved (${frm.doc.status || 'Active'})`, color);

        // Add Quick Action to log field outcome
        frm.add_custom_button(__('Log Field Outcome'), function() {
            frappe.new_doc('Activity Outcome', {
                kre: frm.doc.name,
                measurement_date: frappe.datetime.nowdate()
            });
        }, __('Actions')).addClass('btn-primary');
    },

    target_value: function(frm) {
        calculate_achievement(frm);
    },
    current_value: function(frm) {
        calculate_achievement(frm);
    },
    baseline_value: function(frm) {
        calculate_achievement(frm);
    }
});

function calculate_achievement(frm) {
    const target = frm.doc.target_value || 0;
    const baseline = frm.doc.baseline_value || 0;
    const current = frm.doc.current_value || 0;

    const span = target - baseline;
    if (span > 0) {
        const achieved = ((current - baseline) / span) * 100;
        frm.set_value('achievement_pct', Math.max(0, achieved));
    }
}
