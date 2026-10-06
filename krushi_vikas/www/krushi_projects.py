import frappe
from frappe.utils import flt


def get_context(context):
    context.no_cache = 1

    # Query standard ERPNext Project DocType.
    projects = []
    if frappe.db.exists("DocType", "Project"):
        try:
            projects = frappe.get_all(
                "Project",
                fields=[
                    "name",
                    "project_name",
                    "status",
                    "percent_complete",
                    "expected_start_date",
                    "expected_end_date",
                    "custom_project_phase",
                    "custom_thematic_area",
                    "custom_project_coordinator",
                    "custom_project_manager",
                    "custom_budget",
                    "custom_actual_amount_spent",
                    "custom_remaining_funds",
                    "custom_linked_baseline_survey",
                    "custom_linked_field_tracking_form",
                ],
                order_by="modified desc",
                ignore_permissions=True,
            )
        except Exception:
            projects = frappe.get_all(
                "Project",
                fields=["name", "project_name", "status", "percent_complete", "expected_start_date", "expected_end_date"],
                order_by="modified desc",
                ignore_permissions=True,
            )

    # Also merge projects stored in the app's KV Project DocType.
    existing_names = {p.name for p in projects}
    existing_names.update(getattr(p, "project_name", p.name) for p in projects)
    if frappe.db.exists("DocType", "KV Project"):
        kv_projects = frappe.get_all(
            "KV Project",
            fields=[
                "name",
                "project_name",
                "status",
                "project_phase as custom_project_phase",
                "theme as custom_thematic_area",
                "project_coordinator as custom_project_coordinator",
                "project_manager as custom_project_manager",
                "start_date as expected_start_date",
                "end_date as expected_end_date",
                "budget as custom_budget",
                "actual_amount_spent as custom_actual_amount_spent",
                "remaining_funds as custom_remaining_funds",
                "linked_baseline_survey as custom_linked_baseline_survey",
                "linked_field_tracking_form as custom_linked_field_tracking_form",
            ],
            ignore_permissions=True,
        )
        for project in kv_projects:
            if project.project_name not in existing_names and project.name not in existing_names:
                project.percent_complete = 65
                projects.append(project)

    # Enrich project cards with activity and task counts.
    for project in projects:
        project_name = project.name
        project_title = getattr(project, "project_name", None) or project_name
        if frappe.db.exists("DocType", "Activity"):
            project.activity_count = frappe.db.count("Activity", {"project": ["in", [project_name, project_title]]}) or 0
        elif frappe.db.exists("DocType", "Project Activity"):
            project.activity_count = frappe.db.count("Project Activity", {"project": ["in", [project_name, project_title]]}) or 0
        elif frappe.db.exists("DocType", "KV Project Activity"):
            project.activity_count = frappe.db.count("KV Project Activity", {"parent": ["in", [project_name, project_title]]}) or 0
        else:
            project.activity_count = 0
        project.task_count = (
            frappe.db.count("Task", {"project": ["in", [project_name, project_title]]})
            if frappe.db.exists("DocType", "Task")
            else 0
        )
        project.remaining_funds = flt(getattr(project, "custom_budget", 0)) - flt(
            getattr(project, "custom_actual_amount_spent", 0)
        )

    context.projects = projects
    context.users = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "full_name"], ignore_permissions=True)
    context.themes = (
        frappe.get_all("Project Theme", fields=["name", "theme_name"], ignore_permissions=True)
        if frappe.db.exists("DocType", "Project Theme")
        else []
    )
    return context
