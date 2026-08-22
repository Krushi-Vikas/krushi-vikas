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
    test_baseline_survey_lifecycle(company)
    test_project_activity_task_hierarchy(company)
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

def test_baseline_survey_lifecycle(company):
    print("\n[Test 7] Testing Baseline Survey DocType, Validations, and Submission API...")
    from krushi_vikas.api import submit_baseline_survey, get_baseline_survey_options

    # 1. Test Options API
    opts = get_baseline_survey_options()
    assert "villages" in opts and len(opts["villages"]) > 0
    assert "irrigation_sources" in opts and len(opts["irrigation_sources"]) > 0
    print(f"  -> Fetched {len(opts['villages'])} villages and {len(opts['irrigation_sources'])} irrigation sources.")

    # 2. Test Direct DocType Creation with All 11 PDF Child Tables
    survey = frappe.get_doc({
        "doctype": "Baseline Survey",
        "farmer_name": "Ramesh Tukaram Patil",
        "contact_number": "9823456789",
        "village": "Rampur",
        "survey_date": "2024-05-20",
        "field_officer": "Administrator",
        "category": "OBC",
        "house_type": "Pucca",
        "has_toilet": "Yes",
        "is_bpl": "No",
        "family_migrates": "No",
        "is_shg_member": "Yes",
        "shg_name": "Krushi Kranti Mahila Bachat Gat",
        "shg_has_loan": "Yes",
        "shg_business_started": "Yes",
        "shg_business_type": "Bio-fertilizer Unit",
        "total_landholding_acres": 3.5,
        "irrigated_land_acres": 1.5,
        "rainfed_land_acres": 2.0,
        "conducts_soil_testing": "Yes",
        "soil_testing_last_date": "May 2025",
        "fertilizer_as_per_recommendation": "Yes",
        "yield_increase_from_soil_test": "2 Qtl.",
        "produce_sorted_graded": "Yes",
        "practices_organic_farming": "Yes",
        "aware_govt_water_schemes": "Yes",
        "availed_water_scheme_benefits": "Yes",
        "participates_in_gpdp_water": "Yes",
        "has_village_water_committee": "Yes",
        "drinking_water_source": "Tap Water",
        "drinking_water_ownership": "Public",
        "functional_tap_scheme": "Yes",
        "scheme_regular_om": "Yes",
        "drinking_water_at_home": "Yes",
        "water_supply_days_week": "Daily",
        "water_supply_duration": "1 Hr+",
        "drinking_water_year_round": "Yes",
        "wsp_awareness": "Yes",
        "owns_livestock": "Yes",
        "cattle_shed_type": "Pucca",
        "milk_sale_channel": "Dairy",
        "confirmation_consent": 1,
        
        # 1. Household Members
        "household_members_table": [
            {"member_name": "Ramesh Patil", "relation": "Self", "gender": "Male", "age": 45, "occupation": "Agriculture", "annual_income": 120000},
            {"member_name": "Savitri Patil", "relation": "Spouse", "gender": "Female", "age": 40, "occupation": "Housework", "annual_income": 30000},
            {"member_name": "Ganesh Patil", "relation": "Son", "gender": "Male", "age": 18, "occupation": "Other", "annual_income": 0}
        ],
        # 2. Crops
        "crops_table": [
            {"season": "Kharif", "crop_name": "Soybean", "area_irrigated_acres": 1.5, "area_dryland_acres": 0.5, "yield_quintals": 14.0, "market_rate_per_qtl": 4500, "total_income": 63000, "cost_of_production": 18000},
            {"season": "Rabi", "crop_name": "Gram", "area_irrigated_acres": 1.0, "area_dryland_acres": 0.0, "yield_quintals": 8.0, "market_rate_per_qtl": 5000, "total_income": 40000, "cost_of_production": 10000}
        ],
        # 3. Irrigation Sources
        "irrigation_sources_table": [
            {"source_name": "Open Well", "quantity": 1, "depth_feet": 40.0, "water_availability_months": 8}
        ],
        # 4. Irrigation Equipment
        "irrigation_equipment_table": [
            {"equipment_name": "Electric Pump", "quantity_and_capacity": "1 unit (5 HP)"}
        ],
        # 5. Farm Conservation Works
        "farm_conservation_works_table": [
            {"structure_type": "Farm Bunding (Shet Bandh Bandisti)", "status": "Yes", "length_or_count": "300 meters", "implementing_dept": "Agriculture Dept", "is_maintained": "Yes"}
        ],
        # 6. Nullah Conservation Structures
        "nullah_conservation_structures_table": [
            {"structure_name": "Cement Nala Bund (CNB)", "count": 1, "dimensions": "15m x 2m", "scheme_name": "Jalyukt Shivar", "is_maintained": "Yes"}
        ],
        # 7. Livestock Details
        "livestock_table": [
            {"livestock_type": "Cow", "count": 2, "daily_milk_production_liters": 10.0, "domestic_use_liters": 2.0, "sale_liters": 8.0, "income_generated": 36000},
            {"livestock_type": "Goat / Sheep", "count": 4, "daily_milk_production_liters": 0, "income_generated": 12000}
        ],
        # 8. Assets
        "family_assets_table": [
            {"asset_description": "House", "quantity": 1, "estimated_value": 400000},
            {"asset_description": "Tractor", "quantity": 1, "estimated_value": 350000}
        ],
        # 9. Loans
        "loans_table": [
            {"loan_category": "Crop Loan (KCC)", "loan_amount": 100000, "current_outstanding": 80000, "bank_name": "State Bank of India"}
        ],
        # 10. Income
        "family_income_table": [
            {"income_source": "Agriculture / Farming", "monthly_amount": 12000, "annual_amount": 144000}
        ],
        # 11. Expenditure
        "family_expenditure_table": [
            {"expenditure_category": "Agriculture Operations", "monthly_amount": 5000, "annual_amount": 60000}
        ]
    }).insert(ignore_permissions=True)

    assert survey.name.startswith("BLS-")
    assert survey.household_members == 3
    assert survey.livestock_count == 6
    assert len(survey.household_members_table) == 3
    assert len(survey.crops_table) == 2
    assert len(survey.irrigation_sources_table) == 1
    assert len(survey.irrigation_equipment_table) == 1
    assert len(survey.farm_conservation_works_table) == 1
    assert len(survey.nullah_conservation_structures_table) == 1
    assert len(survey.livestock_table) == 2
    assert len(survey.family_assets_table) == 2
    assert len(survey.loans_table) == 1
    assert len(survey.family_income_table) == 1
    assert len(survey.family_expenditure_table) == 1

    survey.submit()
    assert survey.docstatus == 1
    print(f"  -> Created Baseline Survey Doc with all 11 PDF Child Tables: {survey.name} (Auto-calculated: {survey.household_members} members, {survey.livestock_count} animals)")
    print("  -> Baseline Survey submitted and validated successfully.")

    # 4. Test Web Wizard API Submission with Full PDF Tables
    api_res = submit_baseline_survey({
        "farmer_name": "Sunita Rahul Shinde",
        "contact_number": "9765432101",
        "village": "Sonapur",
        "total_landholding_acres": 3.0,
        "irrigated_land_acres": 1.5,
        "rainfed_land_acres": 1.5,
        "primary_irrigation_source": "Farm Pond",
        "confirmation_consent": True,
        "submit_now": True,
        "household_members_table": [
            {"member_name": "Sunita Shinde", "relation": "Self", "gender": "Female", "age": 38, "occupation": "Agriculture"},
            {"member_name": "Rahul Shinde", "relation": "Spouse", "gender": "Male", "age": 42, "occupation": "Agriculture"}
        ],
        "crops_table": [
            {"season": "Kharif", "crop_name": "Cotton", "area_irrigated_acres": 1.0, "area_dryland_acres": 0.0, "yield_quintals": 12.0, "market_rate_per_qtl": 6000, "total_income": 72000, "cost_of_production": 20000}
        ],
        "livestock_table": [
            {"livestock_type": "Buffalo", "count": 1, "daily_milk_production_liters": 8.0, "income_generated": 48000}
        ],
        "family_assets_table": [
            {"asset_description": "Other Farm Implements", "quantity": 1, "estimated_value": 35000}
        ],
        "loans_table": [
            {"loan_category": "Crop Loan (KCC)", "loan_amount": 50000, "current_outstanding": 30000, "bank_name": "Gramin Bank"}
        ],
        "family_income_table": [
            {"income_source": "Agriculture / Farming", "monthly_amount": 6000, "annual_amount": 72000}
        ],
        "family_expenditure_table": [
            {"expenditure_category": "Groceries & Household Expenses", "monthly_amount": 3000, "annual_amount": 36000}
        ]
    })

    assert api_res["success"] is True
    assert api_res["name"].startswith("BLS-")
    print(f"  -> Web Wizard Multi-Table Baseline API submission successful: {api_res['name']}")

    # 5. Test Direct Raw Nested Questionnaire JSON Submission
    raw_user_json_payload = {
        "organization_name": "Institute of Agriculture Development and Rural Training",
        "form_title": "Family Survey Form",
        "basic_information": {
            "1.head_of_family_name": "Anil Dagadu Shinde",
            "1.mobile_number": "9822334455",
            "2.village_name": "Rampur",
            "2.age": 48,
            "2.category": ["OBC"],
            "3.house_type": ["Pucca (Permanent)"],
            "4.has_toilet": ["Yes"],
            "5.is_below_poverty_line": ["No"],
            "6.is_migrated_from_village_for_livelihood": ["No"],
            "7.if_yes_migration_details": {"where": "", "duration_days_or_months": ""}
        },
        "family_details": {
            "8.family_members_list_table": [
                {"serial_no": 1, "name": "Anil Shinde", "gender": "Male", "age": 48, "education": "Graduate", "occupation": "Agriculture"},
                {"serial_no": 2, "name": "Kavita Shinde", "gender": "Female", "age": 44, "education": "12th Pass", "occupation": "Household work"}
            ]
        },
        "self_help_group_shg_details": {
            "9.is_family_member_in_shg": ["Yes"],
            "10.if_yes_shg_name": "Pragati Mahila Bachat Gat",
            "11.if_yes_has_taken_loan_through_shg": ["Yes"],
            "12.if_loan_taken_has_started_business": ["Yes"],
            "13.type_of_business": "Goat Rearing"
        },
        "agricultural_details": {
            "14.total_land_acres": 4.5,
            "14.irrigated_land_acres": 2.5,
            "14.dryland_acres": 2.0,
            "15.do_you_conduct_soil_testing": ["Yes"],
            "15.when_was_last_soil_test_done": "May 2024",
            "16.were_fertilizer_doses_applied_according_to_soil_test": ["Yes"],
            "17.if_yes_increase_in_production": ["2 Quintals"],
            "18.is_agricultural_produce_sold_after_grading": ["Yes"],
            "19.source_of_modern_technology_information": ["Krishi Vigyan Kendra (KVK)"],
            "20.is_organic_fertilizer_adopted": ["Yes"],
            "20.crop_production_details_table": {
                "rows": [
                    {"season": "Kharif", "crop": "Soybean", "area_irrigated": 2.0, "area_dryland": 0.5, "production": 22.0, "place_of_sale": "APMC", "market_rate": 4800, "total_income": 105600, "production_cost": 28000, "profit": 77600},
                    {"season": "Vegetables (Bhaji Pala)", "crop": "Tomato", "area_irrigated": 0.5, "area_dryland": 0.0, "production": 50.0, "place_of_sale": "Local", "market_rate": 1500, "total_income": 75000, "production_cost": 20000, "profit": 55000}
                ]
            },
            "21.irrigation_details": {
                "sources_table": [
                    {"source": "Well (Vihir)", "count": 1, "depth": 45, "water_availability_months": 10}
                ],
                "equipment_table": [
                    {"equipment": "Electric Pump", "count_and_capacity_hp": "1 - 5 HP"}
                ]
            },
            "22.awareness_of_govt_water_schemes_e.g._PMKSY_Jalyukt_Shivar_Watershed": ["Yes"],
            "23.if_yes_benefited_from_water_structures_under_govt_schemes_e.g._well_repair_CNB_desilting": ["Yes"],
            "24.if_yes_soil_and_water_conservation_work_done_in_farm_table": [
                {"structure": "Farm Bunding (Shet Bandh Bandisti)", "done": ["Yes"], "length_or_count": "400 m", "department": "Agri Dept", "maintained": ["Yes"]}
            ],
            "25.participation_in_GP_PDP_Gram_Panchayat_Development_Plan_or_local_schemes_for_water_management": ["Yes"],
            "26.if_yes_type_of_participation": ["Suggesting development works in village"],
            "27.has_water_related_awareness_programs_e.g._Farmer_Exposure_Visit_IEC_happened_in_village": ["Yes"],
            "28.is_there_a_stream_or_rivulet_nala_odha_near_your_farm": ["Yes"],
            "29.if_yes_has_soil_and_water_conservation_work_been_done_on_it": ["Yes"],
            "30.if_yes_types_and_numbers_of_structures_table": [
                {"structure": "Cement Nala Bund (CNB)", "count": 1, "length_or_count": "15m", "scheme_name": "Jalyukt Shivar", "maintained": ["Yes"]}
            ]
        },
        "drinking_water_details": {
            "31.is_there_a_water_committee_Pani_Samiti_in_the_village": ["Yes"],
            "32.do_you_participate_in_village_water_supply_management": ["Yes"],
            "33.main_source_of_drinking_water": ["Tap (Nal)"],
            "34.type_of_drinking_water_source": ["Public"],
            "35.is_there_a_water_supply_scheme_tap_water_scheme_in_village": ["Yes"],
            "36.if_yes_is_maintenance_of_scheme_done_regularly": ["Yes"],
            "37.is_drinking_water_available_up_to_the_house": ["Yes"],
            "38.how_many_days_a_week_does_water_come": ["Daily"],
            "39.duration_of_water_supply_per_day": ["1 Hour"],
            "40.is_drinking_water_available_throughout_the_year": ["Yes"],
            "41.if_no_how_many_months_is_it_available": "",
            "42.how_is_water_supplied_in_remaining_months": ["Private Borewell"],
            "43.distance_traveled_to_fetch_drinking_water": ["Near House"],
            "44.awareness_of_Water_Security_Plan_for_ensuring_year-round_water": ["Yes"],
            "45.if_yes_source_of_information": ["Krishi Vigyan Kendra (KVK)"],
            "46.has_your_family_participated_in_preparing_village_Water_Security_Plan": ["Yes"],
            "47.if_yes_was_the_Water_Security_Plan_adopted_during_water_scarcity": ["Yes"],
            "48.practices_adopted_by_family_for_water_security_or_budgeting": ["Drip Irrigation"]
        },
        "livestock_details": {
            "49.does_family_own_livestock": ["Yes"],
            "50.if_yes_livestock_inventory_table": [
                {"livestock_type": "Cow (Gay)", "count": 2, "milk_production_per_day_liters": 12.0, "domestic_milk_consumption_liters": 2.0, "available_for_sale_liters": 10.0, "income_earned_INR": 42000},
                {"livestock_type": "Goat (Sheli)", "count": 5, "milk_production_per_day_liters": "NA", "domestic_milk_consumption_liters": 0, "available_for_sale_liters": 0, "income_earned_INR": 25000}
            ],
            "51.is_there_a_cowshed": ["Pucca (Permanent)"],
            "52.where_is_milk_sold": ["Dairy"]
        },
        "asset_details_table": {
            "53.assets_list": [
                {"sr_no": 1, "asset_name": "House", "count": 1, "estimated_value_INR": 500000},
                {"sr_no": 2, "asset_name": "T.V.", "count": 1, "estimated_value_INR": 18000},
                {"sr_no": 9, "asset_name": "Tractor", "count": 1, "estimated_value_INR": 600000}
            ]
        },
        "loan_details_table": {
            "54.loan_particulars": [
                {"sr_no": 1, "loan_type": "Crop Loan (Pik Karja)", "amount_INR": 120000, "current_status": "Active", "bank_name": "SBI"}
            ]
        },
        "income_and_expenditure_table": {
            "family_income": [
                {"source": "Agriculture (Sheti)", "monthly_income_INR": 18000, "annual_income_INR": 216000}
            ],
            "family_expenditure": [
                {"sr_no": 1, "category": "Agriculture (Sheti)", "monthly_expense_INR": 6000, "annual_expense_INR": 72000}
            ]
        },
        "other_necessary_information": "Participates actively in village water committee.",
        "signatures": {
            "name_of_surveyor_questionnaire_filler": "Field Officer Sunil",
            "signature_of_family_head": "Anil Shinde"
        }
    }

    raw_api_res = submit_baseline_survey(raw_user_json_payload)
    assert raw_api_res["success"] is True
    assert raw_api_res["name"].startswith("BLS-")
    print(f"  -> Successfully verified and inserted Direct User JSON Payload into Baseline Survey: {raw_api_res['name']}")

    # 6. Test Excel/CSV Export
    from krushi_vikas.api import export_baseline_survey_excel
    export_baseline_survey_excel(survey.name)
    assert frappe.response.get("type") == "csv"
    assert "AGRICULTURAL DEVELOPMENT AND RURAL TRAINING INSTITUTE" in frappe.response.get("result", "")
    print(f"  -> Verified Excel/CSV multi-table export structure for {survey.name}")


def test_project_activity_task_hierarchy(company):
    print("\n[Test 8] Testing Project, Activity & Task 3-Tier Hierarchy with Financial Tracking...")
    
    # 1. Ensure Theme
    theme_name = None
    existing_themes = frappe.get_all("Project Theme", limit=1)
    if existing_themes:
        theme_name = existing_themes[0].name
    else:
        td = frappe.get_doc({
            "doctype": "Project Theme",
            "theme_name": "Watershed & Water Security",
            "is_group": 0
        }).insert(ignore_permissions=True)
        theme_name = td.name
        
    # 2. Ensure Sample Baseline Survey & Field Tracking Form
    baseline = frappe.get_all("Baseline Survey", limit=1)
    baseline_name = baseline[0].name if baseline else None
    
    feedback = frappe.get_all("Feedback Survey", limit=1)
    feedback_name = feedback[0].name if feedback else None

    # 3. Create Project with logical grouping of fields
    proj = frappe.get_doc({
        "doctype": "Project",
        "project_name": "Jal Sanjivani Watershed Project",
        "company": company,
        "custom_project_phase": "Execution",
        "custom_thematic_area": theme_name,
        "custom_project_coordinator": "Administrator",
        "custom_project_manager": "Administrator",
        "expected_start_date": "2026-01-01",
        "expected_end_date": "2026-12-31",
        "custom_budget": 1500000.0,
        "custom_actual_amount_spent": 0.0,
        "custom_linked_baseline_survey": baseline_name,
        "custom_linked_field_tracking_form": feedback_name
    }).insert(ignore_permissions=True)

    goal_name = "Increase Village Water Retention by 50%"
    goal = frappe.get_doc({
        "doctype": "Project Goal",
        "goal_name": goal_name,
        "project": proj.name,
        "company": company,
        "theme": theme_name,
        "weightage": 100
    }).insert(ignore_permissions=True)

    # 4. Add Activities to Project
    proj.append("custom_activities", {
        "activity_name": "Community Water Budgeting & Jal Parishad",
        "goal": goal.name,
        "description": "Conduct water security planning sessions with farmers",
        "assignee": "Administrator",
        "timeline": "Jan 2026 - Mar 2026",
        "input_output": "10 training kits / 1 Village Water Budget",
        "impact": "100% household participation in water conservation",
        "status": "In Progress"
    })
    proj.append("custom_activities", {
        "activity_name": "Construction of 5 Continuous Contour Trenches (CCT)",
        "goal": goal.name,
        "description": "Excavation and bunding on hillside slopes",
        "assignee": "Administrator",
        "timeline": "Apr 2026 - Jun 2026",
        "input_output": "Excavation equipment / 500 meters of trenches",
        "impact": "50,000 liters groundwater recharge per rain event",
        "status": "Planned"
    })
    proj.save(ignore_permissions=True)
    
    print(f"  -> Created Project: {proj.name} ({proj.project_name})")
    assert proj.custom_remaining_funds == 1500000.0, f"Expected 1500000.0, got {proj.custom_remaining_funds}"
    print(f"  -> Initial Remaining Funds: Rs. {proj.custom_remaining_funds} (Budget: {proj.custom_budget} - Spent: {proj.custom_actual_amount_spent})")

    # 4. Verify Activity records automatically created / synchronized
    activities = frappe.get_all("Activity", filters={"project": proj.name}, fields=["name", "activity_name", "status", "timeline_description", "impact", "input_output"])
    assert len(activities) >= 2, f"Expected at least 2 activities, found {len(activities)}"
    print(f"  -> Verified {len(activities)} Activity DocType records synchronized from Project Activity child table:")
    for act in activities:
        print(f"     [+] Activity Doc: {act.name} | Name: '{act.activity_name}' | Status: {act.status} | Impact: '{act.impact}'")

    # 5. Create Tasks under the Activity (3-tier hierarchy: Project -> Activity -> Task)
    first_act = activities[0]
    task1 = frappe.get_doc({
        "doctype": "Task",
        "subject": "Organize Jal Parishad Farmer Community Gathering",
        "project": proj.name,
        "custom_activity": first_act.name,
        "company": company,
        "custom_project_phase": "Execution",
        "status": "Open"
    }).insert(ignore_permissions=True)

    task2 = frappe.get_doc({
        "doctype": "Task",
        "subject": "Publish Village Water Budget Balance Sheet",
        "project": proj.name,
        "custom_activity": first_act.name,
        "company": company,
        "custom_project_phase": "Execution",
        "status": "Open"
    }).insert(ignore_permissions=True)

    print(f"  -> Verified Hierarchy (Tier 1: Project {proj.name} -> Tier 2: Activity {first_act.name} -> Tier 3: Tasks {task1.name}, {task2.name})")

    # 6. Project Coordinator updates Actual Amount Spent
    proj.custom_actual_amount_spent = 425000.0
    proj.save(ignore_permissions=True)
    proj.reload()
    assert proj.custom_remaining_funds == 1075000.0, f"Expected 1075000.0, got {proj.custom_remaining_funds}"
    print(f"  -> Project Coordinator updated Actual Spent to Rs. {proj.custom_actual_amount_spent}. Auto-calculated Remaining Funds: Rs. {proj.custom_remaining_funds} (Budget: {proj.custom_budget} - Spent: {proj.custom_actual_amount_spent})")
    
    # 7. Test Dedicated KV Project Web Form API
    from krushi_vikas.api import get_project_form_options, submit_kv_project
    opts = get_project_form_options()
    assert "users" in opts and "themes" in opts
    print(f"  -> Fetched Web Form Options successfully ({len(opts['users'])} users, {len(opts['themes'])} themes).")

    kvp_res = submit_kv_project({
        "project_name": "Drone Didi Agricultural Fleet Project",
        "theme": theme_name,
        "project_coordinator": "Administrator",
        "project_manager": "Administrator",
        "project_phase": "Execution",
        "status": "Deployed",
        "start_date": "2026-02-01",
        "end_date": "2026-11-30",
        "budget": 2500000.0,
        "actual_amount_spent": 800000.0,
        "linked_baseline_survey": baseline_name,
        "linked_field_tracking_form": feedback_name,
        "activities": [
            {
                "activity_name": "Drone Procurement & Calibration",
                "goal": "Equip 10 SHG women with agricultural spraying drones",
                "assignee": "Administrator",
                "start_date": "2026-02-01",
                "end_date": "2026-04-30",
                "input_output": "10 Drone Kits ready",
                "impact": "1000 acres crop coverage per season",
                "status": "Completed"
            }
        ]
    })
    assert kvp_res["success"] is True
    assert kvp_res["name"].startswith("KVP-")
    assert kvp_res["remaining_funds"] == 1700000.0
    print(f"  -> Submitted KV Project Web Form successfully: {kvp_res['name']} ({kvp_res['project_name']}) | Remaining Funds: Rs. {kvp_res['remaining_funds']}")

    # 8. Test Modifying Activity and adding Tasks via child table
    act_to_modify = frappe.get_doc("Activity", first_act.name)
    act_to_modify.append("tasks", {
        "subject": "Community Water Quality Testing via Jal Kit",
        "status": "Open",
        "priority": "High",
        "exp_start_date": "2026-02-15",
        "exp_end_date": "2026-03-15",
        "description": "Test fluoride and nitrate levels across 10 open wells."
    })
    act_to_modify.save(ignore_permissions=True)
    act_to_modify.reload()
    
    # Verify the new task was created in Task DocType and linked back
    linked_task_id = act_to_modify.tasks[-1].linked_task
    assert linked_task_id is not None, "Expected new Task record to be created and linked"
    created_task = frappe.get_doc("Task", linked_task_id)
    assert created_task.subject == "Community Water Quality Testing via Jal Kit"
    assert created_task.custom_activity == act_to_modify.name
    # 9. Test Feedback Survey presence inside KV Project
    kvp_doc = frappe.get_doc("KV Project", kvp_res["name"])
    assert kvp_doc.linked_field_tracking_form == feedback_name
    print(f"  -> Verified Structural Form linkage in KV Project: Linked Feedback Survey = {kvp_doc.linked_field_tracking_form}")
    
    # Link a feedback survey to this project and check table reload
    frappe.db.set_value("Feedback Survey", feedback_name, "project", kvp_doc.name)
    kvp_doc.onload()
    assert len(kvp_doc.feedback_surveys) > 0, "Expected feedback survey to be loaded inside KV Project"
    print(f"  -> Verified Feedback Surveys child table inside KV Project ({len(kvp_doc.feedback_surveys)} survey(s) found: {kvp_doc.feedback_surveys[0].feedback_survey})")
    print("  -> Project, Activity & Task 3-tier hierarchy and financial tracking validated successfully!")










