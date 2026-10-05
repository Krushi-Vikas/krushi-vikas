import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today
from frappe import _

class FeedbackSurvey(Document):
    def validate(self):
        self.set_defaults_and_level()
        self.validate_respondent_details()
        self.validate_quantitative_inputs()
        self.validate_qualitative_feedback()

    def set_defaults_and_level(self):
        # Determine survey level if not explicitly provided
        if not self.get("survey_level"):
            if self.get("project") and not self.get("activity") and not self.get("linked_activity"):
                self.survey_level = "Project"
            else:
                self.survey_level = "Activity"

        # If Activity level and linked_activity is provided, populate activity name and project
        if self.survey_level == "Activity":
            if self.get("linked_activity") and frappe.db.exists("Activity", self.linked_activity):
                act = frappe.get_doc("Activity", self.linked_activity)
                if not self.get("activity"):
                    self.activity = act.activity_name or act.name
                if not self.get("project"):
                    self.project = act.project
            elif self.get("activity") and not self.get("linked_activity"):
                # Try finding linked activity by name
                act_name = frappe.db.get_value("Activity", {"activity_name": self.activity}, "name")
                if not act_name and frappe.db.exists("Activity", self.activity):
                    act_name = self.activity
                if act_name:
                    self.linked_activity = act_name
                    if not self.get("project"):
                        self.project = frappe.db.get_value("Activity", act_name, "project")

        # If Project level and no activity text, set a sensible label
        if self.survey_level == "Project":
            if not self.get("activity") or not self.activity.strip():
                self.activity = "Project Level Feedback"

        # Default field_officer to current user if new
        if self.is_new() and not self.get("field_officer"):
            self.field_officer = frappe.session.user

    def validate_respondent_details(self):
        if not self.village or not self.village.strip():
            frappe.throw(_("Village / Location is required."))
        if not self.date_of_visit:
            frappe.throw(_("Date of Visit is required."))
        elif getdate(self.date_of_visit) > getdate(today()):
            frappe.throw(_("Date of Visit ({0}) cannot be in the future.").format(self.date_of_visit))

        if not self.field_officer or not self.field_officer.strip():
            frappe.throw(_("Field Officer / Facilitator is required."))

        # Level-specific requirements
        if self.survey_level == "Project":
            if not self.get("project"):
                frappe.throw(_("Project is required for Project-level Feedback Survey."))
        else:
            if not self.get("activity") or not self.activity.strip():
                frappe.throw(_("Activity / Intervention is required for Activity-level Feedback Survey."))

        if not self.respondent_type or not self.respondent_type.strip():
            frappe.throw(_("Respondent Type is required."))
        if self.respondent_type == "Other" and (not self.respondent_type_other or not self.respondent_type_other.strip()):
            frappe.throw(_("Please specify the respondent type in 'Other (please specify)'."))

    def validate_quantitative_inputs(self):
        if self.total_participants is None:
            frappe.throw(_("Total Participants / Beneficiaries Reached is required."))
        if self.total_participants < 0:
            frappe.throw(_("Total Participants / Beneficiaries Reached must be 0 or greater."))
            
        if self.households_involved is not None:
            if self.households_involved < 0:
                frappe.throw(_("Number of Households Involved cannot be negative."))
            if self.total_participants > 0 and self.households_involved > self.total_participants:
                frappe.throw(_("Number of Households Involved ({0}) cannot exceed Total Participants ({1}).").format(
                    self.households_involved, self.total_participants
                ))

        if self.sessions_conducted is not None and self.sessions_conducted < 0:
            frappe.throw(_("Number of Sessions Conducted cannot be negative."))

        if self.adoption_percentage is None:
            frappe.throw(_("Adoption / Usage percentage is required."))
        elif self.adoption_percentage < 0 or self.adoption_percentage > 100:
            frappe.throw(_("Adoption / Usage percentage must be between 0% and 100%."))

    def validate_qualitative_feedback(self):
        if not self.significant_change or not self.significant_change.strip():
            frappe.throw(_("Most Significant Change / Success Story is required."))
        elif len(self.significant_change.strip()) < 10:
            frappe.throw(_("Most Significant Change / Success Story must be at least 10 characters long."))

        if not self.overall_rating:
            frappe.throw(_("Overall Qualitative Rating is required."))
        else:
            try:
                rating = int(self.overall_rating)
                if rating < 1 or rating > 5:
                    frappe.throw(_("Overall Qualitative Rating must be between 1 and 5."))
            except ValueError:
                frappe.throw(_("Invalid Overall Qualitative Rating. Must be an integer between 1 and 5."))

    def before_submit(self):
        if not self.confirmation_accuracy:
            frappe.throw(_("You must confirm that the information provided is accurate before submitting."))
        self.submission_status = "Submitted"

    def on_cancel(self):
        self.submission_status = "Cancelled"
