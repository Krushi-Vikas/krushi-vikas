import frappe
from erpnext.setup.setup_wizard.install_fixtures import install

def run():
    print("Installing ERPNext setup fixtures...")
    install("India")
    frappe.db.commit()
    print("Fixtures installed successfully!")
