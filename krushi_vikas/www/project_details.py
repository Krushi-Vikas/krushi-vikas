import frappe
from krushi_vikas.api import get_project_detail, get_all_dropdown_options

def get_context(context):
    context.no_cache = 1
    project_id = frappe.form_dict.get("name") or frappe.form_dict.get("id")
    
    try:
        detail = get_project_detail(project_id)
        context.project = detail.get("project") or {"name": "PROJ-DEFAULT", "project_name": "General Project", "status": "Open", "custom_budget": 0, "custom_actual_amount_spent": 0, "custom_remaining_funds": 0}
        context.activities = detail.get("activities") or []
        context.tasks = detail.get("tasks") or []
        context.structured_forms = detail.get("structured_forms") or {"baseline_surveys": [], "feedback_surveys": [], "village_profiles": []}
    except Exception as e:
        context.error = str(e)
        context.project = {"name": "PROJ-DEFAULT", "project_name": "General Project", "status": "Open", "custom_budget": 0, "custom_actual_amount_spent": 0, "custom_remaining_funds": 0}
        context.activities = []
        context.tasks = []
        context.structured_forms = {"baseline_surveys": [], "feedback_surveys": [], "village_profiles": []}
        
    context.options = get_all_dropdown_options()
    return context
