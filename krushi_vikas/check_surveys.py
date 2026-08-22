import frappe

def show():
    surveys = frappe.get_all(
        "Feedback Survey",
        fields=[
            "name", "village", "date_of_visit", "field_officer", "activity",
            "respondent_type", "total_participants", "adoption_percentage",
            "overall_rating", "submission_status", "docstatus", "creation", "owner"
        ],
        order_by="creation desc"
    )
    print(f"Total Feedback Surveys stored in database: {len(surveys)}")
    for s in surveys:
        print(f"  • [{s.name}] Village: {s.village} | Date: {s.date_of_visit} | Officer: {s.field_officer} | Rating: {s.overall_rating}/5 | Status: {s.submission_status} | Created: {s.creation}")
