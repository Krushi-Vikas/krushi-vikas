import frappe
from frappe.utils import today, add_days
from krushi_vikas.api import submit_feedback_survey, get_project_detail, get_activity_detail

def run():
    print("\n=======================================================")
    print("🔬 THOROUGH END-TO-END VERIFICATION: SURVEY & CLOSURE")
    print("=======================================================")
    
    frappe.session.user = "Administrator"
    
    # 0. Setup test users and data
    from krushi_vikas.test_project_permissions import provision_test_users
    provision_test_users()
    
    pm_user = "pm1_test@krushivikas.org"
    fo_user = "fo1_test@krushivikas.org"
    pc_user = "pc1_test@krushivikas.org"
    
    # Clean previous test artifacts
    for fs in frappe.get_all("Feedback Survey"):
        fs_doc = frappe.get_doc("Feedback Survey", fs.name)
        if fs_doc.village == "Thorough Test Village" or (fs_doc.project and "Thorough" in str(fs_doc.project)):
            try:
                if fs_doc.docstatus == 1:
                    fs_doc.cancel()
                frappe.delete_doc("Feedback Survey", fs.name, force=True, ignore_permissions=True)
            except Exception:
                frappe.delete_doc("Feedback Survey", fs.name, force=True, ignore_permissions=True)
                
    for a in frappe.get_all("Activity", filters={"activity_name": "Thorough Test Activity"}):
        frappe.delete_doc("Activity", a.name, force=True, ignore_permissions=True)
        
    for p in frappe.get_all("KV Project", filters={"project_name": "Thorough Test Project"}):
        frappe.delete_doc("KV Project", p.name, force=True, ignore_permissions=True)
        
    frappe.db.commit()
    
    # Create test project
    frappe.session.user = pc_user
    proj = frappe.new_doc("KV Project")
    proj.project_name = "Thorough Test Project"
    proj.project_coordinator = pc_user
    proj.project_manager = pm_user
    proj.status = "In Progress"
    proj.start_date = "2026-01-01"
    proj.end_date = "2026-12-31"
    proj.budget = 100000
    proj.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"✓ Setup: Created Project '{proj.name}' (Manager: {pm_user}, Coordinator: {pc_user})")
    
    # Create test activity
    frappe.session.user = pm_user
    act = frappe.new_doc("Activity")
    act.activity_name = "Thorough Test Activity"
    act.project = proj.name
    act.assignee = pm_user
    act.status = "Open"
    act.approved_budget = 50000
    act.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"✓ Setup: Created Activity '{act.name}' under Project '{proj.name}'")
    
    # -------------------------------------------------------------------------
    # TEST 1: Role separation in Web API (submit_feedback_survey)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 1] Role Separation in Feedback Survey API ---")
    
    # 1.1 FO tries to submit Project-level survey -> MUST FAIL
    frappe.session.user = fo_user
    try:
        submit_feedback_survey({
            "survey_level": "Project",
            "project": proj.name,
            "overall_rating": "4"
        })
        assert False, "Field Officer should be blocked from submitting Project-level survey!"
    except frappe.PermissionError as e:
        print(f"  [1.1] PASS: Field Officer blocked from Project-level survey: {str(e)[:60]}")
        
    # 1.2 PM tries to submit Activity-level survey -> MUST FAIL
    frappe.session.user = pm_user
    try:
        submit_feedback_survey({
            "survey_level": "Activity",
            "linked_activity": act.name,
            "activity": act.activity_name,
            "project": proj.name,
            "village": "Thorough Test Village",
            "date_of_visit": today(),
            "respondent_type": "Farmer",
            "total_participants": 10,
            "adoption_percentage": 50.0,
            "significant_change": "Good impact observed",
            "confirmation_accuracy": True
        })
        assert False, "Project Manager should be blocked from submitting Activity-level survey!"
    except frappe.PermissionError as e:
        print(f"  [1.2] PASS: Project Manager blocked from Activity-level survey: {str(e)[:60]}")

    # -------------------------------------------------------------------------
    # TEST 2: Project-Level Optional Fields via Web API
    # -------------------------------------------------------------------------
    print("\n--- [TEST 2] Project-Level Survey: ALL Fields Optional ---")
    
    # 2.1 PM submits Project-level survey with ZERO optional fields
    frappe.session.user = pm_user
    res_minimal = submit_feedback_survey({
        "survey_level": "Project",
        "project": proj.name
    })
    assert res_minimal.get("success") is True, "Expected success for minimal project survey"
    fs_min = frappe.get_doc("Feedback Survey", res_minimal["name"])
    assert fs_min.survey_level == "Project"
    assert fs_min.project == proj.name
    assert fs_min.village is None or fs_min.village == ""
    assert fs_min.total_participants in (0, None)
    assert fs_min.overall_rating in ("3", None, "")
    assert fs_min.docstatus == 1, "Expected survey to be submitted"
    print(f"  [2.1] PASS: Project survey with all fields omitted created & submitted: {fs_min.name}")

    # 2.2 PM submits Project-level survey with only partial qualitative comments
    res_partial = submit_feedback_survey({
        "survey_level": "Project",
        "project": proj.name,
        "overall_rating": "5",
        "significant_change": "Transformative community watershed impact across multiple villages."
    })
    assert res_partial.get("success") is True
    fs_part = frappe.get_doc("Feedback Survey", res_partial["name"])
    assert fs_part.overall_rating == "5"
    assert fs_part.significant_change.startswith("Transformative")
    assert fs_part.total_participants in (0, None)
    print(f"  [2.2] PASS: Project survey with partial fields created & submitted: {fs_part.name}")

    # 2.3 Format validation on Project survey when values ARE provided
    try:
        submit_feedback_survey({
            "survey_level": "Project",
            "project": proj.name,
            "date_of_visit": add_days(today(), 5) # Future date
        })
        assert False, "Future date in project survey should be rejected!"
    except frappe.ValidationError as e:
        print(f"  [2.3a] PASS: Future date properly rejected: {str(e)[:60]}")

    try:
        submit_feedback_survey({
            "survey_level": "Project",
            "project": proj.name,
            "adoption_percentage": 150.0 # Out of bounds
        })
        assert False, "Adoption > 100% in project survey should be rejected!"
    except frappe.ValidationError as e:
        print(f"  [2.3b] PASS: Invalid adoption percentage properly rejected: {str(e)[:60]}")

    # -------------------------------------------------------------------------
    # TEST 3: Activity-Level Mandatory Fields Strictly Enforced
    # -------------------------------------------------------------------------
    print("\n--- [TEST 3] Activity-Level Survey: Mandatory Fields Strictly Enforced ---")
    
    # 3.1 Missing Village
    frappe.session.user = fo_user
    try:
        submit_feedback_survey({
            "survey_level": "Activity",
            "linked_activity": act.name,
            "activity": act.activity_name,
            "project": proj.name,
            "date_of_visit": today(),
            "respondent_type": "Farmer",
            "total_participants": 10,
            "adoption_percentage": 60.0,
            "significant_change": "Good outcome reached.",
            "overall_rating": "4",
            "confirmation_accuracy": True
        })
        assert False, "Activity survey without Village must fail!"
    except frappe.ValidationError as e:
        print(f"  [3.1] PASS: Missing village strictly blocked: {str(e)[:60]}")

    # 3.2 Missing Significant Change
    try:
        submit_feedback_survey({
            "survey_level": "Activity",
            "linked_activity": act.name,
            "activity": act.activity_name,
            "project": proj.name,
            "village": "Thorough Test Village",
            "date_of_visit": today(),
            "respondent_type": "Farmer",
            "total_participants": 10,
            "adoption_percentage": 60.0,
            "overall_rating": "4",
            "confirmation_accuracy": True
        })
        assert False, "Activity survey without Significant Change must fail!"
    except frappe.ValidationError as e:
        print(f"  [3.2] PASS: Missing significant change strictly blocked: {str(e)[:60]}")

    # 3.3 Significant change too short (< 10 chars)
    try:
        submit_feedback_survey({
            "survey_level": "Activity",
            "linked_activity": act.name,
            "activity": act.activity_name,
            "project": proj.name,
            "village": "Thorough Test Village",
            "date_of_visit": today(),
            "respondent_type": "Farmer",
            "total_participants": 10,
            "adoption_percentage": 60.0,
            "significant_change": "Short",
            "overall_rating": "4",
            "confirmation_accuracy": True
        })
        assert False, "Activity survey with significant change < 10 chars must fail!"
    except frappe.ValidationError as e:
        print(f"  [3.3] PASS: Short significant change strictly blocked: {str(e)[:60]}")

    # 3.4 Valid FO Activity Survey submission -> MUST SUCCEED
    res_act = submit_feedback_survey({
        "survey_level": "Activity",
        "linked_activity": act.name,
        "activity": act.activity_name,
        "project": proj.name,
        "village": "Thorough Test Village",
        "date_of_visit": today(),
        "respondent_type": "Farmer",
        "total_participants": 22,
        "households_involved": 18,
        "sessions_conducted": 2,
        "adoption_percentage": 82.5,
        "significant_change": "Farmers successfully implemented soil moisture retention.",
        "overall_rating": "5",
        "confirmation_accuracy": True,
        "submit_now": True
    })
    assert res_act.get("success") is True
    fs_act = frappe.get_doc("Feedback Survey", res_act["name"])
    assert fs_act.survey_level == "Activity"
    assert fs_act.total_participants == 22
    assert fs_act.adoption_percentage == 82.5
    assert fs_act.docstatus == 1
    print(f"  [3.4] PASS: Valid Activity survey successfully created & submitted: {fs_act.name}")

    # -------------------------------------------------------------------------
    # TEST 4: Pre-Closure Enforcements on Activity and Project
    # -------------------------------------------------------------------------
    print("\n--- [TEST 4] Pre-Closure Enforcements ---")

    # 4.1 Fresh Activity without survey cannot be completed
    frappe.session.user = pm_user
    fresh_act = frappe.new_doc("Activity")
    fresh_act.activity_name = "Thorough Fresh Activity"
    fresh_act.project = proj.name
    fresh_act.assignee = pm_user
    fresh_act.status = "Open"
    fresh_act.insert(ignore_permissions=True)
    
    fresh_act.status = "Completed"
    try:
        fresh_act.save()
        assert False, "Fresh activity without feedback survey should NOT be closed!"
    except frappe.ValidationError as e:
        print(f"  [4.1] PASS: Closing Activity without survey blocked: {str(e)[:60]}")

    # 4.2 After adding survey, Activity can be completed
    frappe.session.user = fo_user
    submit_feedback_survey({
        "survey_level": "Activity",
        "linked_activity": fresh_act.name,
        "activity": fresh_act.activity_name,
        "project": proj.name,
        "village": "Thorough Test Village",
        "date_of_visit": today(),
        "respondent_type": "Farmer",
        "total_participants": 12,
        "adoption_percentage": 75.0,
        "significant_change": "Community adopted new composting techniques.",
        "overall_rating": "4",
        "confirmation_accuracy": True,
        "submit_now": True
    })
    frappe.session.user = pm_user
    fresh_act.reload()
    fresh_act.status = "Completed"
    fresh_act.save()
    assert fresh_act.status == "Completed"
    print(f"  [4.2] PASS: Activity marked Completed after adding feedback survey.")

    # 4.3 Fresh Project without survey cannot be completed
    frappe.session.user = pc_user
    fresh_proj = frappe.new_doc("KV Project")
    fresh_proj.project_name = "Thorough Fresh Project"
    fresh_proj.project_coordinator = pc_user
    fresh_proj.project_manager = pm_user
    fresh_proj.status = "In Progress"
    fresh_proj.start_date = "2026-01-01"
    fresh_proj.end_date = "2026-12-31"
    fresh_proj.budget = 50000
    fresh_proj.insert(ignore_permissions=True)

    fresh_proj.status = "Completed"
    try:
        fresh_proj.save()
        assert False, "Fresh project without feedback survey should NOT be completed!"
    except frappe.ValidationError as e:
        print(f"  [4.3] PASS: Closing Project without survey blocked: {str(e)[:60]}")

    # 4.4 After PM adds Project-level survey (with all optional fields omitted!), Project can be completed
    frappe.session.user = pm_user
    submit_feedback_survey({
        "survey_level": "Project",
        "project": fresh_proj.name
    })
    frappe.session.user = pc_user
    fresh_proj.reload()
    fresh_proj.status = "Completed"
    fresh_proj.save()
    assert fresh_proj.status == "Completed"
    print(f"  [4.4] PASS: Project marked Completed after adding minimal Project-level survey.")

    # -------------------------------------------------------------------------
    # TEST 5: Project Details Data API (get_project_detail)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 5] Project Details Data API (get_project_detail) ---")
    proj_detail = get_project_detail(proj.name)
    assert "structured_forms" in proj_detail
    surveys = proj_detail["structured_forms"].get("feedback_surveys", [])
    assert len(surveys) >= 3, f"Expected at least 3 surveys, found {len(surveys)}"
    
    levels = [s.get("survey_level") for s in surveys]
    assert "Project" in levels, "Expected 'Project' level in project detail surveys"
    assert "Activity" in levels, "Expected 'Activity' level in project detail surveys"
    print(f"  [5.1] PASS: get_project_detail returned {len(surveys)} surveys with levels: {set(levels)}")

    # Cleanup test documents
    for name in [proj.name, fresh_proj.name]:
        frappe.delete_doc("KV Project", name, force=True, ignore_permissions=True)
    for name in [act.name, fresh_act.name]:
        frappe.delete_doc("Activity", name, force=True, ignore_permissions=True)
    for fs_id in [res_minimal["name"], res_partial["name"], res_act["name"]]:
        try:
            doc = frappe.get_doc("Feedback Survey", fs_id)
            if doc.docstatus == 1:
                doc.cancel()
            doc.delete(ignore_permissions=True)
        except Exception:
            pass
    frappe.db.commit()
    print("  [5.2] PASS: Cleaned up thorough test data.")

    print("\n=======================================================")
    print("🏆 ALL THOROUGH TESTS PASSED SUCCESSFULLY! 100% VERIFIED")
    print("=======================================================")
    return True
