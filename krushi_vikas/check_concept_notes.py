import frappe

def show():
    notes = frappe.get_all(
        "Concept Note",
        fields=["name", "title", "thematic_area", "status", "estimated_budget", "beneficiary_estimate", "target_geography", "creation"]
    )
    print(f"Total Concept Notes in database: {len(notes)}")
    for n in notes:
        print(f"  • [{n.name}] {n.title} | Theme: {n.thematic_area} | Budget: ₹{n.estimated_budget:,} | Status: {n.status} | Geography: {n.target_geography}")
