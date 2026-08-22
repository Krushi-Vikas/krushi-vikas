import frappe
import json

def run():
    frappe.session.user = "Administrator"
    
    ws = frappe.get_doc("Workspace", "Krushi Vikas")
    
    # Set roles so Administrator can see it
    ws.roles = []
    ws.append("roles", {"role": "System Manager"})
    ws.append("roles", {"role": "Administrator"})
    
    # Build proper content with shortcut cards + links
    ws.content = json.dumps([
        {
            "type": "header",
            "data": {"text": "<b>Krushi Vikas</b>", "level": 4, "col": 12}
        },
        {
            "type": "shortcut",
            "data": {
                "shortcut_name": "KRE",
                "link_type": "DocType",
                "link_to": "KRE",
                "col": 4
            }
        },
        {
            "type": "shortcut",
            "data": {
                "shortcut_name": "Activity Outcome",
                "link_type": "DocType",
                "link_to": "Activity Outcome",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Krushi Vikas",
                "col": 4
            }
        }
    ])
    
    # Add link items for the card
    ws.links = []
    for label, doctype in [
        ("KRE", "KRE"),
        ("Activity Outcome", "Activity Outcome"),
        ("Project", "Project"),
        ("Task", "Task"),
    ]:
        ws.append("links", {
            "label": label,
            "type": "Link",
            "link_type": "DocType",
            "link_to": doctype,
            "onboard": 1,
        })
    
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workspace saved with roles and links")
    
    # Verify sidebar now works
    from frappe.desk.desktop import get_workspace_sidebar_items
    sidebar = get_workspace_sidebar_items()
    print(f"Sidebar items count: {len(sidebar.get('workspaces', []))}")
    for w in sidebar.get('workspaces', []):
        if 'Krushi' in w.get('name',''):
            print(f"  FOUND: {w}")
