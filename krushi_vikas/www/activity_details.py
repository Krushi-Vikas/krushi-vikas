import frappe
from krushi_vikas.api import get_activity_detail, get_all_dropdown_options

def get_context(context):
    context.no_cache = 1
    activity_id = frappe.form_dict.get("name") or frappe.form_dict.get("id")
    
    try:
        detail = get_activity_detail(activity_id)
        context.activity = detail.get("activity") or {"name": "ACT-DEFAULT", "activity_name": "General Activity", "project": "General", "project_title": "General Project", "status": "Open"}
        context.tasks = detail.get("tasks") or []
    except Exception as e:
        context.error = str(e)
        context.activity = {"name": "ACT-DEFAULT", "activity_name": "General Activity", "project": "General", "project_title": "General Project", "status": "Open"}
        context.tasks = []
        
    context.options = get_all_dropdown_options()
    return context
