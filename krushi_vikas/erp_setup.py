import frappe
from erpnext.setup.setup_wizard.setup_wizard import setup_complete

def run():
    try:
        args = frappe._dict({
            "country": "India",
            "company_name": "Krushi Vikas Organization",
            "company_abbr": "KVO",
            "currency": "INR",
            "chart_of_accounts": "Standard",
            "timezone": "Asia/Kolkata",
            "first_name": "Administrator",
            "email": "admin@example.com",
            "password": "admin",
            "domains": ["Services"],
            "fy_start_date": "2026-04-01",
            "fy_end_date": "2027-03-31"
        })
        setup_complete(args)
        frappe.db.commit()
        print("ERPNext Setup Wizard completely bypassed and default company created!")
    except Exception as e:
        print("Error:", str(e))
