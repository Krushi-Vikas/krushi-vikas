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
