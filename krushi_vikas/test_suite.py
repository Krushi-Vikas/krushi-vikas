import frappe
from frappe.model.workflow import apply_workflow

def get_or_create_company():
    company = frappe.db.get_value("Company", {"is_group": 0}, "name")
    if not company:
        for wt in ["Transit", "Stores", "Finished Goods", "Work In Progress"]:
            if not frappe.db.exists("Warehouse Type", wt):
                frappe.get_doc({"doctype": "Warehouse Type", "name": wt}).insert(ignore_permissions=True)
                
        c = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Krushi Vikas Foundation",
            "abbr": "KVF",
            "default_currency": "INR",
            "country": "India"
        }).insert(ignore_permissions=True)
        company = c.name
    return company

def run():
    print("=== STARTING KRUSHI VIKAS VERIFICATION TESTS ===")
    company = get_or_create_company()
    print(f"Using Company: {company}")
    test_hard_dependency_gate(company)
    test_kre_calculation_and_outcome_push(company)
    test_survey_template_api()
    test_project_goal_weightage(company)
    frappe.db.rollback()
    print("=== ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

def test_hard_dependency_gate(company):
    print("\n[Test 1] Testing Hard Dependency Gating on Task...")
    p = frappe.get_doc({
        "doctype": "Project",
        "project_name": "Test Watershed Project",
        "company": company,
        "custom_project_phase": "Execution"
    }).insert(ignore_permissions=True)
    
    t1 = frappe.get_doc({
        "doctype": "Task",
        "subject": "Digging Trenches (Predecessor)",
        "project": p.name,
        "status": "Open"
    }).insert(ignore_permissions=True)
    
    t2 = frappe.get_doc({
        "doctype": "Task",
        "subject": "Planting Saplings (Successor)",
        "project": p.name,
        "status": "Open",
        "depends_on": [{"task": t1.name}]
    }).insert(ignore_permissions=True)
    
    t2.status = "Completed"
    try:
        t2.save(ignore_permissions=True)
        assert False, "Should have thrown ValidationError because predecessor is incomplete!"
    except frappe.ValidationError as e:
        print("  -> Expected block triggered successfully:", str(e))
        
    t1.reload()
    t1.status = "Completed"
    t1.save(ignore_permissions=True)
    
    t2.reload()
    t2.status = "Completed"
    t2.save(ignore_permissions=True)
    assert t2.status == "Completed"
    print("  -> Successor task completed successfully after predecessor was completed!")

def test_kre_calculation_and_outcome_push(company):
    print("\n[Test 2] Testing KRE Math and Activity Outcome Workflow Push...")
    p = frappe.get_doc({
        "doctype": "Project",
        "project_name": "Test Soil Moisture Project",
        "company": company
    }).insert(ignore_permissions=True)
    
    kre = frappe.get_doc({
        "doctype": "KRE",
        "kre_name": "Area brought under micro-irrigation",
        "project": p.name,
        "unit": "Hectares",
        "baseline_value": 10.0,
        "current_value": 10.0,
        "target_value": 110.0
    }).insert(ignore_permissions=True)
    
    assert kre.achievement_pct == 0.0
    
    task = frappe.get_doc({
        "doctype": "Task",
        "subject": "Install Drip Kits Block A",
        "project": p.name,
        "custom_kre": kre.name,
        "custom_is_milestone_activity": 0
    }).insert(ignore_permissions=True)
    
    outcome = frappe.get_doc({
        "doctype": "Activity Outcome",
        "task": task.name,
        "project": p.name,
        "kre": kre.name,
        "is_milestone_activity": 0,
        "measurement_date": frappe.utils.today(),
        "baseline_value": 10.0,
        "actual_value": 50.0,
        "satisfaction_rating": 4.5,
        "beneficiary_count": 25,
        "workflow_state": "Draft"
    }).insert(ignore_permissions=True)
    
    print("  -> Stepping through Workflow Approval Chain (Draft -> PC Review -> PM Approval -> Approved)...")
    # Grant required roles to current session user for test
    frappe.set_user("Administrator")
    
    apply_workflow(outcome, "Submit")
    assert outcome.workflow_state == "PC Review"
    print("     [+] Field Officer Submitted -> State: PC Review")
    
    apply_workflow(outcome, "Approve")
    assert outcome.workflow_state == "PM Approval"
    print("     [+] PC Approved -> State: PM Approval")
    
    apply_workflow(outcome, "Approve")
    assert outcome.workflow_state == "Approved"
    print("     [+] PM Approved -> State: Approved")
    
    # Reload KRE and verify value
    kre.reload()
    print(f"  -> KRE Current Value after Outcome: {kre.current_value} (Expected: 60.0)")
    print(f"  -> KRE Achievement %: {kre.achievement_pct:.2f}% (Expected: 50.0%)")
    print(f"  -> KRE Status: {kre.status} (Expected: 'On Track')")
    assert kre.current_value == 60.0
    assert abs(kre.achievement_pct - 50.0) < 0.01
    assert len(kre.measurements) == 1
    print("  -> KRE measurement history correctly logged via workflow hook!")

def test_survey_template_api():
    print("\n[Test 3] Testing Dynamic Survey Template API...")
    tmpl = frappe.get_doc({
        "doctype": "Survey Template",
        "template_name": "Rapid Rural Appraisal (RRA) Template",
        "survey_type": "RRA",
        "description": "Pre-proposal field appraisal",
        "questions": [
            {"sequence": 1, "question_text": "Average family landholding (acres)", "answer_type": "Number", "is_required": 1},
            {"sequence": 2, "question_text": "Primary water source", "answer_type": "Select", "options": "Well\nCanal\nBorewell\nRainfed"},
            {"sequence": 3, "question_text": "Farmer satisfaction with current yield", "answer_type": "Rating"}
        ]
    }).insert(ignore_permissions=True)
    
    from krushi_vikas.api import get_template_questions
    questions = get_template_questions(tmpl.name)
    assert len(questions) == 3
    assert questions[0]["question_text"] == "Average family landholding (acres)"
    print(f"  -> Loaded {len(questions)} questions dynamically via API!")

def test_project_goal_weightage(company):
    print("\n[Test 4] Testing Project Goal & Weighted Objectives Rollup...")
    p = frappe.get_doc({
        "doctype": "Project",
        "project_name": "Test Sustainable Agri Goal Project",
        "company": company
    }).insert(ignore_permissions=True)
    
    kre1 = frappe.get_doc({
        "doctype": "KRE",
        "kre_name": "Metric 1",
        "project": p.name,
        "baseline_value": 0,
        "current_value": 80,
        "target_value": 100
    }).insert(ignore_permissions=True)
    
    kre2 = frappe.get_doc({
        "doctype": "KRE",
        "kre_name": "Metric 2",
        "project": p.name,
        "baseline_value": 0,
        "current_value": 50,
        "target_value": 100
    }).insert(ignore_permissions=True)
    
    goal = frappe.get_doc({
        "doctype": "Project Goal",
        "goal_name": "Improve Farmer Livelihoods by 50%",
        "project": p.name,
        "objectives": [
            {"objective_name": "Water Security", "weightage": 60.0, "kre": kre1.name},
            {"objective_name": "Soil Health", "weightage": 40.0, "kre": kre2.name}
        ]
    }).insert(ignore_permissions=True)
    
    print(f"  -> Rolled-up Goal Achievement: {goal.actual_completion_pct:.2f}% (Expected: 68.00%)")
    assert abs(goal.actual_completion_pct - 68.0) < 0.01
    print("  -> Goal OKR weightage rollup validated successfully!")
