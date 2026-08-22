import frappe
import json

def run():
    frappe.session.user = "Administrator"
    
    # Check what workspaces exist
    workspaces = frappe.get_all("Workspace", fields=["name", "title", "is_hidden", "module"])
    print("Workspaces:", workspaces)
    
    # Check Krushi Vikas workspace content
    if frappe.db.exists("Workspace", "Krushi Vikas"):
        ws = frappe.get_doc("Workspace", "Krushi Vikas")
        print(f"\nKrushi Vikas Workspace:")
        print(f"  Title: {ws.title}")
        print(f"  Is Hidden: {ws.is_hidden}")
        print(f"  Cards (links): {len(ws.links) if hasattr(ws, 'links') else 'N/A'}")
        print(f"  Charts: {len(ws.charts) if hasattr(ws, 'charts') else 'N/A'}")
        print(f"  Content: {ws.content[:200] if ws.content else 'EMPTY'}")
    else:
        print("Krushi Vikas workspace DOES NOT EXIST")
        
    # Get the actual sidebar items response
    from frappe.desk.desktop import get_workspace_sidebar_items
    sidebar = get_workspace_sidebar_items()
    print(f"\nSidebar items count: {len(sidebar.get('workspaces', []))}")
    for w in sidebar.get('workspaces', []):
        print(f"  - {w.get('name')} | {w.get('title')}")
