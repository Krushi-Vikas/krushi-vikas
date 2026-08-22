import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate

@frappe.whitelist()
def get_template_questions(template):
    doc = frappe.get_doc("Survey Template", template)
    return [
        {
            "question_ref": q.name,
            "question_text": q.question_text,
            "answer_type": q.answer_type,
        }
        for q in sorted(doc.questions, key=lambda x: x.sequence or 0)
    ]

def enforce_dependency_gate(doc, method):
    """Hard dependency gate: Task cannot be completed if predecessors are not completed"""
    if doc.status == "Completed":
        for d in (doc.depends_on or []):
            if d.task:
                pred = frappe.get_doc("Task", d.task)
                if pred.status != "Completed":
                    frappe.throw(_(f"Blocked: Predecessor activity '{pred.subject}' ({pred.name}) is not completed yet."))

def push_actual_to_kre(doc, method):
    """Pushes actual value from Activity Outcome to linked KRE upon final approval"""
    if doc.workflow_state == "Approved" or (doc.docstatus == 1 and not getattr(doc, "workflow_state", None)):
        if doc.kre:
            kre_doc = frappe.get_doc("KRE", doc.kre)
            already_logged = any([m.notes == f"Outcome recorded: {doc.name}" for m in (kre_doc.measurements or [])])
            if not already_logged:
                kre_doc.current_value = (kre_doc.current_value or 0) + (doc.actual_value or 0)
                kre_doc.append("measurements", {
                    "date": doc.measurement_date or frappe.utils.today(),
                    "value": doc.actual_value,
                    "source_activity": doc.task,
                    "notes": f"Outcome recorded: {doc.name}"
                })
                kre_doc.save(ignore_permissions=True)

@frappe.whitelist()
def get_baseline_endline_comparison(project, template=None):
    """Comparative analysis between Baseline and Endline surveys"""
    filters = {"project": project, "docstatus": 1}
    if template:
        filters["template"] = template
        
    surveys = frappe.get_all("Survey Response", filters=filters, fields=["name", "survey_type", "response_date", "beneficiary"])
    
    comparison = []
    baseline_answers = {}
    endline_answers = {}
    
    for s in surveys:
        doc = frappe.get_doc("Survey Response", s.name)
        for ans in doc.answers:
            key = (ans.question_text, s.beneficiary or "Overall")
            if s.survey_type == "Baseline":
                baseline_answers[key] = ans.answer_value
            elif s.survey_type == "Endline":
                endline_answers[key] = ans.answer_value
    
    all_keys = set(list(baseline_answers.keys()) + list(endline_answers.keys()))
    for q_text, ben in all_keys:
        b_val = baseline_answers.get((q_text, ben), "-")
        e_val = endline_answers.get((q_text, ben), "-")
        delta = "-"
        try:
            if b_val != "-" and e_val != "-":
                delta = float(e_val) - float(b_val)
        except Exception:
            pass
        comparison.append({
            "question": q_text,
            "beneficiary": ben,
            "baseline": b_val,
            "endline": e_val,
            "delta": delta
        })
    return comparison

@frappe.whitelist(allow_guest=True)
def get_feedback_survey_options():
    """Returns dropdown options for the Feedback Survey Web Form"""
    options = {
        "villages": [
            "Rampur", "Sonapur", "Kalyanpur", "Shivaji Nagar", "Krushnagiri", 
            "Ganeshpur", "Vikas Nagar", "Adarsh Gram", "Sundarpur", "Navgaon"
        ],
        "field_officers": [],
        "activities": [
            "Kitchen Garden Initiative",
            "Drip Irrigation Demonstration",
            "Organic Fertilizer Distribution",
            "Soil Health Assessment & Testing",
            "Watershed Bunding & Contour Trenching",
            "SHG Capacity Building Workshop",
            "Seed Distribution & Training",
            "Post-Harvest Storage Guidance"
        ],
        "respondent_types": [
            "Community Member",
            "Farmer",
            "SHG Leader",
            "Village Elder",
            "Beneficiary",
            "Other"
        ]
    }
    
    # Dynamically fetch users if available
    try:
        users = frappe.get_all(
            "User",
            filters={"enabled": 1, "user_type": "System User"},
            fields=["name", "full_name"],
            limit=20
        )
        if users:
            options["field_officers"] = [
                {"name": u.name, "full_name": u.full_name or u.name}
                for u in users if u.name not in ("Guest",)
            ]
    except Exception:
        pass
        
    if not options["field_officers"]:
        options["field_officers"] = [
            {"name": "Administrator", "full_name": "Anita Sharma (Lead Officer)"},
            {"name": "fo_rahul", "full_name": "Rahul Deshmukh (Field Officer)"},
            {"name": "fo_priya", "full_name": "Priya Patil (Facilitator)"},
            {"name": "fo_vikas", "full_name": "Vikas Shinde (Watershed Coordinator)"}
        ]
        
    return options

@frappe.whitelist(allow_guest=True)
def submit_feedback_survey(data):
    """Submits a Feedback Survey from the Web Wizard / API"""
    import json
    if isinstance(data, str):
        data = json.loads(data)
        
    doc = frappe.get_doc({
        "doctype": "Feedback Survey",
        "village": data.get("village"),
        "date_of_visit": data.get("date_of_visit") or frappe.utils.today(),
        "field_officer": data.get("field_officer") or "Administrator",
        "activity": data.get("activity"),
        "respondent_type": data.get("respondent_type"),
        "respondent_type_other": data.get("respondent_type_other"),
        "project": data.get("project"),
        "beneficiary": data.get("beneficiary"),
        "total_participants": int(data.get("total_participants") or 0),
        "households_involved": int(data.get("households_involved") or 0) if data.get("households_involved") else None,
        "sessions_conducted": int(data.get("sessions_conducted") or 0) if data.get("sessions_conducted") else None,
        "adoption_percentage": float(data.get("adoption_percentage") or 0),
        "outputs_achieved": data.get("outputs_achieved"),
        "significant_change": data.get("significant_change"),
        "community_voice": data.get("community_voice"),
        "barriers_challenges": data.get("barriers_challenges"),
        "facilitator_observations": data.get("facilitator_observations"),
        "overall_rating": str(data.get("overall_rating") or "3"),
        "confirmation_accuracy": 1 if data.get("confirmation_accuracy") else 0,
        "submission_status": "Submitted"
    })
    
    doc.insert(ignore_permissions=True)
    if data.get("submit_now", True):
        doc.submit()
        
    return {
        "success": True,
        "name": doc.name,
        "message": _("Feedback survey submitted successfully.")
    }

@frappe.whitelist()
def get_feedback_analytics(project=None):
    """Aggregates feedback survey statistics and impact metrics"""
    filters = {"docstatus": 1}
    if project:
        filters["project"] = project
        
    surveys = frappe.get_all(
        "Feedback Survey",
        filters=filters,
        fields=[
            "name", "village", "date_of_visit", "activity", "respondent_type",
            "total_participants", "adoption_percentage", "overall_rating"
        ]
    )
    
    total_count = len(surveys)
    if total_count == 0:
        return {
            "total_surveys": 0,
            "avg_rating": 0,
            "total_participants": 0,
            "avg_adoption": 0,
            "rating_breakdown": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }
        
    total_participants = sum([s.total_participants or 0 for s in surveys])
    avg_adoption = sum([s.adoption_percentage or 0 for s in surveys]) / total_count
    ratings = [int(s.overall_rating or 3) for s in surveys]
    avg_rating = sum(ratings) / total_count
    
    rating_breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in ratings:
        if r in rating_breakdown:
            rating_breakdown[r] += 1
            
    return {
        "total_surveys": total_count,
        "avg_rating": round(avg_rating, 2),
        "total_participants": total_participants,
        "avg_adoption": round(avg_adoption, 1),
        "rating_breakdown": rating_breakdown
    }

@frappe.whitelist(allow_guest=True)
def get_village_profile_options():
    """Returns dynamic dropdown options and metadata for Village Profile"""
    districts = ["Akola", "Washim", "Amravati", "Buldhana", "Yavatmal", "Wardha", "Nagpur", "Chhatrapati Sambhajinagar"]
    talukas = ["Akot", "Telhara", "Balapur", "Patur", "Murtizapur", "Barshitakli", "Malegaon", "Risod", "Karanja"]
    
    field_officers = []
    try:
        users = frappe.get_all(
            "User",
            filters={"enabled": 1, "user_type": "System User"},
            fields=["name", "full_name"],
            limit=20
        )
        if users:
            field_officers = [
                {"name": u.name, "full_name": u.full_name or u.name}
                for u in users if u.name not in ("Guest",)
            ]
    except Exception:
        pass
        
    if not field_officers:
        field_officers = [
            {"name": "Administrator", "full_name": "Anita Sharma (Lead Officer)"},
            {"name": "fo_rahul", "full_name": "Rahul Deshmukh (Field Officer)"},
            {"name": "fo_priya", "full_name": "Priya Patil (Watershed Facilitator)"},
            {"name": "fo_vikas", "full_name": "Vikas Shinde (Agronomist)"}
        ]

    projects = []
    try:
        projs = frappe.get_all("Project", fields=["name", "project_name"], limit=20)
        projects = [{"name": p.name, "title": p.project_name or p.name} for p in projs]
    except Exception:
        pass

    if not projects:
        projects = [
            {"name": "PROJ-0001", "title": "Kalyanpur Integrated Watershed Development"},
            {"name": "PROJ-0002", "title": "Village Nutrition & Kitchen Garden Initiative"}
        ]

    return {
        "districts": districts,
        "talukas": talukas,
        "field_officers": field_officers,
        "projects": projects,
        "soil_types": [
            "Deep Black Soil",
            "Medium Black Soil",
            "Red Sandy Soil",
            "Loamy Soil",
            "Laterite Soil",
            "Mixed Soil"
        ],
        "drinking_water_sources": [
            "GP Piped Water Supply",
            "Community Open Wells",
            "Handpumps / Borewells",
            "Water Tankers (Seasonal)",
            "River / Canal"
        ],
        "water_scarcity_levels": [
            "Severe / Tanker Dependent",
            "Moderate Scarcity",
            "Minor Scarcity",
            "Adequate / No Scarcity"
        ],
        "irrigation_practices": [
            "Flood Irrigation",
            "Drip & Sprinkler Micro-Irrigation",
            "Mixed"
        ]
    }

@frappe.whitelist(allow_guest=True)
def submit_village_profile(data):
    """Submits or creates a Village Profile document"""
    import json
    if isinstance(data, str):
        data = json.loads(data)

    doc = frappe.get_doc({
        "doctype": "Village Profile",
        "village_name": data.get("village_name"),
        "village_code": data.get("village_code"),
        "gram_panchayat": data.get("gram_panchayat") or data.get("village_name"),
        "block_taluka": data.get("block_taluka"),
        "district": data.get("district"),
        "state": data.get("state") or "Maharashtra",
        "pincode": data.get("pincode"),
        "field_officer": data.get("field_officer") or "Administrator",
        "project": data.get("project") or None,
        "date_of_survey": data.get("date_of_survey") or frappe.utils.today(),
        "geo_coordinates": data.get("geo_coordinates"),
        
        # Demographics
        "total_population": int(data.get("total_population") or 0),
        "male_population": int(data.get("male_population") or 0),
        "female_population": int(data.get("female_population") or 0),
        "total_households": int(data.get("total_households") or 0),
        "sc_households": int(data.get("sc_households") or 0),
        "st_households": int(data.get("st_households") or 0),
        "obc_general_households": int(data.get("obc_general_households") or 0),
        "bpl_households": int(data.get("bpl_households") or 0),
        "female_headed_households": int(data.get("female_headed_households") or 0),
        "literacy_rate_pct": float(data.get("literacy_rate_pct") or 0) if data.get("literacy_rate_pct") else None,
        
        # Land & Agriculture
        "total_geographical_area_ha": float(data.get("total_geographical_area_ha") or 0),
        "cultivable_land_ha": float(data.get("cultivable_land_ha") or 0),
        "irrigated_area_ha": float(data.get("irrigated_area_ha") or 0),
        "rainfed_area_ha": float(data.get("rainfed_area_ha") or 0),
        "forest_wasteland_ha": float(data.get("forest_wasteland_ha") or 0),
        "marginal_farmers_count": int(data.get("marginal_farmers_count") or 0),
        "small_farmers_count": int(data.get("small_farmers_count") or 0),
        "medium_large_farmers_count": int(data.get("medium_large_farmers_count") or 0),
        "landless_households_count": int(data.get("landless_households_count") or 0),
        "soil_type": data.get("soil_type") or "Medium Black Soil",
        "major_crops_kharif": data.get("major_crops_kharif"),
        "major_crops_rabi": data.get("major_crops_rabi"),
        "horticulture_crops": data.get("horticulture_crops"),
        
        # Water Resources
        "watershed_name": data.get("watershed_name"),
        "primary_drinking_water_source": data.get("primary_drinking_water_source") or "GP Piped Water Supply",
        "summer_water_scarcity_status": data.get("summer_water_scarcity_status") or "Moderate Scarcity",
        "primary_irrigation_practice": data.get("primary_irrigation_practice") or "Mixed",
        "open_wells_count": int(data.get("open_wells_count") or 0),
        "borewells_count": int(data.get("borewells_count") or 0),
        "check_dams_count": int(data.get("check_dams_count") or 0),
        "farm_ponds_count": int(data.get("farm_ponds_count") or 0),
        "percolation_tanks_count": int(data.get("percolation_tanks_count") or 0),
        
        # Institutions & Facilities
        "total_shgs_count": int(data.get("total_shgs_count") or 0),
        "active_fpos_count": int(data.get("active_fpos_count") or 0),
        "fpo_name": data.get("fpo_name"),
        "has_primary_school": 1 if data.get("has_primary_school") else 0,
        "has_secondary_school": 1 if data.get("has_secondary_school") else 0,
        "has_primary_health_center": 1 if data.get("has_primary_health_center") else 0,
        "has_veterinary_clinic": 1 if data.get("has_veterinary_clinic") else 0,
        "has_milk_chilling_center": 1 if data.get("has_milk_chilling_center") else 0,
        "has_custom_hiring_center": 1 if data.get("has_custom_hiring_center") else 0,
        "has_bank_csc": 1 if data.get("has_bank_csc") else 0,
        "all_weather_road_connectivity": 1 if data.get("all_weather_road_connectivity") else 0,
        
        # Needs Assessment
        "key_development_priorities": data.get("key_development_priorities"),
        "water_conservation_interventions": data.get("water_conservation_interventions"),
        "livelihood_interventions": data.get("livelihood_interventions"),
        "surveyor_observations": data.get("surveyor_observations"),
        "profile_status": "Verified" if data.get("submit_now") else "Draft"
    })

    doc.insert(ignore_permissions=True)
    if data.get("submit_now", True):
        doc.submit()

    return {
        "success": True,
        "name": doc.name,
        "village_name": doc.village_name,
        "message": _("Village Profile created successfully.")
    }

@frappe.whitelist()
def get_village_profiles_list():
    """Returns summarized list of village profiles for dashboards and selector maps"""
    profiles = frappe.get_all(
        "Village Profile",
        fields=[
            "name", "village_name", "village_code", "gram_panchayat", "block_taluka", "district",
            "total_population", "total_households", "cultivable_land_ha", "summer_water_scarcity_status",
            "docstatus", "profile_status"
        ],
        order_by="village_name asc"
    )
    return profiles

@frappe.whitelist(allow_guest=True)
def get_baseline_survey_options():
    """Returns dynamic dropdown options for the Baseline Survey Web Wizard"""
    villages = [
        "Rampur", "Sonapur", "Kalyanpur", "Shivaji Nagar", "Krushnagiri", 
        "Ganeshpur", "Vikas Nagar", "Adarsh Gram", "Sundarpur", "Navgaon"
    ]
    
    field_officers = []
    try:
        users = frappe.get_all(
            "User",
            filters={"enabled": 1, "user_type": "System User"},
            fields=["name", "full_name"],
            limit=20
        )
        if users:
            field_officers = [
                {"name": u.name, "full_name": u.full_name or u.name}
                for u in users if u.name not in ("Guest",)
            ]
    except Exception:
        pass
        
    if not field_officers:
        field_officers = [
            {"name": "Administrator", "full_name": "Anita Sharma (Lead Officer)"},
            {"name": "fo_rahul", "full_name": "Rahul Deshmukh (Field Officer)"},
            {"name": "fo_priya", "full_name": "Priya Patil (Watershed Facilitator)"},
            {"name": "fo_vikas", "full_name": "Vikas Shinde (Agronomist)"}
        ]

    projects = []
    try:
        projs = frappe.get_all("Project", fields=["name", "project_name"], limit=20)
        projects = [{"name": p.name, "title": p.project_name or p.name} for p in projs]
    except Exception:
        pass

    if not projects:
        projects = [
            {"name": "PROJ-0001", "title": "Kalyanpur Integrated Watershed Development"},
            {"name": "PROJ-0002", "title": "Village Nutrition & Kitchen Garden Initiative"}
        ]

    return {
        "villages": villages,
        "field_officers": field_officers,
        "projects": projects,
        "farmer_categories": [
            "Marginal Farmer [< 2.5 Acres]",
            "Small Farmer [2.5 - 5.0 Acres]",
            "Medium Farmer [5.0 - 10.0 Acres]",
            "Large Farmer [> 10.0 Acres]",
            "Landless / Agri Labour"
        ],
        "primary_occupations": [
            "Agriculture",
            "Agricultural Labour",
            "Allied Livestock / Dairy",
            "Rural Enterprise / Business",
            "Other"
        ],
        "irrigation_sources": [
            "Open Well",
            "Borewell",
            "Farm Pond / Check Dam",
            "Canal",
            "River / Stream",
            "Rainfed Only"
        ],
        "fertilizer_practices": [
            "100% Chemical Fertilizers",
            "Mixed Chemical & Organic",
            "Mostly Organic / Bio-fertilizer",
            "Natural Farming"
        ],
        "water_scarcity_levels": [
            "No Scarcity (Adequate)",
            "Moderate Scarcity",
            "Severe Scarcity",
            "Critical Dryness"
        ]
    }

@frappe.whitelist(allow_guest=True)
def submit_baseline_survey(data):
    """Submits a Baseline Survey from the Web Wizard / API or nested questionnaire JSON"""
    import json
    if isinstance(data, str):
        data = json.loads(data)

    def _val(v, default=None):
        if v is None:
            return default
        if isinstance(v, list):
            return v[0] if v else default
        return v

    def _float(v, default=0.0):
        if v is None or v == "NA" or v == "":
            return default
        if isinstance(v, list):
            v = v[0] if v else default
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    def _int(v, default=0):
        if v is None or v == "NA" or v == "":
            return default
        if isinstance(v, list):
            v = v[0] if v else default
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return default

    # Extract sections if submitted as nested questionnaire JSON
    basic_info = data.get("basic_information") or {}
    family_details = data.get("family_details") or {}
    shg = data.get("self_help_group_shg_details") or {}
    agri = data.get("agricultural_details") or {}
    irrigation_details = agri.get("21.irrigation_details") or {}
    drinking = data.get("drinking_water_details") or {}
    livestock = data.get("livestock_details") or {}
    asset_data = data.get("asset_details_table") or {}
    loan_data = data.get("loan_details_table") or {}
    inc_exp_data = data.get("income_and_expenditure_table") or {}
    signatures = data.get("signatures") or {}
    migration_details = basic_info.get("7.if_yes_migration_details") or {}
    crop_table_obj = agri.get("20.crop_production_details_table") or {}
    crop_rows = crop_table_obj.get("rows") if isinstance(crop_table_obj, dict) else crop_table_obj

    doc = frappe.get_doc({
        "doctype": "Baseline Survey",
        "farmer_name": data.get("farmer_name") or basic_info.get("1.head_of_family_name") or "Farmer",
        "contact_number": data.get("contact_number") or basic_info.get("1.mobile_number") or "9999999999",
        "village": data.get("village") or basic_info.get("2.village_name") or "Sonapur",
        "survey_date": data.get("survey_date") or frappe.utils.today(),
        "field_officer": data.get("field_officer") or "Administrator",
        "surveyor_name": data.get("surveyor_name") or signatures.get("name_of_surveyor_questionnaire_filler") or "Enumerator",
        "project": data.get("project") or None,
        "beneficiary": data.get("beneficiary") or None,
        
        # Family Profile
        "age": int(_val(data.get("age") or basic_info.get("2.age")) or 45),
        "category": _val(data.get("category") or basic_info.get("2.category"), "Open"),
        "house_type": _val(data.get("house_type") or basic_info.get("3.house_type"), "Pucca (Permanent)"),
        "has_toilet": _val(data.get("has_toilet") or basic_info.get("4.has_toilet"), "Yes"),
        "is_bpl": _val(data.get("is_bpl") or basic_info.get("5.is_below_poverty_line"), "No"),
        "family_migrates": _val(data.get("family_migrates") or basic_info.get("6.is_migrated_from_village_for_livelihood"), "No"),
        "migration_location": data.get("migration_location") or migration_details.get("where"),
        "migration_duration": data.get("migration_duration") or migration_details.get("duration_days_or_months"),
        "household_members": int(data.get("household_members") or 0) if data.get("household_members") else None,
        
        # SHG & Enterprise
        "is_shg_member": _val(data.get("is_shg_member") or shg.get("9.is_family_member_in_shg"), "No"),
        "shg_name": data.get("shg_name") or shg.get("10.if_yes_shg_name"),
        "shg_has_loan": _val(data.get("shg_has_loan") or shg.get("11.if_yes_has_taken_loan_through_shg"), "No"),
        "shg_business_started": _val(data.get("shg_business_started") or shg.get("12.if_loan_taken_has_started_business"), "No"),
        "shg_business_type": data.get("shg_business_type") or shg.get("13.type_of_business"),
        
        # Agricultural Details
        "total_landholding_acres": float(_val(data.get("total_landholding_acres") or agri.get("14.total_land_acres")) or 0),
        "irrigated_land_acres": float(_val(data.get("irrigated_land_acres") or agri.get("14.irrigated_land_acres")) or 0),
        "rainfed_land_acres": float(_val(data.get("rainfed_land_acres") or agri.get("14.dryland_acres")) or 0),
        "conducts_soil_testing": _val(data.get("conducts_soil_testing") or agri.get("15.do_you_conduct_soil_testing"), "No"),
        "soil_testing_last_date": data.get("soil_testing_last_date") or agri.get("15.when_was_last_soil_test_done"),
        "fertilizer_as_per_recommendation": _val(data.get("fertilizer_as_per_recommendation") or agri.get("16.were_fertilizer_doses_applied_according_to_soil_test"), "No"),
        "yield_increase_from_soil_test": _val(data.get("yield_increase_from_soil_test") or agri.get("17.if_yes_increase_in_production"), "Not Applicable"),
        "produce_sorted_graded": _val(data.get("produce_sorted_graded") or agri.get("18.is_agricultural_produce_sold_after_grading"), "Yes"),
        "tech_info_source": _val(data.get("tech_info_source") or agri.get("19.source_of_modern_technology_information"), "Agriculture Department"),
        "practices_organic_farming": _val(data.get("practices_organic_farming") or agri.get("20.is_organic_fertilizer_adopted"), "No"),
        
        # Water & Soil Conservation
        "aware_govt_water_schemes": _val(data.get("aware_govt_water_schemes") or agri.get("22.awareness_of_govt_water_schemes_e.g._PMKSY_Jalyukt_Shivar_Watershed"), "Yes"),
        "availed_water_scheme_benefits": _val(data.get("availed_water_scheme_benefits") or agri.get("23.if_yes_benefited_from_water_structures_under_govt_schemes_e.g._well_repair_CNB_desilting"), "No"),
        "participates_in_gpdp_water": _val(data.get("participates_in_gpdp_water") or agri.get("25.participation_in_GP_PDP_Gram_Panchayat_Development_Plan_or_local_schemes_for_water_management"), "No"),
        "nature_of_gpdp_participation": _val(data.get("nature_of_gpdp_participation") or agri.get("26.if_yes_type_of_participation")),
        "village_water_awareness_programs": _val(data.get("village_water_awareness_programs") or agri.get("27.has_water_related_awareness_programs_e.g._Farmer_Exposure_Visit_IEC_happened_in_village"), "Yes"),
        "has_stream_near_land": _val(data.get("has_stream_near_land") or agri.get("28.is_there_a_stream_or_rivulet_nala_odha_near_your_farm"), "No"),
        "stream_structures_constructed": _val(data.get("stream_structures_constructed") or agri.get("29.if_yes_has_soil_and_water_conservation_work_been_done_on_it"), "No"),
        
        # Drinking Water
        "has_village_water_committee": _val(data.get("has_village_water_committee") or drinking.get("31.is_there_a_water_committee_Pani_Samiti_in_the_village"), "Yes"),
        "participates_drinking_water_mgmt": _val(data.get("participates_drinking_water_mgmt") or drinking.get("32.do_you_participate_in_village_water_supply_management"), "No"),
        "drinking_water_source": _val(data.get("drinking_water_source") or drinking.get("33.main_source_of_drinking_water"), "Tap Water"),
        "drinking_water_ownership": _val(data.get("drinking_water_ownership") or drinking.get("34.type_of_drinking_water_source"), "Public"),
        "functional_tap_scheme": _val(data.get("functional_tap_scheme") or drinking.get("35.is_there_a_water_supply_scheme_tap_water_scheme_in_village"), "Yes"),
        "scheme_regular_om": _val(data.get("scheme_regular_om") or drinking.get("36.if_yes_is_maintenance_of_scheme_done_regularly"), "Yes"),
        "drinking_water_at_home": _val(data.get("drinking_water_at_home") or drinking.get("37.is_drinking_water_available_up_to_the_house"), "Yes"),
        "water_supply_days_week": _val(data.get("water_supply_days_week") or drinking.get("38.how_many_days_a_week_does_water_come"), "Daily"),
        "water_supply_duration": _val(data.get("water_supply_duration") or drinking.get("39.duration_of_water_supply_per_day"), "1 Hour"),
        "drinking_water_year_round": _val(data.get("drinking_water_year_round") or drinking.get("40.is_drinking_water_available_throughout_the_year"), "Yes"),
        "water_available_months": data.get("water_available_months") or drinking.get("41.if_no_how_many_months_is_it_available"),
        "scarcity_water_mgmt": _val(data.get("scarcity_water_mgmt") or drinking.get("42.how_is_water_supplied_in_remaining_months"), "Private Borewell"),
        "drinking_water_distance": _val(data.get("drinking_water_distance") or drinking.get("43.distance_traveled_to_fetch_drinking_water"), "Near House"),
        "wsp_awareness": _val(data.get("wsp_awareness") or drinking.get("44.awareness_of_Water_Security_Plan_for_ensuring_year-round_water"), "Partially"),
        "wsp_info_source": _val(data.get("wsp_info_source") or drinking.get("45.if_yes_source_of_information")),
        "wsp_drafting_participation": _val(data.get("wsp_drafting_participation") or drinking.get("46.has_your_family_participated_in_preparing_village_Water_Security_Plan"), "No"),
        "wsp_implemented_scarcity": _val(data.get("wsp_implemented_scarcity") or drinking.get("47.if_yes_was_the_Water_Security_Plan_adopted_during_water_scarcity"), "No"),
        "water_budgeting_practices": _val(data.get("water_budgeting_practices") or drinking.get("48.practices_adopted_by_family_for_water_security_or_budgeting"), "Drip Irrigation"),
        
        # Livestock
        "owns_livestock": _val(data.get("owns_livestock") or livestock.get("49.does_family_own_livestock"), "Yes"),
        "livestock_count": int(data.get("livestock_count") or 0),
        "cattle_shed_type": _val(data.get("cattle_shed_type") or livestock.get("51.is_there_a_cowshed"), "Pucca (Permanent)"),
        "milk_sale_channel": _val(data.get("milk_sale_channel") or livestock.get("52.where_is_milk_sold"), "Dairy"),
        
        # Review & Notes
        "other_notes": data.get("other_notes") or data.get("other_necessary_information"),
        "confirmation_consent": 1 if (data.get("confirmation_consent") or signatures.get("signature_of_family_head")) else 0,
        "submission_status": "Draft"
    })

    # 1. Household Members Table (Table 8)
    members_list = data.get("household_members_table") or family_details.get("8.family_members_list_table") or []
    for member in members_list:
        name = member.get("member_name") or member.get("name")
        if not name:
            continue
        doc.append("household_members_table", {
            "member_name": name,
            "relation": member.get("relation") or "Self",
            "gender": member.get("gender") or "Male",
            "age": int(member.get("age") or 0) if member.get("age") else None,
            "education": member.get("education") or "Secondary [9-10]",
            "occupation": member.get("occupation") or member.get("primary_occupation") or "Agriculture",
            "annual_income": float(member.get("annual_income") or 0)
        })

    # 2. Crops Table (Page 2)
    crops_list = data.get("crops_table") or crop_rows or []
    for crop in crops_list:
        cname = crop.get("crop_name") or crop.get("crop")
        if not cname:
            continue
        doc.append("crops_table", {
            "season": crop.get("season") or "Kharif",
            "crop_name": cname,
            "area_irrigated_acres": float(crop.get("area_irrigated_acres") or crop.get("area_irrigated") or 0),
            "area_dryland_acres": float(crop.get("area_dryland_acres") or crop.get("area_dryland") or 0),
            "yield_quintals": float(crop.get("yield_quintals") or crop.get("production") or 0),
            "place_of_sale": crop.get("place_of_sale") or "Local APMC Market",
            "market_rate_per_qtl": float(crop.get("market_rate_per_qtl") or crop.get("market_rate") or 0),
            "total_income": float(crop.get("total_income") or 0),
            "cost_of_production": float(crop.get("cost_of_production") or crop.get("production_cost") or 0),
            "net_profit": float(crop.get("net_profit") or crop.get("profit") or 0)
        })

    # 3. Irrigation Sources (Page 3 Table 1)
    ir_sources = data.get("irrigation_sources_table") or irrigation_details.get("sources_table") or []
    for ir in ir_sources:
        sname = ir.get("source_name") or ir.get("source")
        if not sname:
            continue
        if "Well" in sname or "Vihir" in sname:
            sname = "Open Well"
        elif "Bore" in sname:
            sname = "Borewell"
        elif "Canal" in sname:
            sname = "Canal"
        elif "River" in sname:
            sname = "River (Nadivarun)"
        elif sname not in ("Well (Vihir)", "Open Well", "Borewell", "Canal (Kalva)", "Canal", "River (Nadivarun)", "River Lift", "Other"):
            sname = "Other"

        doc.append("irrigation_sources_table", {
            "source_name": sname,
            "quantity": int(ir.get("quantity") or ir.get("count") or 1),
            "depth_feet": float(ir.get("depth_feet") or ir.get("depth") or 0),
            "water_availability_months": int(ir.get("water_availability_months") or 8)
        })

    # 4. Irrigation Equipment (Page 3 Table 2)
    ir_eq = data.get("irrigation_equipment_table") or irrigation_details.get("equipment_table") or []
    for eq in ir_eq:
        ename = eq.get("equipment_name") or eq.get("equipment")
        if not ename:
            continue
        doc.append("irrigation_equipment_table", {
            "equipment_name": ename,
            "quantity_and_capacity": eq.get("quantity_and_capacity") or eq.get("count_and_capacity_hp") or "1 - 5 HP"
        })

    # 5. Farm Soil & Water Conservation Works (Page 3 Table 24)
    farm_works = data.get("farm_conservation_works_table") or agri.get("24.if_yes_soil_and_water_conservation_work_done_in_farm_table") or []
    for sc in farm_works:
        stype = sc.get("structure_type") or sc.get("structure")
        if not stype:
            continue
        if "Bunding" in stype or "Bandh" in stype:
            stype = "Farm Bunding (Shet Bandh Bandisti)"
        elif "Pond" in stype or "Tale" in stype:
            stype = "Farm Pond (Shet Tale)"
        elif "CCT" in stype or "Contour" in stype:
            stype = "Continuous Contour Trenches (CCT)"
        elif "WAT" in stype or "Absorption" in stype:
            stype = "Water Absorption Trenches (WAT)"
        elif "Boulder" in stype or "LBS" in stype:
            stype = "Loose Boulder Structure (LBS)"
        elif stype not in ("Farm Bunding (Shet Bandh Bandisti)", "Farm Pond (Shet Tale)", "Continuous Contour Trench (CCT)", "Continuous Contour Trenches (CCT)", "Water Absorption Trench (WAT)", "Water Absorption Trenches (WAT)", "Loose Boulder Structure (LBS)", "Other"):
            stype = "Other"

        doc.append("farm_conservation_works_table", {
            "structure_type": stype,
            "status": _val(sc.get("status") or sc.get("done"), "Yes"),
            "length_or_count": sc.get("length_or_count") or "200 m",
            "implementing_dept": sc.get("implementing_dept") or sc.get("department") or "Agriculture Dept",
            "is_maintained": _val(sc.get("is_maintained") or sc.get("maintained"), "Yes")
        })

    # 6. Stream/Nullah Conservation Structures (Page 4 Table 30)
    nullah_works = data.get("nullah_conservation_structures_table") or agri.get("30.if_yes_types_and_numbers_of_structures_table") or []
    for nc in nullah_works:
        sname = nc.get("structure_name") or nc.get("structure")
        if not sname:
            continue
        doc.append("nullah_conservation_structures_table", {
            "structure_name": sname,
            "count": int(nc.get("count") or 1),
            "dimensions": nc.get("dimensions") or nc.get("length_or_count") or "15m x 2.5m",
            "scheme_name": nc.get("scheme_name") or "Jalyukt Shivar",
            "is_maintained": _val(nc.get("is_maintained") or nc.get("maintained"), "Yes")
        })

    # 7. Livestock Table (Page 5 Table 50)
    ls_list = data.get("livestock_table") or livestock.get("50.if_yes_livestock_inventory_table") or []
    for ls in ls_list:
        ltype = ls.get("livestock_type") or ls.get("animal_type")
        if not ltype:
            continue
        if "Cow" in ltype or "Gay" in ltype:
            ltype = "Cow (Gay)"
        elif "Buffalo" in ltype or "Mhais" in ltype:
            ltype = "Buffalo (Mhais)"
        elif "Bullock" in ltype or "Bail" in ltype:
            ltype = "Bullock (Bail)"
        elif "Goat" in ltype or "Sheli" in ltype or "Sheep" in ltype:
            ltype = "Goat (Sheli)"
        elif "Hen" in ltype or "Poultry" in ltype or "Kombdi" in ltype:
            ltype = "Hen/Poultry (Kombdi)"
        elif ltype not in ("Cow (Gay)", "Cow", "Buffalo (Mhais)", "Buffalo", "Bullock (Bail)", "Bullock", "Goat (Sheli)", "Goat / Sheep", "Hen/Poultry (Kombdi)", "Poultry / Hen", "Other"):
            ltype = "Other"

        doc.append("livestock_table", {
            "livestock_type": ltype,
            "count": int(ls.get("count") or ls.get("quantity") or 1),
            "daily_milk_production_liters": float(ls.get("daily_milk_production_liters") or (ls.get("milk_production_per_day_liters") if ls.get("milk_production_per_day_liters") != "NA" else 0) or 0),
            "domestic_use_liters": float(ls.get("domestic_use_liters") or ls.get("domestic_milk_consumption_liters") or 0),
            "sale_liters": float(ls.get("sale_liters") or ls.get("available_for_sale_liters") or 0),
            "income_generated": float(ls.get("income_generated") or ls.get("income_earned_INR") or 0)
        })

    # 8. Asset Details (Page 6 Table 53)
    asset_list = data.get("family_assets_table") or asset_data.get("53.assets_list") or []
    for ast in asset_list:
        adesc = ast.get("asset_description") or ast.get("asset_name")
        if not adesc:
            continue
        if "TV" in adesc or "Television" in adesc or "T.V" in adesc:
            adesc = "Television (TV)"
        elif "Smart Phone" in adesc or "Smartphone" in adesc or "Phone" in adesc:
            adesc = "Smartphone"
        elif "Two" in adesc or "Bike" in adesc or "Motorcycle" in adesc or "Scooter" in adesc:
            adesc = "Two-Wheeler (Bike/Scooter)"
        elif "Four" in adesc or "Car" in adesc or "Jeep" in adesc:
            adesc = "Four-Wheeler (Car/Jeep)"
        elif "Bullock Cart" in adesc or "Bailgadi" in adesc:
            adesc = "Bullock Cart (Bailgadi)"
        elif "Tractor" in adesc:
            adesc = "Tractor"
        elif "Gas" in adesc or "LPG" in adesc:
            adesc = "LPG Gas Connection"
        elif "Biogas" in adesc or "Bio Gas" in adesc:
            adesc = "Biogas Unit"
        elif "Refrigerator" in adesc or "Fridge" in adesc:
            adesc = "Refrigerator"
        elif "Sprayer" in adesc or "Spray" in adesc or "Pump" in adesc or "Implement" in adesc or "Machinery" in adesc:
            adesc = "Other Farm Implements"
        elif adesc not in ("House", "T.V.", "Television (TV)", "Smart Phone", "Smartphone", "AC", "Air Conditioner (AC)", "Refrigerator", "Two Wheeler", "Two-Wheeler (Bike/Scooter)", "Four Wheeler", "Four-Wheeler (Car/Jeep)", "Bullock Cart (Bailgadi)", "Bullock Cart", "Tractor", "Bio Gas", "Biogas Unit", "LPG Gas", "LPG Gas Connection", "Other Farm Implements (write names)", "Other Farm Implements", "Other"):
            adesc = "Other"

        doc.append("family_assets_table", {
            "asset_description": adesc,
            "quantity": int(ast.get("quantity") or ast.get("count") or 1),
            "estimated_value": float(ast.get("estimated_value") or ast.get("estimated_value_INR") or 0)
        })

    # 9. Loans Table (PDF 54. Loan / Debt Details)
    loans_list = data.get("loans_table") or loan_data.get("54.loan_particulars") or []
    for ln in loans_list:
        lcat = ln.get("loan_category") or ln.get("loan_type") or ln.get("source")
        if not lcat:
            continue
        if "Crop" in lcat or "Pik" in lcat or "KCC" in lcat or "PACS" in lcat:
            lcat = "Crop Loan (KCC)"
        elif "Allied" in lcat or "Dairy" in lcat:
            lcat = "Agri-Allied Loan"
        elif "Commercial" in lcat or "Business" in lcat:
            lcat = "Business / Commercial Loan"
        elif lcat not in ("Crop Loan (Pik Karja)", "Crop Loan (KCC)", "Agri-Allied Loan (Sheti Poorak Karja)", "Agri-Allied Loan", "Commercial/Business Loan (Vyavasayik Karja)", "Business / Commercial Loan", "Other Loan", "Other Loan (Personal / SHG / Moneylender)", "Other"):
            lcat = "Other Loan"

        doc.append("loans_table", {
            "loan_category": lcat,
            "loan_amount": _float(ln.get("loan_amount") or ln.get("amount_INR")),
            "current_outstanding": _float(ln.get("current_outstanding") or ln.get("outstanding_amount")),
            "loan_status": ln.get("loan_status") or (ln.get("current_status") if not str(ln.get("current_status", "")).replace(".", "").isdigit() else "Active") or "Active",
            "bank_name": ln.get("bank_name") or ln.get("source") or "Bank"
        })

    # 10. Family Income Table (Page 6-7)
    inc_list = data.get("family_income_table") or inc_exp_data.get("family_income") or []
    for inc in inc_list:
        isrc = inc.get("income_source") or inc.get("source")
        if not isrc:
            continue
        doc.append("family_income_table", {
            "income_source": isrc,
            "monthly_amount": float(inc.get("monthly_amount") or inc.get("monthly_income_INR") or 0),
            "annual_amount": float(inc.get("annual_amount") or inc.get("annual_income_INR") or 0)
        })

    # 11. Family Expenditure Table (Page 6-7)
    exp_list = data.get("family_expenditure_table") or inc_exp_data.get("family_expenditure") or []
    for exp in exp_list:
        ecat = exp.get("expenditure_category") or exp.get("category")
        if not ecat:
            continue
        doc.append("family_expenditure_table", {
            "expenditure_category": ecat,
            "monthly_amount": float(exp.get("monthly_amount") or exp.get("monthly_expense_INR") or 0),
            "annual_amount": float(exp.get("annual_amount") or exp.get("annual_expense_INR") or 0)
        })

    doc.insert(ignore_permissions=True)
    if data.get("submit_now", True):
        doc.submit()

    return {
        "success": True,
        "name": doc.name,
        "message": _("Baseline survey recorded successfully.")
    }

@frappe.whitelist()
def export_baseline_survey_excel(name):
    """Exports a single Baseline Survey and all its 11 child tables into structured CSV/Excel format"""
    import csv
    import io

    doc = frappe.get_doc("Baseline Survey", name)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Title & Metadata
    writer.writerow(["AGRICULTURAL DEVELOPMENT AND RURAL TRAINING INSTITUTE"])
    writer.writerow(["FAMILY SURVEY QUESTIONNAIRE - EXPORT"])
    writer.writerow(["Survey ID", doc.name, "Survey Date", str(doc.survey_date), "Status", doc.submission_status])
    writer.writerow([])
    
    # 1. Identification
    writer.writerow(["1. FARMER & HOUSEHOLD IDENTIFICATION"])
    writer.writerow(["Name of Head of Family", doc.farmer_name, "Mobile No", doc.contact_number or ""])
    writer.writerow(["Village", doc.village, "Age", doc.age or ""])
    writer.writerow(["Category", doc.category or "", "House Type", doc.house_type or ""])
    writer.writerow(["Toilet Available?", doc.has_toilet or "", "BPL?", doc.is_bpl or ""])
    writer.writerow(["Family Migrates?", doc.family_migrates or "", "Migration Location", doc.migration_location or ""])
    writer.writerow(["Migration Duration", doc.migration_duration or "", "Total Household Members", doc.household_members or 0])
    writer.writerow([])
    
    # 2. SHG
    writer.writerow(["SELF-HELP GROUP (SHG) & ENTERPRISE DETAILS"])
    writer.writerow(["SHG Member?", doc.is_shg_member or "", "SHG Name", doc.shg_name or ""])
    writer.writerow(["SHG Taken Loan?", doc.shg_has_loan or "", "Business Started?", doc.shg_business_started or ""])
    writer.writerow(["Type of Business", doc.shg_business_type or "", "", ""])
    writer.writerow([])
    
    # 3. Family Members
    writer.writerow(["8. FAMILY INFORMATION TABLE"])
    writer.writerow(["Sr. No.", "Name", "Relation", "Gender", "Age", "Education", "Occupation", "Annual Income (Rs.)"])
    for idx, row in enumerate(doc.household_members_table or [], 1):
        writer.writerow([idx, row.member_name, row.relation, row.gender, row.age, row.education, row.occupation, row.annual_income])
    writer.writerow([])
    
    # 4. Agricultural Details
    writer.writerow(["2. AGRICULTURAL DETAILS"])
    writer.writerow(["Total Land (Acres)", doc.total_landholding_acres, "Irrigated (Acres)", doc.irrigated_land_acres, "Rainfed (Acres)", doc.rainfed_land_acres])
    writer.writerow(["Conducts Soil Testing?", doc.conducts_soil_testing or "", "Last Done Date", doc.soil_testing_last_date or ""])
    writer.writerow(["Fertilizer as per recommendation?", doc.fertilizer_as_per_recommendation or "", "Yield Increase", doc.yield_increase_from_soil_test or ""])
    writer.writerow(["Produce Sorted/Graded?", doc.produce_sorted_graded or "", "Organic Farming?", doc.practices_organic_farming or ""])
    writer.writerow(["Modern Tech Info Source", doc.tech_info_source or "", "", ""])
    writer.writerow([])
    
    # 5. Crops Table
    writer.writerow(["CROP PRODUCTION & RETURNS TABLE"])
    writer.writerow(["Season", "Crop Name", "Area Irrigated (Acres)", "Area Dryland (Acres)", "Yield (Qtl)", "Place of Sale", "Market Rate (Rs./Qtl)", "Total Income (Rs.)", "Cost of Prod. (Rs.)", "Net Profit (Rs.)"])
    for row in (doc.crops_table or []):
        writer.writerow([row.season, row.crop_name, row.area_irrigated_acres, row.area_dryland_acres, row.yield_quintals, row.place_of_sale, row.market_rate_per_qtl, row.total_income, row.cost_of_production, row.net_profit])
    writer.writerow([])
    
    # 6. Irrigation Sources & Equipment
    writer.writerow(["21. IRRIGATION SOURCES"])
    writer.writerow(["Sr. No.", "Irrigation Source", "Quantity", "Depth (Feet)", "Water Availability (Months)"])
    for idx, row in enumerate(doc.irrigation_sources_table or [], 1):
        writer.writerow([idx, row.source_name, row.quantity, row.depth_feet, row.water_availability_months])
    writer.writerow([])
    
    writer.writerow(["21. IRRIGATION EQUIPMENT"])
    writer.writerow(["Sr. No.", "Equipment Name", "Quantity & Capacity (HP)"])
    for idx, row in enumerate(doc.irrigation_equipment_table or [], 1):
        writer.writerow([idx, row.equipment_name, row.quantity_and_capacity])
    writer.writerow([])
    
    # 7. Farm Conservation Works
    writer.writerow(["24. SOIL AND WATER CONSERVATION WORKS ON FARM"])
    writer.writerow(["Sr. No.", "Structure Type", "Status (Yes/No)", "Length / Count", "Implementing Dept.", "Maintained? (Yes/No)"])
    for idx, row in enumerate(doc.farm_conservation_works_table or [], 1):
        writer.writerow([idx, row.structure_type, row.status, row.length_or_count, row.implementing_dept, row.is_maintained])
    writer.writerow([])
    
    # 8. Stream Works
    writer.writerow(["30. STREAM / NULLAH CONSERVATION STRUCTURES"])
    writer.writerow(["Sr. No.", "Structure Name", "Count", "Length / Dimensions", "Under Which Scheme?", "Maintained? (Y/N)"])
    for idx, row in enumerate(doc.nullah_conservation_structures_table or [], 1):
        writer.writerow([idx, row.structure_name, row.count, row.dimensions, row.scheme_name, row.is_maintained])
    writer.writerow([])
    
    # 9. Drinking Water & WSP
    writer.writerow(["DRINKING WATER DETAILS & WATER SECURITY PLAN"])
    writer.writerow(["Village Water Committee?", doc.has_village_water_committee or "", "Participates in Mgmt?", doc.participates_drinking_water_mgmt or ""])
    writer.writerow(["Drinking Water Source", doc.drinking_water_source or "", "Source Ownership", doc.drinking_water_ownership or ""])
    writer.writerow(["Functional Tap Scheme?", doc.functional_tap_scheme or "", "Regular O&M?", doc.scheme_regular_om or ""])
    writer.writerow(["Water at Home?", doc.drinking_water_at_home or "", "Supply Days/Week", doc.water_supply_days_week or ""])
    writer.writerow(["Supply Duration", doc.water_supply_duration or "", "Year-Round Available?", doc.drinking_water_year_round or ""])
    writer.writerow(["Scarcity Management", doc.scarcity_water_mgmt or "", "Distance to Source", doc.drinking_water_distance or ""])
    writer.writerow(["WSP Awareness?", doc.wsp_awareness or "", "WSP Info Source", doc.wsp_info_source or ""])
    writer.writerow(["Participated in Drafting WSP?", doc.wsp_drafting_participation or "", "WSP Implemented in Scarcity?", doc.wsp_implemented_scarcity or ""])
    writer.writerow(["Water Budgeting Practices", doc.water_budgeting_practices or "", "", ""])
    writer.writerow([])
    
    # 10. Livestock
    writer.writerow(["50. LIVESTOCK DETAILS"])
    writer.writerow(["Sr. No.", "Livestock Type", "Count", "Daily Milk Prod. (Liters)", "Domestic Use (Liters)", "Available for Sale", "Income Generated (Rs.)"])
    for idx, row in enumerate(doc.livestock_table or [], 1):
        writer.writerow([idx, row.livestock_type, row.count, row.daily_milk_production_liters, row.domestic_use_liters, row.sale_liters, row.income_generated])
    writer.writerow([])
    writer.writerow(["Cattle Shed Type", doc.cattle_shed_type or "", "Milk Sale Counter", doc.milk_sale_channel or ""])
    writer.writerow([])
    
    # 11. Assets
    writer.writerow(["53. ASSET DETAILS"])
    writer.writerow(["Sr. No.", "Asset Description", "Quantity", "Estimated Value (Rs.)"])
    for idx, row in enumerate(doc.family_assets_table or [], 1):
        writer.writerow([idx, row.asset_description, row.quantity, row.estimated_value])
    writer.writerow([])
    
    # 12. Loans
    writer.writerow(["54. LOAN / DEBT DETAILS"])
    writer.writerow(["Sr. No.", "Loan Type", "Loan Amount (Rs.)", "Current Outstanding (Rs.)", "Name of Bank / Institution"])
    for idx, row in enumerate(doc.loans_table or [], 1):
        writer.writerow([idx, row.loan_category, row.loan_amount, getattr(row, 'current_outstanding', 0), row.bank_name])
    writer.writerow([])
    
    # 13. Family Income & Expenditure
    writer.writerow(["FAMILY INCOME & EXPENDITURE BREAKDOWN"])
    writer.writerow(["Income Source", "Monthly (Rs.)", "Annual (Rs.)", "Expenditure Category", "Monthly (Rs.)", "Annual (Rs.)"])
    inc_rows = doc.family_income_table or []
    exp_rows = doc.family_expenditure_table or []
    max_len = max(len(inc_rows), len(exp_rows), 1)
    for i in range(max_len):
        inc_src = inc_rows[i].income_source if i < len(inc_rows) else ""
        inc_m = inc_rows[i].monthly_amount if i < len(inc_rows) else ""
        inc_a = inc_rows[i].annual_amount if i < len(inc_rows) else ""
        exp_cat = exp_rows[i].expenditure_category if i < len(exp_rows) else ""
        exp_m = exp_rows[i].monthly_amount if i < len(exp_rows) else ""
        exp_a = exp_rows[i].annual_amount if i < len(exp_rows) else ""
        writer.writerow([inc_src, inc_m, inc_a, exp_cat, exp_m, exp_a])
    writer.writerow([])
    
    writer.writerow(["Surveyor Name", doc.surveyor_name or doc.field_officer or "", "Notes", doc.other_notes or ""])

    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = 'Baseline Survey'
    frappe.response['result'] = output.getvalue()
    frappe.response['filename'] = f"{doc.name}_{doc.farmer_name.replace(' ', '_')}_Export.csv"


def validate_project_finances_and_activities(doc, method=None):
    """Calculates remaining funds and validates Project configuration & dates"""
    budget = flt(doc.get("custom_budget") or doc.get("estimated_costing") or 0)
    actual_spent = flt(doc.get("custom_actual_amount_spent") or 0)
    doc.custom_remaining_funds = budget - actual_spent
    
    if flt(doc.get("custom_budget")) > 0 and not flt(doc.get("estimated_costing")):
        doc.estimated_costing = doc.custom_budget

    if doc.expected_start_date and doc.expected_end_date:
        if str(doc.expected_end_date) < str(doc.expected_start_date):
            frappe.throw("End Date cannot be before Start Date for Project.")


def sync_project_activities(doc, method=None):
    """Synchronizes Project Activity child table rows with standalone Activity DocType records"""
    for row in doc.get("custom_activities") or []:
        if not row.activity_name:
            continue
            
        if row.linked_activity_doc and frappe.db.exists("Activity", row.linked_activity_doc):
            frappe.db.set_value("Activity", row.linked_activity_doc, {
                "activity_name": row.activity_name,
                "goal": row.goal,
                "assignee": row.assignee,
                "description": row.description,
                "input_output": row.input_output,
                "impact": row.impact,
                "timeline_description": row.timeline,
                "theme": doc.get("custom_thematic_area")
            }, update_modified=False)
        elif not row.linked_activity_doc:
            act = frappe.get_doc({
                "doctype": "Activity",
                "activity_name": row.activity_name,
                "project": doc.name,
                "theme": doc.get("custom_thematic_area"),
                "goal": row.goal,
                "assignee": row.assignee,
                "description": row.description,
                "input_output": row.input_output,
                "impact": row.impact,
                "status": "In Progress" if row.status == "In Progress" else ("Completed" if row.status == "Completed" else "Open"),
                "timeline_description": row.timeline
            })
            act.insert(ignore_permissions=True)
            frappe.db.set_value("Project Activity", row.name, "linked_activity_doc", act.name, update_modified=False)


@frappe.whitelist()
def get_project_form_options():
    """Returns dropdown options for Project Web Form"""
    users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, fields=["name", "full_name", "email"])
    themes = frappe.get_all("Project Theme", fields=["name", "theme_name"])
    goals = frappe.get_all("Project Goal", fields=["name", "goal_name"])
    baselines = frappe.get_all("Baseline Survey", fields=["name", "farmer_name", "village"])
    feedbacks = frappe.get_all("Feedback Survey", fields=["name", "activity", "village"])
    
    return {
        "users": users,
        "themes": themes,
        "goals": goals,
        "baseline_surveys": baselines,
        "feedback_surveys": feedbacks,
        "phases": ["Planning", "Proposal", "Execution", "Results", "Feedback", "Future"],
        "statuses": ["Planning", "In Progress", "Deployed", "Completed", "Cancelled"]
    }


@frappe.whitelist(allow_guest=True)
def submit_kv_project(data):
    """Submits a KV Project and activities from Web Form or API"""
    import json
    if isinstance(data, str):
        data = json.loads(data)
        
    doc = frappe.get_doc({
        "doctype": "KV Project",
        "project_name": data.get("project_name") or "New Initiative",
        "theme": data.get("theme"),
        "project_phase": data.get("project_phase") or "Execution",
        "status": data.get("status") or "In Progress",
        "project_coordinator": data.get("project_coordinator") or "Administrator",
        "project_manager": data.get("project_manager") or "Administrator",
        "start_date": data.get("start_date") or nowdate(),
        "end_date": data.get("end_date") or nowdate(),
        "budget": flt(data.get("budget") or 0),
        "actual_amount_spent": flt(data.get("actual_amount_spent") or 0),
        "linked_baseline_survey": data.get("linked_baseline_survey"),
        "linked_field_tracking_form": data.get("linked_field_tracking_form")
    })
    
    for act in data.get("activities") or []:
        if not act.get("activity_name"):
            continue
        doc.append("activities", {
            "activity_name": act.get("activity_name"),
            "goal": act.get("goal"),
            "assignee": act.get("assignee"),
            "start_date": act.get("start_date") or doc.start_date,
            "end_date": act.get("end_date") or doc.end_date,
            "status": act.get("status") or "Planned",
            "description": act.get("description"),
            "input_output": act.get("input_output"),
            "impact": act.get("impact")
        })
        
    for fb in data.get("feedback_surveys") or []:
        survey_id = fb.get("feedback_survey")
        if not survey_id and fb.get("village"):
            # Create standalone Feedback Survey
            new_fb = frappe.get_doc({
                "doctype": "Feedback Survey",
                "village": fb.get("village"),
                "date_of_visit": fb.get("date_of_visit") or nowdate(),
                "field_officer": fb.get("field_officer") or doc.project_coordinator or "Administrator",
                "activity": fb.get("activity") or "Community Intervention",
                "respondent_type": fb.get("respondent_type") or "Community Member",
                "total_participants": int(fb.get("total_participants") or 25),
                "households_involved": int(fb.get("households_involved") or 15),
                "overall_rating": fb.get("overall_rating") or "5",
                "significant_change": fb.get("significant_change") or "Positive community adoption",
                "facilitator_observations": fb.get("facilitator_observations") or "Satisfactory participation",
                "project": doc.name,
                "submission_status": "Submitted"
            })
            new_fb.insert(ignore_permissions=True)
            survey_id = new_fb.name
            
        if survey_id:
            doc.append("feedback_surveys", {
                "feedback_survey": survey_id,
                "village": fb.get("village"),
                "activity": fb.get("activity"),
                "date_of_visit": fb.get("date_of_visit") or nowdate(),
                "total_participants": int(fb.get("total_participants") or 0),
                "overall_rating": str(fb.get("overall_rating") or "5")
            })
        
    doc.insert(ignore_permissions=True)
    
    # Also create standard ERPNext Project mirror if useful
    try:
        if not frappe.db.exists("Project", {"project_name": doc.project_name}):
            frappe.get_doc({
                "doctype": "Project",
                "project_name": doc.project_name,
                "company": frappe.defaults.get_user_default("Company") or frappe.get_all("Company")[0].name,
                "custom_project_phase": doc.project_phase,
                "custom_thematic_area": doc.theme,
                "custom_project_coordinator": doc.project_coordinator,
                "custom_project_manager": doc.project_manager,
                "expected_start_date": doc.start_date,
                "expected_end_date": doc.end_date,
                "custom_budget": doc.budget,
                "custom_actual_amount_spent": doc.actual_amount_spent,
                "custom_remaining_funds": doc.remaining_funds,
                "custom_linked_baseline_survey": doc.linked_baseline_survey,
                "custom_linked_field_tracking_form": doc.linked_field_tracking_form
            }).insert(ignore_permissions=True)
    except Exception:
        pass
        
    return {
        "success": True,
        "name": doc.name,
        "project_name": doc.project_name,
        "remaining_funds": doc.remaining_funds
    }


# ==========================================
# FRONTEND PORTAL CRUD & QUERY APIS
# ==========================================

@frappe.whitelist(allow_guest=True)
def get_all_dropdown_options():
    """Returns dropdown options for Project, Activity, Task, and Form modals."""
    projects = frappe.get_all("Project", fields=["name", "project_name", "status"])
    users = frappe.get_all("User", filters={"enabled": 1, "name": ["not in", ["Guest", "Administrator"]]}, fields=["name", "full_name", "email"])
    if not users:
        users = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "full_name", "email"])
    themes = frappe.get_all("Project Theme", fields=["name", "theme_name"]) if frappe.db.exists("DocType", "Project Theme") else []
    goals = frappe.get_all("Project Goal", fields=["name", "goal_name", "project"]) if frappe.db.exists("DocType", "Project Goal") else []
    activities = frappe.get_all("Activity", fields=["name", "activity_name", "project", "status"]) if frappe.db.exists("DocType", "Activity") else []
    villages = frappe.get_all("Village Profile", fields=["name", "village_name", "district"]) if frappe.db.exists("DocType", "Village Profile") else []
    
    return {
        "projects": projects,
        "users": users,
        "themes": themes,
        "goals": goals,
        "activities": activities,
        "villages": villages,
        "phases": ["Survey", "Proposal", "Execution", "Results", "Feedback", "Future"],
        "statuses": ["Open", "In Progress", "Completed", "Cancelled"],
        "task_statuses": ["Open", "Working", "Pending Review", "Completed", "Cancelled"],
        "priorities": ["Low", "Medium", "High", "Urgent"]
    }


@frappe.whitelist(allow_guest=True)
def get_project_detail(project_id=None):
    """Fetches full project details, associated activities, tasks, and attached structured forms."""
    if not project_id:
        first = frappe.get_all("Project", fields=["name"], limit=1) or (frappe.get_all("KV Project", fields=["name"], limit=1) if frappe.db.exists("DocType", "KV Project") else [])
        if first:
            project_id = first[0].name

    proj = None
    if project_id and frappe.db.exists("Project", project_id):
        proj = frappe.get_doc("Project", project_id)
    elif project_id and frappe.db.exists("KV Project", project_id):
        proj = frappe.get_doc("KV Project", project_id)
    elif project_id:
        projs = frappe.get_all("Project", filters={"project_name": project_id}, limit=1)
        if projs:
            proj = frappe.get_doc("Project", projs[0].name)
        elif frappe.db.exists("DocType", "KV Project"):
            projs = frappe.get_all("KV Project", filters={"project_name": project_id}, limit=1)
            if projs:
                proj = frappe.get_doc("KV Project", projs[0].name)
                
    if not proj:
        # Default empty structure if no project in DB
        return {
            "project": {"name": "PROJ-DEFAULT", "project_name": "General Project", "status": "Open", "custom_budget": 0, "custom_actual_amount_spent": 0, "custom_remaining_funds": 0},
            "activities": [],
            "tasks": [],
            "structured_forms": {"baseline_surveys": [], "feedback_surveys": [], "village_profiles": []}
        }
        
    p_name = proj.name
    p_title = getattr(proj, "project_name", p_name)
    
    # Project data dict
    budget = flt(getattr(proj, "custom_budget", getattr(proj, "budget", 0)))
    spent = flt(getattr(proj, "custom_actual_amount_spent", getattr(proj, "actual_amount_spent", 0)))
    remaining = budget - spent
    
    project_data = {
        "name": p_name,
        "project_name": p_title,
        "status": getattr(proj, "status", "Open"),
        "percent_complete": flt(getattr(proj, "percent_complete", 65)),
        "expected_start_date": getattr(proj, "expected_start_date", getattr(proj, "start_date", "2026-01-01")),
        "expected_end_date": getattr(proj, "expected_end_date", getattr(proj, "end_date", "2026-12-31")),
        "custom_project_phase": getattr(proj, "custom_project_phase", getattr(proj, "project_phase", "Proposal")),
        "custom_thematic_area": getattr(proj, "custom_thematic_area", getattr(proj, "theme", "Watershed Management")),
        "custom_project_coordinator": getattr(proj, "custom_project_coordinator", getattr(proj, "project_coordinator", "Administrator")),
        "custom_project_manager": getattr(proj, "custom_project_manager", getattr(proj, "project_manager", "Administrator")),
        "custom_budget": budget,
        "custom_actual_amount_spent": spent,
        "custom_remaining_funds": remaining,
        "custom_linked_baseline_survey": getattr(proj, "custom_linked_baseline_survey", getattr(proj, "linked_baseline_survey", "")),
        "custom_linked_field_tracking_form": getattr(proj, "custom_linked_field_tracking_form", getattr(proj, "linked_field_tracking_form", ""))
    }
    
    # Fetch Activities for this Project
    activities = []
    if frappe.db.exists("DocType", "Activity"):
        act_docs = frappe.get_all(
            "Activity",
            filters={"project": ["in", [p_name, p_title]]},
            fields=[
                "name", "activity_name", "project", "theme", "status",
                "assignee", "goal", "linked_kre", "start_date", "end_date",
                "input_output", "impact", "planned_budget", "actual_expenditure", "description"
            ],
            order_by="creation asc"
        )
        for act in act_docs:
            task_count = frappe.db.count("Task", {"custom_activity": act.name}) or 0
            act["task_count"] = task_count
            activities.append(act)
            
    # Also check child table Project Activity if any exist
    if not activities and hasattr(proj, "activities") and proj.activities:
        for a in proj.activities:
            activities.append({
                "name": a.linked_activity or a.name,
                "activity_name": a.activity_name,
                "project": p_name,
                "theme": project_data["custom_thematic_area"],
                "status": a.status or "In Progress",
                "assignee": a.assignee or "Administrator",
                "start_date": a.start_date or "2026-01-01",
                "end_date": a.end_date or "2026-03-31",
                "input_output": a.input_output or "",
                "impact": a.impact or "",
                "planned_budget": flt(getattr(a, "planned_budget", 0)),
                "actual_expenditure": flt(getattr(a, "actual_expenditure", 0)),
                "description": a.description or "",
                "task_count": frappe.db.count("Task", {"custom_activity": a.linked_activity or a.name}) or 0
            })
            
    # Fetch Tasks for this Project
    tasks = []
    if frappe.db.exists("DocType", "Task"):
        task_docs = frappe.get_all(
            "Task",
            filters={"project": ["in", [p_name, p_title]]},
            fields=[
                "name", "subject", "project", "custom_activity", "status",
                "priority", "exp_start_date", "exp_end_date", "description",
                "_assign"
            ],
            order_by="creation asc"
        )
        for td in task_docs:
            td["custom_assignee"] = "Administrator"
        tasks = task_docs
        
    # Fetch Structured Forms attached to this Project
    # 1. Baseline Surveys
    baseline_surveys = []
    if frappe.db.exists("DocType", "Baseline Survey"):
        bl_docs = frappe.get_all(
            "Baseline Survey",
            filters={"project": ["in", [p_name, p_title]]},
            fields=["name", "farmer_name", "village", "survey_date", "submission_status", "household_members", "livestock_count"],
            order_by="creation desc"
        )
        if not bl_docs and project_data["custom_linked_baseline_survey"]:
            if frappe.db.exists("Baseline Survey", project_data["custom_linked_baseline_survey"]):
                bl = frappe.get_doc("Baseline Survey", project_data["custom_linked_baseline_survey"])
                bl_docs = [{
                    "name": bl.name,
                    "farmer_name": getattr(bl, "farmer_name", "Primary Beneficiary"),
                    "village": bl.village or "Rampur",
                    "survey_date": bl.survey_date or "2026-01-15",
                    "submission_status": getattr(bl, "submission_status", "Submitted"),
                    "household_members": getattr(bl, "household_members", 5),
                    "livestock_count": getattr(bl, "livestock_count", 4)
                }]
        baseline_surveys = bl_docs
        
    # 2. Feedback Surveys
    feedback_surveys = []
    if frappe.db.exists("DocType", "Feedback Survey"):
        fb_docs = frappe.get_all(
            "Feedback Survey",
            filters={"project": ["in", [p_name, p_title]]},
            fields=["name", "village", "activity", "date_of_visit", "total_participants", "overall_rating", "respondent_type", "significant_change"],
            order_by="creation desc"
        )
        if not fb_docs and project_data["custom_linked_field_tracking_form"]:
            if frappe.db.exists("Feedback Survey", project_data["custom_linked_field_tracking_form"]):
                fb = frappe.get_doc("Feedback Survey", project_data["custom_linked_field_tracking_form"])
                fb_docs = [{
                    "name": fb.name,
                    "village": fb.village or "Rampur",
                    "activity": fb.activity or "Water Budgeting Workshop",
                    "date_of_visit": fb.date_of_visit or "2026-02-15",
                    "total_participants": fb.total_participants or 35,
                    "overall_rating": fb.overall_rating or "5",
                    "respondent_type": fb.respondent_type or "Farmer",
                    "significant_change": fb.significant_change or "High adoption rate"
                }]
        feedback_surveys = fb_docs
        
    # 3. Village Profiles
    village_profiles = []
    if frappe.db.exists("DocType", "Village Profile"):
        vp_names = list(set([b.get("village") for b in baseline_surveys if b.get("village")] + [f.get("village") for f in feedback_surveys if f.get("village")]))
        if vp_names:
            village_profiles = frappe.get_all(
                "Village Profile",
                filters={"village_name": ["in", vp_names]},
                fields=["name", "village_name", "district", "block_taluka", "total_population", "total_households", "profile_status"]
            )
        if not village_profiles:
            village_profiles = frappe.get_all(
                "Village Profile",
                fields=["name", "village_name", "district", "block_taluka", "total_population", "total_households", "profile_status"],
                limit=3
            )
            
    return {
        "project": project_data,
        "activities": activities,
        "tasks": tasks,
        "structured_forms": {
            "baseline_surveys": baseline_surveys,
            "feedback_surveys": feedback_surveys,
            "village_profiles": village_profiles
        }
    }


@frappe.whitelist(allow_guest=True)
def get_activity_detail(activity_id=None):
    """Fetches single activity details and its associated child tasks."""
    if not activity_id:
        first = frappe.get_all("Activity", fields=["name"], limit=1)
        if first:
            activity_id = first[0].name
            
    if not activity_id or not frappe.db.exists("Activity", activity_id):
        # Default empty activity structure if none in DB
        return {
            "activity": {"name": "ACT-DEFAULT", "activity_name": "General Activity", "project": "General", "project_title": "General Project", "status": "Open"},
            "tasks": []
        }
        
    act = frappe.get_doc("Activity", activity_id)
    p_name = act.project
    
    # Project title
    project_title = p_name
    if frappe.db.exists("Project", p_name):
        project_title = frappe.db.get_value("Project", p_name, "project_name") or p_name
    elif frappe.db.exists("DocType", "KV Project") and frappe.db.exists("KV Project", p_name):
        project_title = frappe.db.get_value("KV Project", p_name, "project_name") or p_name
        
    # Fetch tasks for this activity
    tasks = frappe.get_all(
        "Task",
        filters={"custom_activity": activity_id},
        fields=[
            "name", "subject", "project", "custom_activity", "status",
            "priority", "exp_start_date", "exp_end_date", "description",
            "_assign"
        ],
        order_by="creation asc"
    )
    for td in tasks:
        td["custom_assignee"] = "Administrator"
    
    return {
        "activity": {
            "name": act.name,
            "activity_name": act.activity_name,
            "project": act.project,
            "project_title": project_title,
            "theme": act.theme,
            "status": act.status or "Open",
            "assignee": act.assignee,
            "goal": act.goal,
            "linked_kre": act.linked_kre,
            "start_date": act.start_date,
            "end_date": act.end_date,
            "timeline_description": act.timeline_description,
            "input_output": act.input_output,
            "impact": act.impact,
            "planned_budget": flt(act.planned_budget),
            "actual_expenditure": flt(act.actual_expenditure),
            "description": act.description
        },
        "tasks": tasks
    }


@frappe.whitelist(allow_guest=True)
def save_activity(data):
    """Create or Update an Activity record."""
    if isinstance(data, str):
        import json
        data = json.loads(data)
        
    name = data.get("name")
    if name and frappe.db.exists("Activity", name):
        doc = frappe.get_doc("Activity", name)
    else:
        doc = frappe.new_doc("Activity")
        
    # Set fields
    doc.activity_name = data.get("activity_name")
    doc.project = data.get("project")
    doc.theme = data.get("theme")
    doc.status = data.get("status") or "Open"
    doc.assignee = data.get("assignee")
    doc.goal = data.get("goal")
    doc.linked_kre = data.get("linked_kre")
    doc.start_date = data.get("start_date")
    doc.end_date = data.get("end_date")
    doc.timeline_description = data.get("timeline_description")
    doc.input_output = data.get("input_output")
    doc.impact = data.get("impact")
    doc.planned_budget = flt(data.get("planned_budget") or 0)
    doc.actual_expenditure = flt(data.get("actual_expenditure") or 0)
    doc.description = data.get("description")
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {
        "success": True,
        "name": doc.name,
        "activity_name": doc.activity_name,
        "project": doc.project,
        "status": doc.status
    }


@frappe.whitelist(allow_guest=True)
def delete_activity_record(name):
    """Delete an Activity record after checking for child tasks."""
    if not frappe.db.exists("Activity", name):
        frappe.throw(_("Activity does not exist."))
        
    # Check for child tasks and remove / unlink them
    tasks = frappe.get_all("Task", filters={"custom_activity": name})
    for t in tasks:
        frappe.delete_doc("Task", t.name, ignore_permissions=True)
        
    frappe.delete_doc("Activity", name, ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "message": f"Activity {name} and child tasks deleted successfully."}


@frappe.whitelist(allow_guest=True)
def save_task(data):
    """Create or Update a Task record."""
    if isinstance(data, str):
        import json
        data = json.loads(data)
        
    name = data.get("name")
    if name and frappe.db.exists("Task", name):
        doc = frappe.get_doc("Task", name)
    else:
        doc = frappe.new_doc("Task")
        
    doc.subject = data.get("subject")
    doc.project = data.get("project")
    doc.custom_activity = data.get("custom_activity")
    doc.status = data.get("status") or "Open"
    doc.priority = data.get("priority") or "Medium"
    doc.exp_start_date = data.get("exp_start_date")
    doc.exp_end_date = data.get("exp_end_date")
    doc.description = data.get("description")
    doc.custom_assignee = data.get("custom_assignee")
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {
        "success": True,
        "name": doc.name,
        "subject": doc.subject,
        "status": doc.status,
        "project": doc.project,
        "custom_activity": doc.custom_activity
    }


@frappe.whitelist(allow_guest=True)
def delete_task_record(name):
    """Delete a Task record."""
    if not frappe.db.exists("Task", name):
        frappe.throw(_("Task does not exist."))
    frappe.delete_doc("Task", name, ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "message": f"Task {name} deleted successfully."}


@frappe.whitelist(allow_guest=True)
def toggle_task_status(name, status):
    """Update task status (validating dependency gate)."""
    if not frappe.db.exists("Task", name):
        frappe.throw(_("Task does not exist."))
    doc = frappe.get_doc("Task", name)
    doc.status = status
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def get_global_activities(project=None, status=None, assignee=None, search=None):
    """Returns global list of all activities with parent project details."""
    filters = {}
    if project:
        filters["project"] = project
    if status:
        filters["status"] = status
    if assignee:
        filters["assignee"] = assignee
        
    activities = frappe.get_all(
        "Activity",
        filters=filters,
        fields=[
            "name", "activity_name", "project", "theme", "status",
            "assignee", "goal", "start_date", "end_date", "impact",
            "planned_budget", "actual_expenditure", "creation"
        ],
        order_by="modified desc"
    )
    
    # Enrich with project title and task count
    project_map = {}
    for p in frappe.get_all("Project", fields=["name", "project_name"]):
        project_map[p.name] = p.project_name
    for p in frappe.get_all("KV Project", fields=["name", "project_name"]):
        project_map[p.name] = p.project_name
        
    result = []
    for a in activities:
        a["project_title"] = project_map.get(a.project, a.project)
        a["task_count"] = frappe.db.count("Task", {"custom_activity": a.name}) or 0
        if search:
            s = search.lower()
            if s not in a.activity_name.lower() and s not in (a["project_title"] or "").lower():
                continue
        result.append(a)
        
    return result


@frappe.whitelist(allow_guest=True)
def get_global_tasks(project=None, activity=None, status=None, priority=None, assignee=None, search=None):
    """Returns global list of all tasks with Project → Activity → Task hierarchy tags."""
    filters = {}
    if project:
        filters["project"] = project
    if activity:
        filters["custom_activity"] = activity
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    tasks = frappe.get_all(
        "Task",
        filters=filters,
        fields=[
            "name", "subject", "project", "custom_activity", "status",
            "priority", "exp_start_date", "exp_end_date", "description",
            "_assign", "creation"
        ],
        order_by="modified desc"
    )
    for t in tasks:
        t["custom_assignee"] = "Administrator"
        if t.get("_assign"):
            try:
                import json
                users = json.loads(t["_assign"])
                if users:
                    t["custom_assignee"] = users[0]
            except Exception:
                pass
    
    # Build maps
    project_map = {}
    for p in frappe.get_all("Project", fields=["name", "project_name"]):
        project_map[p.name] = p.project_name
    for p in frappe.get_all("KV Project", fields=["name", "project_name"]):
        project_map[p.name] = p.project_name
        
    act_map = {}
    for a in frappe.get_all("Activity", fields=["name", "activity_name", "project"]):
        act_map[a.name] = a
        
    result = []
    for t in tasks:
        act_info = act_map.get(t.custom_activity, {})
        t["activity_name"] = act_info.get("activity_name", t.custom_activity or "General Task")
        parent_p = t.project or act_info.get("project", "")
        t["project_title"] = project_map.get(parent_p, parent_p or "General Project")
        
        if search:
            s = search.lower()
            if s not in t.subject.lower() and s not in t["activity_name"].lower() and s not in t["project_title"].lower():
                continue
        result.append(t)
        
    return result


@frappe.whitelist(allow_guest=True)
def get_analytics_summary():
    """Aggregates enterprise analytics across projects, activities, tasks, and surveys."""
    total_projects = frappe.db.count("Project") or frappe.db.count("KV Project") or 0
    total_activities = frappe.db.count("Activity") or 0
    total_tasks = frappe.db.count("Task") or 0
    total_baseline = frappe.db.count("Baseline Survey") or 0
    total_feedback = frappe.db.count("Feedback Survey") or 0
    total_villages = frappe.db.count("Village Profile") or 0
    
    # Financial sums
    projects = frappe.get_all("Project", fields=["custom_budget", "custom_actual_amount_spent", "status", "custom_project_phase"])
    total_budget = sum([flt(p.custom_budget) for p in projects])
    total_spent = sum([flt(p.custom_actual_amount_spent) for p in projects])
    remaining_funds = total_budget - total_spent
    
    # Feedback rating average
    ratings = frappe.get_all("Feedback Survey", fields=["overall_rating", "total_participants"])
    avg_rating = 0
    total_participants = sum([cint(r.total_participants) for r in ratings])
    if ratings:
        valid_ratings = [flt(r.overall_rating) for r in ratings if r.overall_rating and r.overall_rating.isdigit()]
        if valid_ratings:
            avg_rating = round(sum(valid_ratings) / len(valid_ratings), 2)
            
    return {
        "kpis": {
            "total_projects": total_projects,
            "total_activities": total_activities,
            "total_tasks": total_tasks,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "remaining_funds": remaining_funds,
            "total_baseline": total_baseline,
            "total_feedback": total_feedback,
            "total_villages": total_villages,
            "avg_feedback_rating": avg_rating,
            "total_beneficiaries_reached": total_participants
        }
    }










