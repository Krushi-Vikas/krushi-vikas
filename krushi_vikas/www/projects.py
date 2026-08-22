import frappe
from frappe.utils import flt

def get_context(context):
    context.no_cache = 1
    
    # Query standard ERPNext Project DocType
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
            "custom_linked_field_tracking_form"
        ],
        order_by="modified desc"
    )
    
    # Also fallback/merge with KV Project if any records exist
    existing_names = set([p.name for p in projects] + [p.project_name for p in projects])
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
                "linked_field_tracking_form as custom_linked_field_tracking_form"
            ]
        )
        for kv in kv_projects:
            if kv.project_name not in existing_names and kv.name not in existing_names:
                kv.percent_complete = 65
                projects.append(kv)
    
    # Enrich projects with activity count and task count
    for p in projects:
        p_name = p.name
        p_title = p.project_name or p_name
        p.activity_count = frappe.db.count("Activity", {"project": ["in", [p_name, p_title]]}) or 0
        p.task_count = frappe.db.count("Task", {"project": ["in", [p_name, p_title]]}) or 0
        p.remaining_funds = flt(p.custom_budget) - flt(p.custom_actual_amount_spent)
        
    context.projects = projects
    context.users = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "full_name"])
    context.themes = frappe.get_all("Project Theme", fields=["name", "theme_name"]) if frappe.db.exists("DocType", "Project Theme") else []
    return context
