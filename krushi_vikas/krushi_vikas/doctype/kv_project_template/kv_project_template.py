import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class KVProjectTemplate(Document):
    def validate(self):
        activity_names = {row.activity_name for row in (self.get("activities") or [])}
        for row in self.get("tasks") or []:
            if row.activity_name not in activity_names:
                frappe.throw(
                    _(
                        "Checklist step '{0}' is under '{1}', which is not one of "
                        "this template's Activities."
                    ).format(row.subject, row.activity_name)
                )


@frappe.whitelist()
def create_project_from_template(template, project_name, start_date=None,
                                  project_coordinator=None, project_manager=None,
                                  project_director=None):
    """Instantiate a real KV Project (with real Activities and Tasks)
    from a saved template — the same project shape can be reused across
    every village/donor cycle without re-typing the checklist each time.
    """
    tpl = frappe.get_doc("KV Project Template", template)
    start_date = getdate(start_date) if start_date else getdate()
    longest_days = max([a.duration_days or 30 for a in (tpl.get("activities") or [])], default=90)

    project = frappe.get_doc({
        "doctype": "KV Project",
        "project_name": project_name,
        "start_date": start_date,
        "end_date": add_days(start_date, longest_days),
        "project_coordinator": project_coordinator or frappe.session.user,
        "project_manager": project_manager,
        "project_director": project_director,
    })

    # Whoever is actually named on the project is who it should be treated
    # as "raised by" for approval routing — not whoever happens to be
    # clicking Use Template (often an Admin/Director setting it up for
    # someone else, whose own rank would otherwise skip the chain).
    project.flags.raised_by_override = project_manager or project_coordinator or frappe.session.user
    project.insert(ignore_permissions=True)

    tasks_by_activity = {}
    for row in tpl.get("tasks") or []:
        tasks_by_activity.setdefault(row.activity_name, []).append(row)

    for arow in tpl.get("activities") or []:
        activity_end = add_days(start_date, arow.duration_days or 30)
        task_rows = sorted(
            tasks_by_activity.get(arow.activity_name, []),
            key=lambda r: r.sequence or 0,
        )

        activity = frappe.get_doc({
            "doctype": "Activity",
            "activity_name": f"{arow.activity_name} - {project_name}",
            "project": project.name,
            "theme": arow.theme,
            "sub_theme": arow.sub_theme,
            "start_date": start_date,
            "end_date": activity_end,
            "approved_budget": arow.approved_budget,
            "total_expenditure": arow.total_expenditure,
            "target": arow.target,
            "achievement": arow.achievement,
            "tasks": [
                {
                    "subject": trow.subject,
                    "status": "Open",
                    "priority": trow.priority,
                    "exp_start_date": start_date,
                    "exp_end_date": add_days(start_date, trow.offset_days or 7),
                    "description": trow.description,
                }
                for trow in task_rows
            ],
        })
        activity.insert(ignore_permissions=True)

    return project.name
