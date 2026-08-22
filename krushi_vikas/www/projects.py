import frappe
from frappe.utils import flt

def get_context(context):
    context.no_cache = 1
    # Fetch all projects with custom fields
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
    
    # Enrich projects with activity count and task count
    for p in projects:
        p.activity_count = frappe.db.count("Activity", {"project": p.name}) or frappe.db.count("Project Activity", {"parent": p.name}) or 0
        p.task_count = frappe.db.count("Task", {"project": p.name}) or 0
        p.remaining_funds = flt(p.custom_budget) - flt(p.custom_actual_amount_spent)
        
    context.projects = projects
    return context
