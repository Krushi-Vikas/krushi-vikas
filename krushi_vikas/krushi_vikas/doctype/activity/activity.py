import frappe

from frappe.model.document import Document

# The grid uses planning words; Activity uses working ones. Reverse of
# KVProject.STATUS_MAP so a status set directly on the Activity reads
# sensibly back on the project's grid.
GRID_STATUS_MAP = {
	"Draft": "Planned",
	"Open": "Planned",
	"In Progress": "In Progress",
	"Completed": "Completed",
	"Cancelled": "Cancelled",
}


class Activity(Document):

    def validate(self):
        """
        Validate Activity dates and Task dates.
        """

        # -----------------------------------------------------
        # Activity date validation
        # -----------------------------------------------------

        if self.start_date and self.end_date:

            if self.end_date < self.start_date:

                frappe.throw(
                    "End Date cannot be before Start Date for Activity."
                )


        # -----------------------------------------------------
        # Task date validation
        # -----------------------------------------------------

        for row in self.get("tasks") or []:

            if (
                row.exp_start_date
                and row.exp_end_date
                and row.exp_end_date < row.exp_start_date
            ):

                task_name = (
                    row.subject
                    or "Unnamed Task"
                )

                frappe.throw(
                    f"Task '{task_name}': "
                    "End Date cannot be before Start Date."
                )


    def before_save(self):
        """
        Automatically inherit Activity dates for tasks
        when task dates have not been provided.
        """

        for row in self.get("tasks") or []:

            if not row.exp_start_date and self.start_date:

                row.exp_start_date = self.start_date


            if not row.exp_end_date and self.end_date:

                row.exp_end_date = self.end_date

    def on_update(self):
        self.sync_into_project_grid()

    def sync_into_project_grid(self):
        """Mirror this activity into its project's Activities grid.

        KVProject.sync_activities() is the other direction (grid row ->
        Activity) and sets `flags.skip_project_sync` on this doc before
        saving it, so this method knows not to sync straight back and
        loop the two forever.

        Writes go straight to the child table via frappe.db, never through
        a full `project.save()`, so this direction cannot trigger the
        project's own on_update and start a loop of its own.
        """
        if self.flags.get("skip_project_sync"):
            return

        if not self.project or not frappe.db.exists("KV Project", self.project):
            return

        values = {
            "activity_name": self.activity_name,
            "assignee": self.assignee,
            "status": GRID_STATUS_MAP.get(self.status, "Planned"),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
            "input_output": self.input_output,
            "impact": self.impact,
            "linked_activity": self.name,
        }

        existing_row = frappe.db.get_value(
            "KV Project Activity",
            {
                "parent": self.project,
                "parenttype": "KV Project",
                "linked_activity": self.name,
            },
            "name",
        )

        if existing_row:
            frappe.db.set_value(
                "KV Project Activity", existing_row, values, update_modified=False
            )
            return

        # No grid row for this activity yet under this project. Insert one
        # directly as a child record rather than loading and saving the
        # whole project — that would fire KVProject.on_update() and run
        # sync_activities() for no reason, since this row is already correct.
        next_idx = (
            frappe.db.count(
                "KV Project Activity",
                {"parent": self.project, "parenttype": "KV Project"},
            )
            + 1
        )

        row = frappe.get_doc(
            {
                "doctype": "KV Project Activity",
                "parent": self.project,
                "parenttype": "KV Project",
                "parentfield": "activities",
                "idx": next_idx,
                **values,
            }
        )
        row.insert(ignore_permissions=True)
