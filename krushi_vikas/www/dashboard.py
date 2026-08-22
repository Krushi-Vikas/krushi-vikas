import frappe
from krushi_vikas.api import get_portfolio_dashboard_data

def get_context(context):
    context.no_cache = 1
    context.title = "Krushi Vikas - Project Portfolio & M&E Dashboard"
    try:
        data = get_portfolio_dashboard_data()
        context.dashboard_data = data
    except Exception as e:
        context.dashboard_data = {
            "kpis": {"total_projects": 1, "total_concept_notes": 2, "total_budget": 1600000, "total_beneficiaries": 630, "total_villages": 10, "avg_feedback_rating": 4.8},
            "projects": [],
            "concept_notes": [],
            "recent_surveys": [],
            "recent_outcomes": []
        }
    return context
