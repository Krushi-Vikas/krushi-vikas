import frappe
from frappe import _

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



