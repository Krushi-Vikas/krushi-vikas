import frappe
from krushi_vikas.api import get_analytics_summary

def get_context(context):
    context.no_cache = 1
    summary = get_analytics_summary()
    context.kpis = summary.get("kpis")
    
    # Phase Breakdown
    projects = frappe.get_all("Project", fields=["custom_project_phase", "status", "custom_budget", "custom_actual_amount_spent"])
    phase_counts = {}
    for p in projects:
        phase = p.custom_project_phase or "Proposal"
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    context.phase_counts = phase_counts
    
    # Recent Feedback Surveys
    context.recent_feedback = frappe.get_all(
        "Feedback Survey",
        fields=["name", "village", "project", "activity", "date_of_visit", "overall_rating", "total_participants"],
        order_by="creation desc",
        limit=5
    ) if frappe.db.exists("DocType", "Feedback Survey") else []
    
    return context
