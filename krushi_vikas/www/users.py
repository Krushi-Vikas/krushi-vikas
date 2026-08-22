import frappe

def get_context(context):
    context.no_cache = 1
    users = frappe.get_all(
        "User",
        filters={"enabled": 1, "name": ["not in", ["Guest"]]},
        fields=["name", "full_name", "email", "user_type", "last_active", "creation"],
        order_by="creation desc"
    )
    
    # Enrich users with their roles
    for u in users:
        roles = frappe.get_roles(u.name)
        # Filter out standard system roles for clean display
        app_roles = [r for r in roles if r in ["System Manager", "Administrator", "Field Officer", "Project Manager", "Project Coordinator", "Reviewer"]]
        u.app_roles = app_roles or ["User"]
        
    context.users = users
    return context
