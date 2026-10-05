import frappe

def execute():
    print("Setting default app and workspace for all users...")

    # Default App — controls post-login Apps Page behavior
    frappe.db.set_value("System Settings", "System Settings", "default_app", "krushi_vikas")

    # Default App + Default Workspace — per-user, overrides any personal override
    frappe.db.sql("""
        UPDATE `tabUser`
        SET default_app = %s,
            default_workspace = %s
        WHERE user_type = 'System User'
    """, ("krushi_vikas", "Krushi Vikas"))

    frappe.db.commit()
    frappe.clear_cache()
    print("Default app and workspace set for all users.")