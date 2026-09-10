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

    # The grid uses planning words; Activity uses working ones.
    STATUS_MAP = {"Planned": "Open", "In Progress": "In Progress",
                  "Completed": "Completed", "Cancelled": "Cancelled"}

    def on_update(self):
        self.sync_activities()

    def sync_activities(self):
        """Turn each row of the Activities grid into a real Activity.

        Without this the grid is a scratchpad: the rows look like activities
        but nothing can link to them, so tasks have nothing to attach to.
        Each row remembers the Activity it created, so saving again updates
        rather than duplicates.
        """
        for row in self.get("activities") or []:
            if not row.activity_name:
                continue

            values = {
                "activity_name": row.activity_name,
                "project": self.name,
                "theme": self.theme,
                "assignee": row.assignee,
                "status": self.STATUS_MAP.get(row.status, "Open"),
                "start_date": row.start_date or self.start_date,
                "end_date": row.end_date or self.end_date,
                "description": row.description,
                "input_output": row.input_output,
                "impact": row.impact,
            }

            if row.linked_activity and frappe.db.exists("Activity", row.linked_activity):
                activity = frappe.get_doc("Activity", row.linked_activity)
                activity.update(values)
                activity.save(ignore_permissions=True)
                continue

            # An activity of the same name under this project is the same
            # activity — adopt it rather than making a second one.
            existing = frappe.db.get_value(
                "Activity",
                {"project": self.name, "activity_name": row.activity_name},
                "name",
            )

            if existing:
                activity = frappe.get_doc("Activity", existing)
                activity.update(values)
                activity.save(ignore_permissions=True)
            else:
                activity = frappe.get_doc(dict(doctype="Activity", **values))
                activity.insert(ignore_permissions=True)

            row.db_set("linked_activity", activity.name, update_modified=False)

    def after_insert(self):
        """Route the project to whoever is above the person who raised it."""
        from krushi_vikas.approvals import start_approval

        if self.approval_status and self.approval_status != "Draft":
            return

        start_approval(self, raised_by=self.owner)

    def refresh_journey_stage(self):
        """Recompute and persist the stage outside a save.

        validate() runs before the approval chain moves the document, so the
        stored stage would otherwise lag a step behind every approval.
        """
        self.set_journey_stage()
        self.db_set("journey_stage", self.journey_stage, update_modified=False)

    def set_journey_stage(self):
        """Steps 06-10 of the operational roadmap.

        Derived rather than entered: the stage is a reading of the project's
        own state, so it cannot drift from reality the way a hand-set field
        does. Recomputed on every save.
        """
        if self.status in ("Completed", "Cancelled"):
            self.journey_stage = "Closed"
            return

        # Created, but not signed off. Nothing downstream counts until the
        # approval chain clears.
        if self.approval_status in ("Pending Approval", "Rejected"):
            self.journey_stage = "Awaiting Approval"
            return

        if not self.is_new() and self.has_reverse_reporting():
            self.journey_stage = "Reverse Reporting"
            return

        if self.status in ("In Progress", "Deployed"):
            self.journey_stage = "Execution"
            return

        # Approved but idle, or already carrying activities: the outstanding
        # work is allocation. The stage names what happens next, so it never
        # moves backwards as the project progresses.
        if self.approval_status == "Approved" or self.get("activities") or (
            not self.is_new() and self.has_activities()
        ):
            self.journey_stage = "Task Assignment"
            return

        self.journey_stage = "Project Created"

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
