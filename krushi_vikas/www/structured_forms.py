import frappe

def get_context(context):
    context.no_cache = 1
    context.baseline_count = frappe.db.count("Baseline Survey") if frappe.db.exists("DocType", "Baseline Survey") else 0
    context.feedback_count = frappe.db.count("Feedback Survey") if frappe.db.exists("DocType", "Feedback Survey") else 0
    context.village_count = frappe.db.count("Village Profile") if frappe.db.exists("DocType", "Village Profile") else 0
    
    context.recent_baseline = frappe.get_all(
        "Baseline Survey",
        fields=["name", "farmer_name", "village", "project", "survey_date", "submission_status"],
        order_by="creation desc",
        limit=5
    ) if frappe.db.exists("DocType", "Baseline Survey") else []
    
    context.recent_feedback = frappe.get_all(
        "Feedback Survey",
        fields=["name", "village", "project", "activity", "date_of_visit", "overall_rating", "total_participants"],
        order_by="creation desc",
        limit=5
    ) if frappe.db.exists("DocType", "Feedback Survey") else []
    
    context.recent_villages = frappe.get_all(
        "Village Profile",
        fields=["name", "village_name", "district", "block_taluka", "total_households", "profile_status"],
        order_by="creation desc",
        limit=5
    ) if frappe.db.exists("DocType", "Village Profile") else []
    
    return context
