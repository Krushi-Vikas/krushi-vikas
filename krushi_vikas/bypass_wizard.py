import frappe

def run():
    # Force complete the setup wizard
    frappe.db.set_single_value("System Settings", "setup_complete", 1)
    frappe.db.set_single_value("System Settings", "is_first_startup", 0)
    
    frappe.db.commit()
    print("Setup Wizard Forcefully Bypassed!")
