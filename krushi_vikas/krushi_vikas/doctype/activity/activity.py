import frappe

from frappe.model.document import Document


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