import frappe
from frappe.model.document import Document
from frappe.utils import flt

class KVProject(Document):
    def onload(self):
        """Loads and updates linked feedback surveys under this project"""
        if self.name:
            surveys = frappe.get_all("Feedback Survey",
                filters={"project": ["in", [self.name, self.project_name]]},
                fields=["name", "village", "activity", "date_of_visit", "total_participants", "overall_rating"]
            )
            if surveys:
                self.set("feedback_surveys", [])
                for s in surveys:
                    self.append("feedback_surveys", {
                        "feedback_survey": s.name,
                        "village": s.village,
                        "activity": s.activity,
                        "date_of_visit": s.date_of_visit,
                        "total_participants": s.total_participants,
                        "overall_rating": s.overall_rating
                    })

    def validate(self):
        if self.start_date and self.end_date and str(self.end_date) < str(self.start_date):
            frappe.throw("End Date cannot be before Start Date for KV Project.")
            
        # Calculate remaining funds
        b = flt(self.budget)
        spent = flt(self.actual_amount_spent)
        self.remaining_funds = b - spent
        
        # Validate activity dates
        for act in self.get("activities") or []:
            if act.start_date and act.end_date and str(act.end_date) < str(act.start_date):
                frappe.throw(f"Activity '{act.activity_name}': End Date cannot be before Start Date.")
