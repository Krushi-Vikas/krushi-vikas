import frappe
from frappe.core.doctype.user.user import get_desk_home
from erpnext.setup.utils import is_setup_complete

def run():
    frappe.session.user = "Administrator"
    user = frappe.get_doc("User", "Administrator")
    print("User role profile:", user.role_profile_name)
    print("User home page:", user.home_page)
    print("System Settings setup_complete:", frappe.db.get_single_value("System Settings", "setup_complete"))
    print("Conf setup_complete:", frappe.conf.get("setup_complete"))
    print("ERPNext is_setup_complete:", is_setup_complete())
    
    # Check default company
    print("Default Company:", frappe.db.get_single_value('Global Defaults', 'default_company'))
    print("Companies:", frappe.db.get_all("Company", pluck="name"))
    
    # Try getting the home route
    print("Desk home:", get_desk_home(user))
