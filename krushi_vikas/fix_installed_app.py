import frappe

def run():
    frappe.session.user = "Administrator"
    
    # Check what's in Installed Application
    rows = frappe.get_all(
        "Installed Application",
        fields=["name", "app_name", "is_setup_complete"]
    )
    print("Installed Application rows:", rows)
    
    # Set is_setup_complete = 1 for frappe and erpnext
    for row in rows:
        if row.app_name in ("frappe", "erpnext"):
            frappe.db.set_value("Installed Application", row.name, "is_setup_complete", 1)
            print(f"Set {row.app_name} is_setup_complete = 1")
    
    # Also add them if missing
    existing = [r.app_name for r in rows]
    for app in ["frappe", "erpnext"]:
        if app not in existing:
            doc = frappe.new_doc("Installed Application")
            doc.app_name = app
            doc.is_setup_complete = 1
            doc.insert(ignore_permissions=True)
            print(f"Created Installed Application for {app}")
    
    frappe.db.commit()
    
    # Verify
    from frappe import is_setup_complete
    print(f"is_setup_complete() now returns: {is_setup_complete()}")
