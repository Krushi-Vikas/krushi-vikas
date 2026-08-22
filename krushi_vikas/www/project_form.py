import frappe
from krushi_vikas.api import get_project_form_options

def get_context(context):
    context.no_cache = 1
    context.options = get_project_form_options()
    return context
