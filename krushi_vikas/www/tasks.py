import frappe
from krushi_vikas.api import get_global_tasks, get_all_dropdown_options

def get_context(context):
    context.no_cache = 1
    project_filter = frappe.form_dict.get("project")
    activity_filter = frappe.form_dict.get("activity")
    status_filter = frappe.form_dict.get("status")
    priority_filter = frappe.form_dict.get("priority")
    
    context.tasks = get_global_tasks(
        project=project_filter,
        activity=activity_filter,
        status=status_filter,
        priority=priority_filter
    )
    context.options = get_all_dropdown_options()
    context.selected_project = project_filter or ""
    context.selected_activity = activity_filter or ""
    context.selected_status = status_filter or ""
    context.selected_priority = priority_filter or ""
    return context
