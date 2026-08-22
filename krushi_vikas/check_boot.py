import frappe
from frappe.boot import get_bootinfo

def run():
    frappe.set_user("Administrator")
    boot_info = get_bootinfo()

    workspaces = [ws.get("name") for ws in boot_info.get("allowed_workspaces", [])]
    print("ALLOWED WORKSPACES FOR ADMINISTRATOR:")
    print(workspaces)

    print("\nDOES KRUSHI VIKAS EXIST IN DB?", frappe.db.exists("Workspace", "Krushi Vikas"))
