import frappe

def get_context(context):
    context.no_cache = 1
    context.title = "Feedback Survey Form"
    context.show_sidebar = False
    return context
