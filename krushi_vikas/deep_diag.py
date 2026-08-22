import frappe

def run():
    frappe.session.user = "Administrator"
    from frappe.boot import get_bootinfo
    bootinfo = get_bootinfo()
    print(f"home_page: {bootinfo.get('home_page')}")
    print(f"setup_complete: {bootinfo.get('setup_complete')}")
    print(f"type of setup_complete: {type(bootinfo.get('setup_complete'))}")
