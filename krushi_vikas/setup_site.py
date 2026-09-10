import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
import json

def run():
    setup_roles()
    setup_docperms()
    setup_custom_fields()
    setup_workspace()
    setup_workflows()
    frappe.db.commit()
    print("All site configurations and workflows completed successfully!")

def setup_roles():
    print("Setting up Roles...")
    roles = [
        "Field Officer",
        "Project Manager",
        "Project Coordinator",
        "Project Director",
        "CEO"
    ]
    for r in roles:
        if not frappe.db.exists("Role", r):
            doc = frappe.new_doc("Role")
            doc.role_name = r
            doc.insert(ignore_permissions=True)
            print(f"Created Role: {r}")

def setup_docperms():
    print("Setting up Custom DocPerms...")
    perms = [
        # Project
        {"parent": "Project", "role": "CEO", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Project", "role": "Project Director", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Project", "role": "Project Coordinator", "read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "Project", "role": "Project Manager", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "Project", "role": "Field Officer", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        # Task
        {"parent": "Task", "role": "CEO", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Task", "role": "Project Director", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Task", "role": "Project Coordinator", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Task", "role": "Project Manager", "read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "Task", "role": "Field Officer", "read": 1, "write": 1, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        # KV Project — the app's own project doctype.
        #
        # A single Custom DocPerm row on a doctype makes Frappe ignore the
        # permissions declared in its JSON entirely. Rows existed here for
        # four roles, which silently dropped CEO and Project Director even
        # though kv_project.json lists them — so the unrestricted executive
        # access in api.has_project_permission never took effect, because the
        # base permission check denied them first.
        {"parent": "KV Project", "role": "CEO", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "KV Project", "role": "Project Director", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "KV Project", "role": "Project Coordinator", "read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "KV Project", "role": "Project Manager", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "KV Project", "role": "Field Officer", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        # Activity — mirrors api.has_activity_permission.
        {"parent": "Activity", "role": "CEO", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Activity", "role": "Project Director", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Activity", "role": "Project Coordinator", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Activity", "role": "Project Manager", "read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "Activity", "role": "Field Officer", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        # Roadmap documents (steps 01-03). Reviewers need write access in
        # their review state; the workflows narrow it further per state.
        {"parent": "Concept Note", "role": "CEO", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Concept Note", "role": "Project Director", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Concept Note", "role": "Project Coordinator", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Concept Note", "role": "Project Manager", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "Concept Note", "role": "Field Officer", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "RRA Report", "role": "CEO", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "RRA Report", "role": "Project Director", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "RRA Report", "role": "Project Coordinator", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "RRA Report", "role": "Project Manager", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "RRA Report", "role": "Field Officer", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
        {"parent": "Project Proposal", "role": "CEO", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Project Proposal", "role": "Project Director", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Project Proposal", "role": "Project Coordinator", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Project Proposal", "role": "Project Manager", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1, "report": 1, "export": 1, "print": 1},
        {"parent": "Project Proposal", "role": "Field Officer", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 1, "print": 1},
    ]
    for p in perms:
        if not frappe.db.exists("DocType", p["parent"]):
            continue

        existing = frappe.db.get_value(
            "Custom DocPerm", {"parent": p["parent"], "role": p["role"]}, "name"
        )

        if existing:
            # Update in place: a stale row that is missing a permission is
            # worse than no row at all, because Custom DocPerms suppress the
            # doctype's own JSON permissions wholesale.
            doc = frappe.get_doc("Custom DocPerm", existing)
            doc.update(p)
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.new_doc("Custom DocPerm")
            doc.update(p)
            doc.insert(ignore_permissions=True)

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
                "label": "Activity Owner / Field Officer",
                "fieldtype": "Link",
                "options": "User",
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
            },
            {
                "fieldname": "custom_activity",
                "label": "Activity",
                "fieldtype": "Link",
                "options": "Activity",
                "insert_after": "project",
                "in_list_view": 1,
                "in_standard_filter": 1,
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
                "label": "Theme",
                "fieldtype": "Link",
                "options": "Project Theme",
                "insert_after": "custom_project_phase",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_project_coordinator",
                "label": "Project Coordinator",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "custom_thematic_area",
                "in_list_view": 1,
                "reqd": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_project_manager",
                "label": "Project Manager",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "custom_project_coordinator",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_concept_note",
                "label": "Originating Concept Note",
                "fieldtype": "Link",
                "options": "Concept Note",
                "insert_after": "custom_project_manager",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_financial_section",
                "label": "Financial Tracking & Budget",
                "fieldtype": "Section Break",
                "insert_after": "custom_concept_note",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_budget",
                "label": "Budget (INR)",
                "fieldtype": "Currency",
                "default": "0",
                "insert_after": "custom_financial_section",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_actual_amount_spent",
                "label": "Actual Amount Spent (INR)",
                "fieldtype": "Currency",
                "default": "0",
                "insert_after": "custom_budget",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_col_budget_brk",
                "fieldtype": "Column Break",
                "insert_after": "custom_actual_amount_spent",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_remaining_funds",
                "label": "Remaining Funds (INR)",
                "fieldtype": "Currency",
                "default": "0",
                "read_only": 1,
                "insert_after": "custom_col_budget_brk",
                "in_list_view": 1,
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_structural_forms_sec",
                "label": "Linked Structural Forms",
                "fieldtype": "Section Break",
                "insert_after": "custom_remaining_funds",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_linked_baseline_survey",
                "label": "Linked Baseline Form",
                "fieldtype": "Link",
                "options": "Baseline Survey",
                "insert_after": "custom_structural_forms_sec",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_col_forms_brk",
                "fieldtype": "Column Break",
                "insert_after": "custom_linked_baseline_survey",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_linked_field_tracking_form",
                "label": "Linked Feedback Survey / Field Tracking Form",
                "fieldtype": "Link",
                "options": "Feedback Survey",
                "insert_after": "custom_col_forms_brk",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_feedback_surveys_sec",
                "label": "Feedback Surveys & Field Observations",
                "fieldtype": "Section Break",
                "insert_after": "custom_linked_field_tracking_form",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_feedback_surveys",
                "label": "Feedback Surveys",
                "fieldtype": "Table",
                "options": "Project Feedback Detail",
                "insert_after": "custom_feedback_surveys_sec",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_activities_sec",
                "label": "Activities",
                "fieldtype": "Section Break",
                "insert_after": "custom_feedback_surveys",
                "module": "Krushi Vikas"
            },
            {
                "fieldname": "custom_activities",
                "label": "Project Activities",
                "fieldtype": "Table",
                "options": "Project Activity",
                "insert_after": "custom_activities_sec",
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
        ("PM Review", "Warning"),
        ("PC Approval", "Info"),
        ("PC Review", "Warning"),
        ("PM Approval", "Info"),
        ("Director Signoff", "Primary"),
        ("Approved", "Success"),
        ("Rejected", "Danger"),
        ("Under Review", "Warning"),
        ("Management Review", "Warning"),
        ("Director Review", "Info")
    ]
    for state_name, style in states:
        if not frappe.db.exists("Workflow State", state_name):
            doc = frappe.new_doc("Workflow State")
            doc.workflow_state_name = state_name
            doc.style = style
            doc.insert(ignore_permissions=True)

    actions = [
        "Submit", "Review", "Approve", "Reject", "Send Back",
        "Submit for Review", "Escalate"
    ]
    for action_name in actions:
        if not frappe.db.exists("Workflow Action Master", action_name):
            doc = frappe.new_doc("Workflow Action Master")
            doc.workflow_action_name = action_name
            doc.insert(ignore_permissions=True)

    # Activity Outcome Workflow — step 10 of the roadmap.
    ensure_workflow(
        "Activity Outcome Approval", "Activity Outcome", "workflow_state",
        [
            {"state": "Draft", "doc_status": "0", "allow_edit_roles": ["Field Officer"]},
            {"state": "PM Review", "doc_status": "0", "allow_edit_roles": ["Project Manager"]},
            {"state": "PC Approval", "doc_status": "1", "allow_edit_roles": ["Project Coordinator"]},
            {"state": "Director Signoff", "doc_status": "1", "allow_edit_roles": [EXEC]},
            {"state": "Approved", "doc_status": "1", "allow_edit_roles": ["Project Coordinator"]},
            {"state": "Rejected", "doc_status": "0", "allow_edit_roles": ["Field Officer"]},
        ],
        [
            {"state": "Draft", "action": "Submit", "next_state": "PM Review", "allowed": "Field Officer"},
            {"state": "PM Review", "action": "Approve", "next_state": "PC Approval", "allowed": "Project Manager"},
            {"state": "PM Review", "action": "Reject", "next_state": "Rejected", "allowed": "Project Manager"},
            {"state": "Rejected", "action": "Submit", "next_state": "PM Review", "allowed": "Field Officer"},
            {"state": "PC Approval", "action": "Approve", "next_state": "Approved",
             "allowed": "Project Coordinator", "condition": "doc.is_milestone_activity == 0"},
            {"state": "PC Approval", "action": "Approve", "next_state": "Director Signoff",
             "allowed": "Project Coordinator", "condition": "doc.is_milestone_activity == 1"},
            {"state": "Director Signoff", "action": "Approve", "next_state": "Approved", "allowed": EXEC},
        ],
    )

    setup_journey_workflows()


# Leadership tiers that sign off. Kept together so a role rename is a
# one-line change rather than a hunt through transitions.
EXEC = "Project Director"


# An active workflow narrows editing to the roles named in each state's
# allow_edit. Without these, the executive tier would lose the unrestricted
# rights that krushi_vikas.api.has_project_permission grants them — a
# workflow would silently outrank the permission model.
ALWAYS_EDIT = ("System Manager", "Project Director", "CEO")


def expand_states(states):
    """Frappe stores one role per state row, so a state editable by several
    roles needs one row each. Written here as a list per state and expanded."""
    rows = []

    for state in states:
        roles = list(state.get("allow_edit_roles") or [])

        for role in ALWAYS_EDIT:
            if role not in roles:
                roles.append(role)

        for role in roles:
            rows.append(
                {
                    "state": state["state"],
                    "doc_status": state["doc_status"],
                    "allow_edit": role,
                }
            )

    return rows


def ensure_workflow(name, doctype, state_field, states, transitions):
    """Recreate a workflow from scratch so edits to this file always win.

    Frappe has no merge semantics for workflow rows; deleting and
    reinserting is the only way to make this idempotent.
    """
    if frappe.db.exists("Workflow", name):
        frappe.delete_doc("Workflow", name, ignore_permissions=True, force=True)

    states = expand_states(states)

    wf = frappe.new_doc("Workflow")
    wf.workflow_name = name
    wf.document_type = doctype
    wf.is_active = 1
    wf.workflow_state_field = state_field
    wf.send_email_alert = 0
    wf.set("states", states)
    wf.set("transitions", transitions)
    wf.insert(ignore_permissions=True)
    print(f"Workflow '{name}' created!")


def setup_journey_workflows():
    """The maker-checker gates of the 10-step operational roadmap.

    Steps 04 (external approval of the proposal) and 07 (internal approval
    of the project) are the two hard gates; the concept note and appraisal
    carry lighter review loops so nothing enters the pipeline unreviewed.
    """

    # ── 01 Concept Note — reviewed by management ──────────────────
    # Uses the existing `status` Select rather than adding a second
    # status field to the form.
    ensure_workflow(
        "Concept Note Approval", "Concept Note", "status",
        [
            {"state": "Draft", "doc_status": "0", "allow_edit_roles": ["Project Coordinator"]},
            {"state": "Under Review", "doc_status": "0", "allow_edit_roles": [EXEC]},
            {"state": "Approved", "doc_status": "1", "allow_edit_roles": [EXEC]},
            {"state": "Rejected", "doc_status": "0", "allow_edit_roles": ["Project Coordinator"]},
        ],
        [
            {"state": "Draft", "action": "Submit for Review", "next_state": "Under Review",
             "allowed": "Project Coordinator"},
            {"state": "Under Review", "action": "Approve", "next_state": "Approved", "allowed": EXEC},
            {"state": "Under Review", "action": "Reject", "next_state": "Rejected", "allowed": EXEC},
            {"state": "Rejected", "action": "Submit for Review", "next_state": "Under Review",
             "allowed": "Project Coordinator"},
        ],
    )

    # ── 02 RRA Report — management appraisal ──────────────────────
    ensure_workflow(
        "RRA Report Approval", "RRA Report", "workflow_state",
        [
            {"state": "Draft", "doc_status": "0", "allow_edit_roles": ["Project Coordinator"]},
            {"state": "Management Review", "doc_status": "0", "allow_edit_roles": [EXEC]},
            {"state": "Approved", "doc_status": "1", "allow_edit_roles": [EXEC]},
            {"state": "Rejected", "doc_status": "0", "allow_edit_roles": ["Project Coordinator"]},
        ],
        [
            {"state": "Draft", "action": "Submit for Review", "next_state": "Management Review",
             "allowed": "Project Coordinator"},
            {"state": "Management Review", "action": "Approve", "next_state": "Approved", "allowed": EXEC},
            {"state": "Management Review", "action": "Reject", "next_state": "Rejected", "allowed": EXEC},
            {"state": "Rejected", "action": "Submit for Review", "next_state": "Management Review",
             "allowed": "Project Coordinator"},
        ],
    )

    # ── 03/04 Proposal — drafted by PM, signed off by Director/CXO ─
    # This is gate 04 of the roadmap. create_project_from_proposal()
    # refuses to run until this reaches Approved.
    ensure_workflow(
        "Project Proposal Approval", "Project Proposal", "workflow_state",
        [
            {"state": "Draft", "doc_status": "0", "allow_edit_roles": ["Project Manager"]},
            {"state": "PC Review", "doc_status": "0", "allow_edit_roles": ["Project Coordinator"]},
            {"state": "Director Review", "doc_status": "0", "allow_edit_roles": [EXEC]},
            {"state": "Approved", "doc_status": "1", "allow_edit_roles": [EXEC]},
            {"state": "Rejected", "doc_status": "0", "allow_edit_roles": ["Project Manager"]},
        ],
        [
            {"state": "Draft", "action": "Submit for Review", "next_state": "PC Review",
             "allowed": "Project Manager"},
            {"state": "PC Review", "action": "Escalate", "next_state": "Director Review",
             "allowed": "Project Coordinator"},
            {"state": "PC Review", "action": "Send Back", "next_state": "Draft",
             "allowed": "Project Coordinator"},
            {"state": "Director Review", "action": "Approve", "next_state": "Approved", "allowed": EXEC},
            {"state": "Director Review", "action": "Reject", "next_state": "Rejected", "allowed": EXEC},
            {"state": "Rejected", "action": "Submit for Review", "next_state": "PC Review",
             "allowed": "Project Manager"},
        ],
    )

    # ── 07 Internal approval of the project ───────────────────────
    # KV Project is not submittable, so every state stays at doc_status 0.
    ensure_workflow(
        "KV Project Internal Approval", "KV Project", "workflow_state",
        [
            {"state": "Draft", "doc_status": "0", "allow_edit_roles": ["Project Coordinator"]},
            {"state": "Director Review", "doc_status": "0", "allow_edit_roles": [EXEC]},
            {"state": "Approved", "doc_status": "0", "allow_edit_roles": [EXEC]},
            {"state": "Rejected", "doc_status": "0", "allow_edit_roles": ["Project Coordinator"]},
        ],
        [
            {"state": "Draft", "action": "Submit for Review", "next_state": "Director Review",
             "allowed": "Project Coordinator"},
            {"state": "Director Review", "action": "Approve", "next_state": "Approved", "allowed": EXEC},
            {"state": "Director Review", "action": "Reject", "next_state": "Rejected", "allowed": EXEC},
            {"state": "Rejected", "action": "Submit for Review", "next_state": "Director Review",
             "allowed": "Project Coordinator"},
        ],
    )

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
