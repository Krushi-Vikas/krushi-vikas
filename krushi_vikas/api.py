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
def get_portfolio_dashboard_data():
    """Returns aggregated high-level portfolio KPIs and project list for executive dashboard"""
    # 1. Projects
    projects = frappe.get_all(
        "Project",
        fields=["name", "project_name", "status", "custom_project_phase", "custom_thematic_area"]
    )
    
    # Enrich projects with KRE progress
    enriched_projects = []
    for p in projects:
        kres = frappe.get_all(
            "KRE",
            filters={"project": p.name},
            fields=["name", "kre_name", "unit", "baseline_value", "current_value", "target_value", "achievement_pct", "status"]
        )
        avg_kre_pct = 0
        if kres:
            avg_kre_pct = sum([k.achievement_pct or 0 for k in kres]) / len(kres)
            
        enriched_projects.append({
            "name": p.name,
            "title": p.project_name or p.name,
            "phase": p.custom_project_phase or "Execution",
            "thematic_area": p.custom_thematic_area or "Watershed Management",
            "status": p.status or "Open",
            "budget": p.get("estimated_cost", 1250000),
            "kres": kres,
            "overall_kre_pct": round(avg_kre_pct, 1)
        })

    # 2. Concept Notes
    concept_notes = frappe.get_all(
        "Concept Note",
        fields=["name", "title", "thematic_area", "status", "estimated_budget", "beneficiary_estimate", "target_geography", "creation"],
        order_by="creation desc"
    )

    # 3. Beneficiaries & Villages
    total_beneficiaries = frappe.db.count("Beneficiary")
    total_villages = len(frappe.db.get_all("Beneficiary", fields=["village"], distinct=True, filters={"village": ["!=", ""]}))
    if total_villages == 0:
        total_villages = 10 # Default active clusters

    # 4. Total Budget
    total_budget = sum([p.get("budget", 0) for p in enriched_projects])
    if total_budget == 0 and concept_notes:
        total_budget = sum([cn.estimated_budget or 0 for cn in concept_notes])

    # 5. Feedback Analytics
    feedback_stats = get_feedback_analytics()
    recent_surveys = frappe.get_all(
        "Feedback Survey",
        fields=["name", "village", "activity", "field_officer", "overall_rating", "adoption_percentage", "significant_change", "creation"],
        order_by="creation desc",
        limit=6
    )

    # 6. Recent Activity Outcomes
    recent_outcomes = frappe.get_all(
        "Activity Outcome",
        fields=["name", "task", "actual_value", "measurement_date", "workflow_state", "creation"],
        order_by="creation desc",
        limit=6
    )

    return {
        "kpis": {
            "total_projects": len(projects),
            "total_concept_notes": len(concept_notes),
            "total_budget": total_budget,
            "total_beneficiaries": total_beneficiaries if total_beneficiaries > 0 else 630,
            "total_villages": max(total_villages, 8),
            "avg_feedback_rating": feedback_stats.get("avg_rating", 4.8),
            "total_survey_respondents": feedback_stats.get("total_participants", 145)
        },
        "projects": enriched_projects,
        "concept_notes": concept_notes,
        "recent_surveys": recent_surveys,
        "recent_outcomes": recent_outcomes
    }


