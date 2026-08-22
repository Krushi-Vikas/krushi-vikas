import frappe

def run():
    frappe.session.user = "Administrator"
    
    # Fix for_user field - should be empty string not NULL
    frappe.db.set_value("Workspace", "Krushi Vikas", "for_user", "")
    frappe.db.commit()
    print("Set for_user to empty string")
    
    # Clear all relevant caches
    frappe.cache.delete_value("user_allowed_modules", user="Administrator")
    frappe.cache.delete_value("user_perm_can_read", user="Administrator")
    frappe.clear_cache()
    
    # Verify
    val = frappe.db.get_value("Workspace", "Krushi Vikas", "for_user")
    print(f"for_user is now: '{val}' (type: {type(val)})")
    
    # Test the actual filter
    workspaces = frappe.get_all(
        "Workspace",
        fields=["name"],
        filters={"for_user": "", "is_hidden": 0, "module": ["not in", ["Dummy Module"]]},
    )
    names = [w.name for w in workspaces]
    print(f"Krushi Vikas in filtered list: {'Krushi Vikas' in names}")
    print(f"Total workspaces: {len(workspaces)}")
