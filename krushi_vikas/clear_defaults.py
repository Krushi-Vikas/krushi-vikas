import frappe

def run():
    # Clear desktop:home_page default
    frappe.db.delete("DefaultValue", {"defkey": "desktop:home_page"})
    frappe.db.set_default("desktop:home_page", "workspace")
    
    # Just in case there are other defaults pointing to setup-wizard
    for d in frappe.db.get_all("DefaultValue", filters={"defvalue": "setup-wizard"}, fields=["name"]):
        frappe.db.delete("DefaultValue", d.name)
        
    frappe.db.commit()
    print("Cleared setup-wizard defaults")
    
    # Also verify that Administrator user doesn't have a restricted role profile
    user = frappe.get_doc("User", "Administrator")
    print(f"Administrator desk_theme: {user.desk_theme}")
