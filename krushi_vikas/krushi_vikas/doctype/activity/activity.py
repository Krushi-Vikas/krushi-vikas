import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class Activity(Document):
    def onload(self):
        """Populates tasks child table if empty when loading existing activity"""
        if not self.get("tasks") and self.name:
            existing_tasks = frappe.get_all("Task", 
                filters={"custom_activity": self.name},
                fields=["name", "subject", "status", "priority", "exp_start_date", "exp_end_date", "description"]
            )
            for t in existing_tasks:
                self.append("tasks", {
                    "subject": t.subject,
                    "status": t.status,
                    "priority": t.priority,
                    "exp_start_date": t.exp_start_date,
                    "exp_end_date": t.exp_end_date,
                    "description": t.description,
                    "linked_task": t.name
                })

    def validate(self):
        if self.start_date and self.end_date and str(self.end_date) < str(self.start_date):
            frappe.throw("End Date cannot be before Start Date for Activity.")
            
        for row in self.get("tasks") or []:
            if row.exp_start_date and row.exp_end_date and str(row.exp_end_date) < str(row.exp_start_date):
                frappe.throw(f"Task '{row.subject}': End Date cannot be before Start Date.")

    def on_update(self):
        """Synchronizes rows in the tasks child table with Task DocType"""
        company = None
        if self.project and frappe.db.exists("Project", self.project):
            company = frappe.db.get_value("Project", self.project, "company")
        if not company:
            company = frappe.defaults.get_user_default("Company") or (frappe.get_all("Company")[0].name if frappe.get_all("Company") else None)

        for row in self.get("tasks") or []:
            if not row.subject:
                continue

            if row.linked_task and frappe.db.exists("Task", row.linked_task):
                # Update existing task
                task_doc = frappe.get_doc("Task", row.linked_task)
                task_doc.subject = row.subject
                task_doc.status = row.status or "Open"
                task_doc.priority = row.priority or "Medium"
                task_doc.exp_start_date = row.exp_start_date or self.start_date
                task_doc.exp_end_date = row.exp_end_date or self.end_date
                task_doc.description = row.description
                if self.project:
                    task_doc.project = self.project
                task_doc.custom_activity = self.name

                if row.depends_on_task and not any(d.task == row.depends_on_task for d in task_doc.get("depends_on") or []):
                    task_doc.append("depends_on", {"task": row.depends_on_task})

                task_doc.save(ignore_permissions=True)
            else:
                # Create new Task
                task_doc = frappe.get_doc({
                    "doctype": "Task",
                    "subject": row.subject,
                    "project": self.project,
                    "custom_activity": self.name,
                    "company": company,
                    "status": row.status or "Open",
                    "priority": row.priority or "Medium",
                    "exp_start_date": row.exp_start_date or self.start_date,
                    "exp_end_date": row.exp_end_date or self.end_date,
                    "description": row.description
                })
                if row.depends_on_task:
                    task_doc.append("depends_on", {"task": row.depends_on_task})
                    
                task_doc.insert(ignore_permissions=True)
                row.linked_task = task_doc.name
                frappe.db.set_value("Activity Task Detail", row.name, "linked_task", task_doc.name, update_modified=False)
