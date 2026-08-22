import frappe

def run():
    frappe.session.user = "Administrator"
    
    user = frappe.get_doc("User", "Administrator")
    print(f"User Home Page: {user.home_page}")
    
    setup_complete = frappe.db.get_single_value("System Settings", "setup_complete")
    print(f"Setup Complete: {setup_complete}")
    
    frappe.local.conf.setup_complete = setup_complete
    
    # Try to set desk route explicitly
    if user.home_page == "setup-wizard":
        user.db_set("home_page", "")
        print("Cleared user.home_page which was setup-wizard")
        
    frappe.db.commit()
    print("Done")
