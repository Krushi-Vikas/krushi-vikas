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
    test_feedback_survey_lifecycle(company)
    test_village_profile_lifecycle(company)
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

def test_feedback_survey_lifecycle(company):
    print("\n[Test 5] Testing Feedback Survey DocType, Validations, and Submission API...")
    from krushi_vikas.api import submit_feedback_survey, get_feedback_survey_options, get_feedback_analytics
    
    # 1. Test Options API
    opts = get_feedback_survey_options()
    assert "villages" in opts and len(opts["villages"]) > 0
    assert "activities" in opts and len(opts["activities"]) > 0
    print(f"  -> Fetched {len(opts['villages'])} villages and {len(opts['activities'])} activities for Web Wizard.")
    
    # 2. Test Direct DocType Creation and Validation
    survey = frappe.get_doc({
        "doctype": "Feedback Survey",
        "village": "Rampur",
        "date_of_visit": "2024-05-20",
        "field_officer": "Administrator",
        "activity": "Kitchen Garden Initiative",
        "respondent_type": "Community Member",
        "total_participants": 45,
        "households_involved": 32,
        "sessions_conducted": 4,
        "adoption_percentage": 78.0,
        "outputs_achieved": "45 Seed Kits & 30 Compost Kits distributed",
        "significant_change": "Families harvesting fresh greens daily.",
        "community_voice": "Earlier we had to travel 7km to buy vegetables.",
        "barriers_challenges": "Minor water scarcity in lower hamlet.",
        "facilitator_observations": "Women SHG members showed great ownership.",
        "overall_rating": "5",
        "confirmation_accuracy": 1
    }).insert(ignore_permissions=True)
    
    assert survey.name.startswith("FS-")
    assert survey.submission_status == "Draft"
    print(f"  -> Created Feedback Survey Doc: {survey.name}")
    
    # 3. Test Submit
    survey.submit()
    survey.reload()
    assert survey.docstatus == 1
    assert survey.submission_status == "Submitted"
    print("  -> Survey submitted and validated successfully.")
    
    # 4. Test Submission via Whitelisted Web API
    api_res = submit_feedback_survey({
        "village": "Sonapur",
        "date_of_visit": "2024-05-21",
        "field_officer": "Administrator",
        "activity": "Drip Irrigation Demonstration",
        "respondent_type": "Farmer",
        "total_participants": 20,
        "adoption_percentage": 85.0,
        "significant_change": "Water usage cut down by half with drip systems.",
        "overall_rating": "4",
        "confirmation_accuracy": True,
        "submit_now": True
    })
    
    assert api_res["success"] is True
    assert api_res["name"].startswith("FS-")
    print(f"  -> Web Wizard API submission successful: {api_res['name']}")
    
    # 5. Test Analytics API
    analytics = get_feedback_analytics()
    assert analytics["total_surveys"] >= 2
    assert analytics["avg_rating"] >= 4.0
    print(f"  -> Aggregated Feedback Analytics: Avg Rating = {analytics['avg_rating']}, Total Reached = {analytics['total_participants']}")

def test_village_profile_lifecycle(company):
    print("\n[Test 6] Testing Village Profile DocType, Validations, and Submission API...")
    from krushi_vikas.api import submit_village_profile, get_village_profile_options, get_village_profiles_list

    # 1. Test Options API
    opts = get_village_profile_options()
    assert "districts" in opts and len(opts["districts"]) > 0
    assert "soil_types" in opts and len(opts["soil_types"]) > 0
    print(f"  -> Fetched {len(opts['districts'])} districts and {len(opts['soil_types'])} soil types for Village Profile.")

    # 2. Test Direct DocType Creation and Validation
    profile = frappe.get_doc({
        "doctype": "Village Profile",
        "village_name": "Rampur",
        "village_code": "MH-AKL-001",
        "gram_panchayat": "Rampur Gram Panchayat",
        "block_taluka": "Akot",
        "district": "Akola",
        "state": "Maharashtra",
        "pincode": "444101",
        "field_officer": "Administrator",
        "date_of_survey": "2024-05-20",
        "total_population": 1450,
        "male_population": 740,
        "female_population": 710,
        "total_households": 280,
        "sc_households": 45,
        "st_households": 30,
        "bpl_households": 85,
        "female_headed_households": 18,
        "literacy_rate_pct": 74.5,
        "total_geographical_area_ha": 520.0,
        "cultivable_land_ha": 420.0,
        "irrigated_area_ha": 130.0,
        "rainfed_area_ha": 290.0,
        "forest_wasteland_ha": 100.0,
        "marginal_farmers_count": 95,
        "small_farmers_count": 80,
        "medium_large_farmers_count": 45,
        "landless_households_count": 60,
        "soil_type": "Medium Black Soil",
        "watershed_name": "Manjara Sub-basin Watershed",
        "primary_drinking_water_source": "GP Piped Water Supply",
        "summer_water_scarcity_status": "Moderate Scarcity",
        "primary_irrigation_practice": "Mixed",
        "open_wells_count": 42,
        "borewells_count": 68,
        "check_dams_count": 3,
        "farm_ponds_count": 12,
        "total_shgs_count": 14,
        "active_fpos_count": 1,
        "has_primary_school": 1,
        "has_bank_csc": 1,
        "all_weather_road_connectivity": 1,
        "key_development_priorities": "Deepening of main drainage nalla and micro-irrigation expansion."
    }).insert(ignore_permissions=True)

    assert profile.name.startswith("VP-")
    assert profile.profile_status == "Draft"
    print(f"  -> Created Village Profile Doc: {profile.name} for {profile.village_name}")

    # 3. Test Submit
    profile.submit()
    profile.reload()
    assert profile.docstatus == 1
    assert profile.profile_status == "Verified"
    print("  -> Village Profile submitted and marked as Verified successfully.")

    # 4. Test Web Wizard API Submission
    api_res = submit_village_profile({
        "village_name": "Sonapur",
        "village_code": "MH-AKL-002",
        "gram_panchayat": "Sonapur Gram Panchayat",
        "block_taluka": "Telhara",
        "district": "Akola",
        "state": "Maharashtra",
        "total_population": 980,
        "total_households": 190,
        "total_geographical_area_ha": 380.0,
        "cultivable_land_ha": 310.0,
        "irrigated_area_ha": 90.0,
        "rainfed_area_ha": 220.0,
        "summer_water_scarcity_status": "Severe / Tanker Dependent",
        "key_development_priorities": "Urgent construction of 2 cement nalla bunds to alleviate summer water tanker dependency.",
        "submit_now": True
    })

    assert api_res["success"] is True
    assert api_res["name"].startswith("VP-")
    print(f"  -> Web Wizard Village Profile API submission successful: {api_res['name']} ({api_res['village_name']})")

    # 5. Test Listing API
    profiles_list = get_village_profiles_list()
    assert len(profiles_list) >= 2
    print(f"  -> Retrieved {len(profiles_list)} village profiles successfully!")



