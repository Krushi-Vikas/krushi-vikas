frappe.ui.form.on("Feedback Survey", {
    refresh: function(frm) {
        frm.trigger("toggle_survey_level");
        frm.trigger("toggle_respondent_other");

        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("View Survey Web Form"), function() {
                window.open("/feedback-survey", "_blank");
            }, __("Actions"));
        }
    },

    survey_level: function(frm) {
        frm.trigger("toggle_survey_level");
    },

    toggle_survey_level: function(frm) {
        const is_project = frm.doc.survey_level === "Project";
        frm.toggle_reqd("project", is_project);
        frm.toggle_display("project", true);

        frm.toggle_reqd("activity", !is_project);
        frm.toggle_display("activity", !is_project);
        frm.toggle_display("linked_activity", !is_project);

        if (is_project && !frm.doc.activity) {
            frm.set_value("activity", "Project Level Feedback");
        }
    },

    linked_activity: function(frm) {
        if (frm.doc.linked_activity) {
            frappe.db.get_value("Activity", frm.doc.linked_activity, ["activity_name", "project"], function(r) {
                if (r) {
                    if (r.activity_name) frm.set_value("activity", r.activity_name);
                    if (r.project) frm.set_value("project", r.project);
                }
            });
        }
    },

    respondent_type: function(frm) {
        frm.trigger("toggle_respondent_other");
        if (frm.doc.respondent_type !== "Other") {
            frm.set_value("respondent_type_other", "");
        }
    },

    toggle_respondent_other: function(frm) {
        const is_other = frm.doc.respondent_type === "Other";
        frm.toggle_reqd("respondent_type_other", is_other);
        frm.toggle_display("respondent_type_other", is_other);
    },

    adoption_percentage: function(frm) {
        if (frm.doc.adoption_percentage < 0 || frm.doc.adoption_percentage > 100) {
            frappe.msgprint(__("Adoption rate must be between 0% and 100%"));
        }
    }
});
