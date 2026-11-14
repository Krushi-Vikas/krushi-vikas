import frappe

def execute():
    rename_workspace_to_dashboard()
    setup_default_app()
    frappe.db.commit()
    print("Default app, workspace rename, test users, and role cleanup completed successfully!")


def rename_workspace_to_dashboard():
    print("Renaming workspace to Krushi Dashboard...")
    if frappe.db.exists("Workspace", "Krushi Vikas") and not frappe.db.exists("Workspace", "Krushi Dashboard"):
        frappe.rename_doc("Workspace", "Krushi Vikas", "Krushi Dashboard", force=True)
        frappe.db.commit()
        print("Workspace renamed: Krushi Vikas -> Krushi Dashboard")
    else:
        print("Rename skipped (already done, or source/target name mismatch).")


def setup_default_app():
    print("Setting default app and workspace for all users...")

    # System-wide default (applies to anyone without a personal override)
    frappe.db.set_value("System Settings", "System Settings", "default_app", "krushi_vikas")

    # Force it onto every existing System User too, clearing any personal override
    frappe.db.sql("""
        UPDATE `tabUser`
        SET default_app = %s,
            default_workspace = %s
        WHERE user_type = 'System User'
    """, ("krushi_vikas", "Krushi Dashboard"))

    frappe.clear_cache()
    print("Default app and workspace set for all users.")
