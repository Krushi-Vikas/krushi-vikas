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
        from krushi_vikas.api import enforce_project_least_privilege
        enforce_project_least_privilege(self)

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

        self.set_journey_stage()

    def set_journey_stage(self):
        """Steps 06-10 of the operational roadmap.

        Derived rather than entered: the stage is a reading of the project's
        own state, so it cannot drift from reality the way a hand-set field
        does. Recomputed on every save.
        """
        if self.status in ("Completed", "Cancelled"):
            self.journey_stage = "Closed"
            return

        # 07 - created, but leadership has not signed it off. Nothing
        # downstream counts until this clears.
        if self.workflow_state and self.workflow_state != "Approved":
            self.journey_stage = "07 Internal Approval"
            return

        if not self.is_new() and self.has_reverse_reporting():
            self.journey_stage = "10 Reverse Reporting"
            return

        if self.status in ("In Progress", "Deployed"):
            self.journey_stage = "09 Execution"
            return

        # Approved but idle, or already carrying activities: the outstanding
        # work is allocation. The stage names what happens next, so it never
        # moves backwards as the project progresses.
        if self.workflow_state == "Approved" or self.get("activities") or (
            not self.is_new() and self.has_activities()
        ):
            self.journey_stage = "08 Task Assignment"
            return

        self.journey_stage = "06 Project Created"

    def has_activities(self):
        return bool(frappe.db.exists("Activity", {"project": self.name}))

    def has_reverse_reporting(self):
        """Step 10: evidence has started flowing back from the field.

        Both reverse-reporting doctypes carry the project directly, so this
        needs no join through Activity.
        """
        for doctype in ("Activity Outcome", "Feedback Survey"):
            if frappe.db.exists(doctype, {"project": self.name}):
                return True

        return False
