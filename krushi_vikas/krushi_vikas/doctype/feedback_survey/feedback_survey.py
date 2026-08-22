import frappe
from frappe.model.document import Document
from frappe import _

class FeedbackSurvey(Document):
    def validate(self):
        self.validate_respondent_details()
        self.validate_quantitative_inputs()
        self.validate_qualitative_feedback()
        
    def validate_respondent_details(self):
        if not self.village:
            frappe.throw(_("Village / Location is required."))
        if not self.date_of_visit:
            frappe.throw(_("Date of Visit is required."))
        if not self.field_officer:
            frappe.throw(_("Field Officer / Facilitator is required."))
        if not self.activity:
            frappe.throw(_("Activity / Intervention is required."))
        if not self.respondent_type:
            frappe.throw(_("Respondent Type is required."))
        if self.respondent_type == "Other" and not self.respondent_type_other:
            frappe.throw(_("Please specify the respondent type in 'Other (please specify)'."))

    def validate_quantitative_inputs(self):
        if self.total_participants is None or self.total_participants < 0:
            frappe.throw(_("Total Participants / Beneficiaries Reached must be 0 or greater."))
        if self.households_involved is not None and self.households_involved < 0:
            frappe.throw(_("Number of Households Involved cannot be negative."))
        if self.sessions_conducted is not None and self.sessions_conducted < 0:
            frappe.throw(_("Number of Sessions Conducted cannot be negative."))
        if self.adoption_percentage is not None:
            if self.adoption_percentage < 0 or self.adoption_percentage > 100:
                frappe.throw(_("Adoption / Usage percentage must be between 0% and 100%."))

    def validate_qualitative_feedback(self):
        if not self.significant_change:
            frappe.throw(_("Most Significant Change / Success Story is required."))
        if self.overall_rating:
            try:
                rating = int(self.overall_rating)
                if rating < 1 or rating > 5:
                    frappe.throw(_("Overall Qualitative Rating must be between 1 and 5."))
            except ValueError:
                frappe.throw(_("Invalid Overall Qualitative Rating."))

    def before_submit(self):
        if not self.confirmation_accuracy:
            frappe.throw(_("You must confirm that the information provided is accurate before submitting."))
        self.submission_status = "Submitted"

    def on_cancel(self):
        self.submission_status = "Cancelled"
