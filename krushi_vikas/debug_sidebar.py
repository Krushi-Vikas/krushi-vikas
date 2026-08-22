import frappe

def run():
    frappe.session.user = "Administrator"
    
    # Directly simulate what get_workspace_sidebar_items does
    blocked_modules = frappe.get_cached_doc("User", frappe.session.user).get_blocked_modules()
    blocked_modules.append("Dummy Module")
    print("blocked_modules:", blocked_modules)
    
    allowed_domains = [None] + frappe.get_active_domains()
    print("allowed_domains:", allowed_domains)
    
    filters = {
        "restrict_to_domain": ["in", allowed_domains],
        "module": ["not in", blocked_modules],
    }
    
    has_access = "Workspace Manager" in frappe.get_roles()
    if not has_access:
        filters["for_user"] = ""
        filters["is_hidden"] = 0
    
    print("filters:", filters)
    
    workspaces = frappe.get_all(
        "Workspace",
        fields=["name", "title", "for_user", "module", "is_hidden", "public", "icon", "indicator_color", "parent_page as parent"],
        filters=filters,
        order_by="title asc",
    )
    print(f"workspaces found: {len(workspaces)}")
    for w in workspaces:
        print(f"  {w.name} | module={w.module} | for_user={w.for_user} | is_hidden={w.is_hidden}")
