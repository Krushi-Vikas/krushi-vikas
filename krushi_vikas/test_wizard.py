import frappe

def run():
    print("Setup Complete in site_config:", frappe.conf.get("setup_complete"))
    print("Setup Complete in System Settings:", frappe.db.get_single_value("System Settings", "setup_complete"))
    
    # Check what route the User is getting
    user = frappe.get_doc("User", "Administrator")
    print("User Home Page:", user.home_page)
