import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
import json

def run():
    setup_roles()
    setup_custom_fields()
    setup_workspace()
    setup_workflows()
    seed_sample_data()
    frappe.db.commit()
    print("All site configurations, workflows, and demo seed data completed successfully!")

def setup_roles():
    print("Setting up Roles...")
    roles = [
        "Field Officer",
        "Project Coordinator",
        "Project Manager",
        "Project Director",
        "CEO"
    ]
    for r in roles:
        if not frappe.db.exists("Role", r):
            doc = frappe.new_doc("Role")
            doc.role_name = r
            doc.insert(ignore_permissions=True)
            print(f"Created Role: {r}")

def setup_custom_fields():
    print("Setting up Custom Fields...")
    custom_fields = {
        "Task": [
            {
                "fieldname": "custom_project_phase",
                "label": "Project Phase",
                "fieldtype": "Select",
                "options": "Survey\nProposal\nExecution\nResults\nFeedback\nFuture",
                "insert_after": "project",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_theme",
                "label": "Theme / Sub-theme",
                "fieldtype": "Link",
                "options": "Project Theme",
                "insert_after": "custom_project_phase",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_kre",
                "label": "Linked KRE",
                "fieldtype": "Link",
                "options": "KRE",
                "insert_after": "custom_theme",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_is_milestone_activity",
                "label": "Is Milestone Activity",
                "fieldtype": "Check",
                "insert_after": "custom_kre",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_activity_owner",
                "label": "Activity Owner (Officer)",
                "fieldtype": "Link",
                "options": "Employee",
                "insert_after": "custom_is_milestone_activity",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_section_budget",
                "label": "Activity Budget & Expenditure",
                "fieldtype": "Section Break",
                "insert_after": "custom_activity_owner",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_planned_budget",
                "label": "Planned Budget (INR)",
                "fieldtype": "Currency",
                "insert_after": "custom_section_budget",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_planned_pct",
                "label": "Planned %",
                "fieldtype": "Percent",
                "insert_after": "custom_planned_budget",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_col_budget_1",
                "fieldtype": "Column Break",
                "insert_after": "custom_planned_pct",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_actual_expenditure",
                "label": "Actual Expenditure (INR)",
                "fieldtype": "Currency",
                "insert_after": "custom_col_budget_1",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_actual_pct",
                "label": "Actual %",
                "fieldtype": "Percent",
                "insert_after": "custom_actual_expenditure",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_variance",
                "label": "Variance (INR)",
                "fieldtype": "Currency",
                "insert_after": "custom_actual_pct",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_beneficiary_count",
                "label": "Beneficiary Count",
                "fieldtype": "Int",
                "insert_after": "custom_variance",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_strategy",
                "label": "Implementation Strategy",
                "fieldtype": "Small Text",
                "insert_after": "custom_beneficiary_count",
                "module": "Krushi Vikas"
            }
        ],
        "Project": [
            {
                "fieldname": "custom_project_phase",
                "label": "Project Phase",
                "fieldtype": "Select",
                "options": "Survey\nProposal\nExecution\nResults\nFeedback\nFuture",
                "insert_after": "project_name",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_thematic_area",
                "label": "Thematic Area",
                "fieldtype": "Link",
                "options": "Project Theme",
                "insert_after": "custom_project_phase",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_concept_note",
                "label": "Originating Concept Note",
                "fieldtype": "Link",
                "options": "Concept Note",
                "insert_after": "custom_thematic_area",
                "module": "Krushi Vikas"
            }
        ]
    }
    create_custom_fields(custom_fields, update=True)
    print("Custom Fields updated!")

def setup_workspace():
    print("Ensuring Workspace...")
    if not frappe.db.exists("Workspace", "Krushi Vikas"):
        ws = frappe.new_doc("Workspace")
        ws.name = "Krushi Vikas"
        ws.label = "Krushi Vikas"
        ws.title = "Krushi Vikas"
        ws.icon = "plant"
        ws.module = "Krushi Vikas"
        ws.is_standard = 0
        ws.public = 1
        ws.content = json_workspace_content()
        ws.insert(ignore_permissions=True)
        print("Workspace 'Krushi Vikas' created!")

def setup_workflows():
    print("Setting up Workflow States & Actions...")
    states = [
        ("Draft", ""),
        ("PC Review", "Warning"),
        ("PM Approval", "Info"),
        ("Director Signoff", "Primary"),
        ("Approved", "Success"),
        ("Rejected", "Danger"),
        ("Under Review", "Warning")
    ]
    for state_name, style in states:
        if not frappe.db.exists("Workflow State", state_name):
            doc = frappe.new_doc("Workflow State")
            doc.workflow_state_name = state_name
            doc.style = style
            doc.insert(ignore_permissions=True)

    actions = ["Submit", "Review", "Approve", "Reject", "Send Back", "Submit for Review"]
    for action_name in actions:
        if not frappe.db.exists("Workflow Action Master", action_name):
            doc = frappe.new_doc("Workflow Action Master")
            doc.workflow_action_name = action_name
            doc.insert(ignore_permissions=True)

    # Activity Outcome Workflow
    if not frappe.db.exists("Workflow", "Activity Outcome Approval"):
        wf = frappe.new_doc("Workflow")
        wf.workflow_name = "Activity Outcome Approval"
        wf.document_type = "Activity Outcome"
        wf.is_active = 1
        wf.workflow_state_field = "workflow_state"
        wf.send_email_alert = 0
        
        wf.set("states", [
            {"state": "Draft", "doc_status": "0", "allow_edit": "Field Officer"},
            {"state": "PC Review", "doc_status": "0", "allow_edit": "Project Coordinator"},
            {"state": "PM Approval", "doc_status": "1", "allow_edit": "Project Manager"},
            {"state": "Director Signoff", "doc_status": "1", "allow_edit": "Project Director"},
            {"state": "Approved", "doc_status": "1", "allow_edit": "Project Manager"},
            {"state": "Rejected", "doc_status": "0", "allow_edit": "Field Officer"},
        ])
        
        wf.set("transitions", [
            {"state": "Draft", "action": "Submit", "next_state": "PC Review", "allowed": "Field Officer"},
            {"state": "PC Review", "action": "Approve", "next_state": "PM Approval", "allowed": "Project Coordinator"},
            {"state": "PC Review", "action": "Reject", "next_state": "Rejected", "allowed": "Project Coordinator"},
            {"state": "Rejected", "action": "Submit", "next_state": "PC Review", "allowed": "Field Officer"},
            {"state": "PM Approval", "action": "Approve", "next_state": "Approved", "allowed": "Project Manager", "condition": "doc.is_milestone_activity == 0"},
            {"state": "PM Approval", "action": "Approve", "next_state": "Director Signoff", "allowed": "Project Manager", "condition": "doc.is_milestone_activity == 1"},
            {"state": "Director Signoff", "action": "Approve", "next_state": "Approved", "allowed": "Project Director"}
        ])
        wf.insert(ignore_permissions=True)
        print("Workflow 'Activity Outcome Approval' created!")

def json_workspace_content():
    content = [
        {"type": "header", "data": {"text": "Krushi Vikas PM System", "level": 3}},
        {"type": "card", "data": {"card_name": "Core Project Tracking", "links": [
            {"type": "Link", "link_type": "DocType", "link_to": "Project", "label": "Projects"},
            {"type": "Link", "link_type": "DocType", "link_to": "Task", "label": "Activities / Tasks"},
            {"type": "Link", "link_type": "DocType", "link_to": "Project Goal", "label": "Project Goals & Objectives"},
            {"type": "Link", "link_type": "DocType", "link_to": "Project Theme", "label": "Themes & Sub-themes"}
        ]}},
        {"type": "card", "data": {"card_name": "Results & KRE (OKRs)", "links": [
            {"type": "Link", "link_type": "DocType", "link_to": "KRE", "label": "Key Result Expectations (KRE)"},
            {"type": "Link", "link_type": "DocType", "link_to": "Activity Outcome", "label": "Activity Outcomes (Field Data)"},
            {"type": "Link", "link_type": "DocType", "link_to": "User Target", "label": "User Targets & Achievements"}
        ]}},
        {"type": "card", "data": {"card_name": "Surveys & Appraisals", "links": [
            {"type": "Link", "link_type": "DocType", "link_to": "Feedback Survey", "label": "Feedback Surveys"},
            {"type": "Link", "link_type": "DocType", "link_to": "Concept Note", "label": "Concept Notes"},
            {"type": "Link", "link_type": "DocType", "link_to": "Survey Template", "label": "Survey Templates"},
            {"type": "Link", "link_type": "DocType", "link_to": "Survey Response", "label": "Survey Responses (RRA / Baseline / Endline)"}
        ]}},
        {"type": "card", "data": {"card_name": "Field Operations & Continuous Learning", "links": [
            {"type": "Link", "link_type": "DocType", "link_to": "Beneficiary", "label": "Beneficiaries (Farmers / Plots)"},
            {"type": "Link", "link_type": "DocType", "link_to": "Input Distribution", "label": "Input Distributions"},
            {"type": "Link", "link_type": "DocType", "link_to": "Improvement Suggestion", "label": "Phase 6 Improvement Archive"}
        ]}}
    ]
    return json.dumps(content)

def seed_sample_data():
    """Seeds realistic demonstration data matching the UI designs"""
    print("Seeding demo data...")
    company = frappe.db.get_value("Company", {"is_group": 0}, "name")
    if not company:
        c = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Krushi Vikas Organization",
            "abbr": "KVO",
            "default_currency": "INR",
            "country": "India"
        }).insert(ignore_permissions=True)
        company = c.name

    # 1. Project Themes
    themes = [
        ("Watershed Management", "WM", 1, None),
        ("Contour Trenching", "WM-CT", 0, "Watershed Management"),
        ("Farm Ponds & Check Dams", "WM-FP", 0, "Watershed Management"),
        ("Sustainable Agriculture", "SA", 1, None),
        ("Micro-Irrigation (Drip/Sprinkler)", "SA-MI", 0, "Sustainable Agriculture"),
        ("Kitchen Gardens & Nutrition", "SA-KG", 0, "Sustainable Agriculture"),
        ("Organic Bio-Fertilizer", "SA-OF", 0, "Sustainable Agriculture"),
        ("Livelihood & Women SHGs", "LW", 1, None)
    ]
    for t_name, t_code, is_grp, parent in themes:
        if not frappe.db.exists("Project Theme", t_name):
            frappe.get_doc({
                "doctype": "Project Theme",
                "theme_name": t_name,
                "theme_code": t_code,
                "is_group": is_grp,
                "parent_project_theme": parent
            }).insert(ignore_permissions=True)

    # 2. Concept Notes
    if not frappe.db.exists("Concept Note", {"title": "Kalyanpur Integrated Watershed Development"}):
        cn1 = frappe.get_doc({
            "doctype": "Concept Note",
            "title": "Kalyanpur Integrated Watershed Development",
            "thematic_area": "Watershed Management",
            "status": "Approved",
            "target_geography": "Kalyanpur Block, Vidarbha Region",
            "beneficiary_estimate": 450,
            "estimated_budget": 1250000.0,
            "duration_months": 12,
            "rationale": "<p>Address critical groundwater depletion and enhance agricultural productivity across 450 smallholder farm families through integrated watershed structures.</p>",
            "raised_by": "Administrator"
        }).insert(ignore_permissions=True)
        cn1.submit()

    if not frappe.db.exists("Concept Note", {"title": "Village Nutrition & Kitchen Garden Initiative"}):
        cn2 = frappe.get_doc({
            "doctype": "Concept Note",
            "title": "Village Nutrition & Kitchen Garden Initiative",
            "thematic_area": "Sustainable Agriculture",
            "status": "Under Review",
            "target_geography": "Rampur & Sonapur Villages",
            "beneficiary_estimate": 180,
            "estimated_budget": 350000.0,
            "duration_months": 6,
            "rationale": "<p>Promote dietary diversity and fresh vegetable access for 180 tribal households through homestead kitchen gardens and organic compost training.</p>",
            "raised_by": "Administrator"
        }).insert(ignore_permissions=True)

    # 3. Beneficiaries
    sample_bens = [
        ("BEN-2026-001", "Ramesh Tukaram Patil", "Male", "Small Farmer", "Rampur"),
        ("BEN-2026-002", "Sunita Rahul Shinde", "Female", "Small Farmer", "Rampur"),
        ("BEN-2026-003", "Ganesh Vithal Deshmukh", "Male", "Marginal Farmer", "Sonapur")
    ]
    for b_id, b_name, gen, cat, vil in sample_bens:
        if not frappe.db.exists("Beneficiary", b_id):
            frappe.get_doc({
                "doctype": "Beneficiary",
                "name": b_id,
                "beneficiary_name": b_name,
                "gender": gen,
                "category": cat,
                "village": vil
            }).insert(ignore_permissions=True)

    # 4. KREs (Key Result Expectations)
    proj_name = frappe.db.get_value("Project", {"project_name": "Kalyanpur Integrated Watershed Development"}, "name")
    if not proj_name:
        p = frappe.get_doc({
            "doctype": "Project",
            "project_name": "Kalyanpur Integrated Watershed Development",
            "company": company,
            "custom_project_phase": "Execution",
            "custom_thematic_area": "Watershed Management"
        }).insert(ignore_permissions=True)
        proj_name = p.name

    if not frappe.db.exists("KRE", {"kre_name": "Area brought under soil conservation bunding"}):
        kre1 = frappe.get_doc({
            "doctype": "KRE",
            "kre_name": "Area brought under soil conservation bunding",
            "project": proj_name,
            "unit": "Hectares",
            "baseline_value": 0.0,
            "current_value": 85.0,
            "target_value": 150.0
        }).insert(ignore_permissions=True)

    if not frappe.db.exists("KRE", {"kre_name": "Smallholder farmers adopting micro-irrigation"}):
        kre2 = frappe.get_doc({
            "doctype": "KRE",
            "kre_name": "Smallholder farmers adopting micro-irrigation",
            "project": proj_name,
            "unit": "Farmers",
            "baseline_value": 10.0,
            "current_value": 65.0,
            "target_value": 100.0
        }).insert(ignore_permissions=True)

    print("Demo data seeded successfully!")

