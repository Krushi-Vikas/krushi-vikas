import frappe

def get_context(context):
    context.no_cache = 1
    context.title = "Feedback Survey Form"
    context.show_sidebar = False
    context.survey_level = frappe.form_dict.get("survey_level") or "Activity"
    context.project = frappe.form_dict.get("project") or ""
    context.activity = frappe.form_dict.get("activity") or ""
    return context
