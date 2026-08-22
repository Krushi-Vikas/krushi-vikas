import frappe
from krushi_vikas.api import get_global_activities, get_all_dropdown_options

def get_context(context):
    context.no_cache = 1
    project_filter = frappe.form_dict.get("project")
    status_filter = frappe.form_dict.get("status")
    
    context.activities = get_global_activities(project=project_filter, status=status_filter)
    context.options = get_all_dropdown_options()
    context.selected_project = project_filter or ""
    context.selected_status = status_filter or ""
    return context
