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
        const act_reqd = !is_project;

        // Project is optional for Project level surveys
        frm.toggle_reqd("project", false);
        frm.toggle_display("project", true);

        // Activity fields
        frm.toggle_reqd("activity", act_reqd);
        frm.toggle_display("activity", act_reqd);
        frm.toggle_display("linked_activity", act_reqd);

        // All other survey fields are optional for Project level, but mandatory for Activity level
        frm.toggle_reqd("village", act_reqd);
        frm.toggle_reqd("date_of_visit", act_reqd);
        frm.toggle_reqd("field_officer", act_reqd);
        frm.toggle_reqd("respondent_type", act_reqd);
        frm.toggle_reqd("total_participants", act_reqd);
        frm.toggle_reqd("adoption_percentage", act_reqd);
        frm.toggle_reqd("significant_change", act_reqd);
        frm.toggle_reqd("overall_rating", act_reqd);
        frm.toggle_reqd("confirmation_accuracy", act_reqd);

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
