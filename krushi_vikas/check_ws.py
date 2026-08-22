import frappe
import json

def run():
    ws = frappe.get_doc("Workspace Settings")
    setup = json.loads(ws.workspace_setup)
    print("WORKSPACE SETUP:")
    for item in setup:
        print(item.get("title"))
    
    # Let's forcibly add Krushi Vikas if not present
    found = False
    for item in setup:
        if item.get("title") == "Krushi Vikas" or item.get("name") == "Krushi Vikas":
            found = True
            break
            
    if not found:
        print("Krushi Vikas is missing from Workspace Settings! Adding it...")
        setup.append({
            "name": "Krushi Vikas",
            "title": "Krushi Vikas",
            "icon": "leaf",
            "type": "Workspace",
            "is_hidden": 0
        })
        ws.workspace_setup = json.dumps(setup)
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        print("Added to Workspace Settings successfully!")
    else:
        print("Krushi Vikas is ALREADY in Workspace Settings.")

