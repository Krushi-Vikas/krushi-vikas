import frappe
import json

def create_workspace():
    if not frappe.db.exists("Workspace", "Krushi Vikas"):
        doc = frappe.new_doc("Workspace")
        doc.name = "Krushi Vikas"
        doc.title = "Krushi Vikas"
        doc.icon = "leaf"
        doc.module = "Krushi Vikas"
        doc.is_standard = 1
        doc.public = 1
    else:
        doc = frappe.get_doc("Workspace", "Krushi Vikas")

    # Add content so it appears
    content = [
        {"type": "header", "data": {"text": "Krushi Vikas", "level": 2}},
        {"type": "shortcut", "data": {"shortcut_name": "KRE", "link_type": "DocType", "link_to": "KRE"}},
        {"type": "shortcut", "data": {"shortcut_name": "Activity Outcome", "link_type": "DocType", "link_to": "Activity Outcome"}}
    ]
    doc.content = json.dumps(content)
    
    try:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Workspace 'Krushi Vikas' updated successfully.")
    except Exception as e:
        print(f"Error creating/updating Workspace: {e}")
