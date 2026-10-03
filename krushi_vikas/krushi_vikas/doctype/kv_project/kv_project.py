import frappe
from frappe.model.document import Document
from frappe.utils import flt

def recompute_themes_covered_db(project_name):
    """Same rollup as KVProject.recompute_themes_covered(), for callers that
    write the Activities grid straight to the database (Activity.on_update's
    sync_into_project_grid) without loading and saving the parent doc.
    """
    rows = frappe.get_all(
        "KV Project Activity",
        filters={"parent": project_name, "parenttype": "KV Project"},
        fields=["theme"],
        distinct=True,
    )
    themes = sorted({r.theme for r in rows if r.theme})
    frappe.db.set_value(
        "KV Project", project_name, "themes_covered", ", ".join(themes), update_modified=False
    )


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

        self.refresh_baseline_coverage()
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
        self.recompute_themes_covered()

    def refresh_baseline_coverage(self):
        villages = self.get("project_villages") or []
        seen_profiles = set()
        warnings = []

        if not villages:
            warnings.append("No Village Profile is linked, so household baseline coverage cannot be monitored.")

        for row in villages:
            if row.village_profile in seen_profiles:
                frappe.throw("A Village Profile can only be linked to a project once.")
            seen_profiles.add(row.village_profile)

            profile = frappe.get_doc("Village Profile", row.village_profile)
            row.village_name = profile.village_name
            row.district = profile.district
            row.total_households = profile.total_households or 0
            row.submitted_baseline_surveys = frappe.db.count(
                "Baseline Survey", {"village_profile": profile.name, "docstatus": 1}
            )
            row.baseline_coverage_percent = (
                (row.submitted_baseline_surveys / row.total_households) * 100
                if row.total_households else 0
            )

            if not row.submitted_baseline_surveys:
                warnings.append("{0} has no submitted household baseline surveys.".format(profile.village_name))

        if warnings:
            frappe.msgprint("<br>".join(warnings), title="Baseline Evidence", indicator="orange")

    def recompute_themes_covered(self):
        """A project spans whatever Themes its Activities actually carry —
        never just the one 'default' Link field. Recomputed from the grid
        already on this doc, so it needs no extra query here.
        """
        themes = sorted({row.theme for row in (self.get("activities") or []) if row.theme})
        self.themes_covered = ", ".join(themes)

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
                "theme": row.theme,
                "sub_theme": row.sub_theme,
                "assignee": row.assignee,
                "status": self.STATUS_MAP.get(row.status, "Open"),
                "start_date": row.start_date or self.start_date,
                "end_date": row.end_date or self.end_date,
                "approved_budget": row.approved_budget,
                "total_expenditure": row.total_expenditure,
                "target": row.target,
                "achievement": row.achievement,
            }

            if row.linked_activity and frappe.db.exists("Activity", row.linked_activity):
                activity = frappe.get_doc("Activity", row.linked_activity)
                activity.update(values)
                # Activity.on_update() mirrors changes back into this same
                # grid; this flag tells it that this save originated here,
                # so it does not turn around and re-sync into us.
                activity.flags.skip_project_sync = True
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
                activity.flags.skip_project_sync = True
                activity.save(ignore_permissions=True)
            else:
                activity = frappe.get_doc(dict(doctype="Activity", **values))
                activity.flags.skip_project_sync = True
                activity.insert(ignore_permissions=True)

            row.db_set("linked_activity", activity.name, update_modified=False)

    def after_insert(self):
        """Route the project to whoever is above the person who raised it.

        Normally that's just whoever clicked Save (self.owner). Creating a
        project from a template is the exception: an Administrator/Director
        commonly builds it on behalf of the Manager or Coordinator actually
        named on it, and routing by the literal owner would let their rank
        skip the whole chain — see kv_project_template.py, which sets
        flags.raised_by_override to the person the project is really for.
        """
        from krushi_vikas.approvals import start_approval

        if self.approval_status and self.approval_status != "Draft":
            return

        raised_by = self.flags.get("raised_by_override") or self.owner
        start_approval(self, raised_by=raised_by)

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
