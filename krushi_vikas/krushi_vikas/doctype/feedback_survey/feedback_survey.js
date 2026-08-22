frappe.ui.form.on("Feedback Survey", {
    refresh: function(frm) {
        // Toggle other specify
        frm.toggle_reqd("respondent_type_other", frm.doc.respondent_type === "Other");
        frm.toggle_display("respondent_type_other", frm.doc.respondent_type === "Other");
        
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("View Survey Web Form"), function() {
                window.open("/feedback-survey", "_blank");
            }, __("Actions"));
        }
    },
    
    respondent_type: function(frm) {
        frm.toggle_reqd("respondent_type_other", frm.doc.respondent_type === "Other");
        frm.toggle_display("respondent_type_other", frm.doc.respondent_type === "Other");
        if (frm.doc.respondent_type !== "Other") {
            frm.set_value("respondent_type_other", "");
        }
    },
    
    adoption_percentage: function(frm) {
        if (frm.doc.adoption_percentage < 0 || frm.doc.adoption_percentage > 100) {
            frappe.msgprint(__("Adoption rate must be between 0% and 100%"));
        }
    }
});
