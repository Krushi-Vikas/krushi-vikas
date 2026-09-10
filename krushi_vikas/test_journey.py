"""End-to-end check of the 10-step operational roadmap.

Run with:
    bench --site krushivikas.local execute krushi_vikas.test_journey.run

Walks a concept note all the way to a project carrying field evidence, and
asserts that every gate refuses to let the chain be short-circuited.
Everything is rolled back at the end.
"""

import frappe
from frappe.model.workflow import apply_workflow

from krushi_vikas.api import (
	create_project_from_proposal,
	create_proposal_from_rra,
	create_rra_from_concept_note,
	get_journey_status,
)

PREFIX = "ZZ Journey Test"


def clear_approvals(project):
	"""Walk a project through however many approval steps it needs."""
	from krushi_vikas.approvals import approve

	for _ in range(4):
		project.reload()

		if project.approval_status != "Pending Approval":
			return

		approver = project.pending_approver or {
			"Project Coordinator": "pc1_test@krushivikas.org",
			"Project Director": "dir_test@krushivikas.org",
			"CEO": "ceo_test@krushivikas.org",
			"Project Manager": "pm1_test@krushivikas.org",
		}.get(project.pending_approver_role)

		frappe.set_user(approver)
		approve("KV Project", project.name)

	frappe.set_user("Administrator")


def run():
	print("=== TESTING 10-STEP OPERATIONAL ROADMAP ===")
	frappe.set_user("Administrator")

	failures = []

	def check(label, condition):
		print(f"  {'PASS' if condition else 'FAIL'}  {label}")
		if not condition:
			failures.append(label)

	def blocked(fn):
		try:
			fn()
		except frappe.ValidationError:
			return True
		return False

	theme = (frappe.get_all("Project Theme", pluck="name") or [None])[0]
	coordinator = "pc1_test@krushivikas.org"

	# ── 01 Concept Note ──────────────────────────────────────────
	note = frappe.new_doc("Concept Note")
	note.title = f"{PREFIX} Watershed"
	note.thematic_area = theme
	note.estimated_budget = 500000
	note.beneficiary_estimate = 300
	note.duration_months = 12
	note.insert()

	check("02 is blocked while the concept note is unapproved",
		blocked(lambda: create_rra_from_concept_note(note.name)))

	apply_workflow(note, "Submit for Review")
	check("01 reaches Under Review", note.status == "Under Review")
	apply_workflow(note, "Approve")
	check("01 reaches Approved and submits", note.status == "Approved" and note.docstatus == 1)

	# ── 02 RRA Report ────────────────────────────────────────────
	report = frappe.get_doc("RRA Report", create_rra_from_concept_note(note.name))
	check("02 inherits the theme from the concept note", report.thematic_area == theme)
	check("02 carries the indicative budget", report.recommended_budget == 500000)
	check("03 is blocked while the appraisal is unapproved",
		blocked(lambda: create_proposal_from_rra(report.name)))

	report.recommendation = "Proceed"
	report.feasibility = "High"
	report.save()
	apply_workflow(report, "Submit for Review")
	apply_workflow(report, "Approve")
	check("02 reaches Approved", report.workflow_state == "Approved")

	# ── 03 Proposal ──────────────────────────────────────────────
	proposal = frappe.get_doc("Project Proposal", create_proposal_from_rra(report.name))
	check("03 seeds a planned window from the concept note duration",
		bool(proposal.planned_start_date and proposal.planned_end_date))

	proposal.append("budget_lines",
		{"particulars": "Field staff", "category": "Personnel", "unit_count": 4, "rate": 50000})
	proposal.append("budget_lines",
		{"particulars": "Check dams", "category": "Infrastructure", "unit_count": 10, "rate": 25000})
	proposal.save()
	check("03 rolls the budget lines up to the total", proposal.total_budget == 450000)
	check("03 derives the duration in months", proposal.duration_months == 12)

	check("06 is blocked while the proposal is unapproved",
		blocked(lambda: create_project_from_proposal(proposal.name)))

	# ── 04 External approval ─────────────────────────────────────
	apply_workflow(proposal, "Submit for Review")
	check("04 routes through coordinator review", proposal.workflow_state == "PC Review")
	apply_workflow(proposal, "Escalate")
	check("04 escalates to the director", proposal.workflow_state == "Director Review")
	apply_workflow(proposal, "Approve")
	check("04 reaches Approved and submits",
		proposal.workflow_state == "Approved" and proposal.docstatus == 1)

	# ── 06 Project creation ──────────────────────────────────────
	project = frappe.get_doc(
		"KV Project", create_project_from_proposal(proposal.name, coordinator=coordinator)
	)
	check("06 carries the approved budget", project.budget == 450000)
	check("06 carries the approved window",
		str(project.start_date) == str(proposal.planned_start_date)
		and str(project.end_date) == str(proposal.planned_end_date))
	check("06 keeps the full provenance chain",
		project.proposal == proposal.name
		and project.rra_report == report.name
		and project.concept_note == note.name)
	check("06 refuses a second project from the same proposal",
		blocked(lambda: create_project_from_proposal(proposal.name)))

	# ── 07 Internal approval ─────────────────────────────────────
	# No longer a fixed workflow: routing depends on who raised the
	# project, so this goes through krushi_vikas.approvals instead.
	from krushi_vikas.approvals import approve

	# This project was raised by the Administrator, whose approval chain is
	# empty, so it is approved outright — a director or CEO raising work
	# needs nobody above them. Routing itself is covered by test_approvals.
	check("07 needs no approval when raised by an authority",
		project.approval_status == "Approved")

	clear_approvals(project)
	project.reload()
	check("07 sits at task assignment once approved",
		project.journey_stage == "Task Assignment")

	# ── 08/09 Activity and execution ─────────────────────────────
	activity = frappe.new_doc("Activity")
	activity.activity_name = f"{PREFIX} Activity"
	activity.project = project.name
	activity.status = "Open"
	activity.insert()

	project.status = "In Progress"; project.save()
	check("09 reflects execution", project.journey_stage == "Execution")

	# ── 10 Reverse reporting ─────────────────────────────────────
	outcome = frappe.new_doc("Activity Outcome")
	outcome.project = project.name
	outcome.measurement_date = "2026-11-01"
	outcome.actual_value = 12
	outcome.insert(ignore_mandatory=True)

	project.save()
	check("10 reflects evidence coming back from the field",
		project.journey_stage == "Reverse Reporting")

	project.status = "Completed"; project.save()
	check("closed once the project completes", project.journey_stage == "Closed")

	# ── Roadmap read-out ─────────────────────────────────────────
	status = get_journey_status(project.name)
	done = {s["number"] for s in status["stages"] if s["complete"]}
	check("roadmap reports 01-04 complete", {"01", "02", "03", "04"} <= done)
	check("roadmap reports 06-10 complete", {"06", "07", "08", "09", "10"} <= done)
	check("roadmap reports 05 outstanding (no baseline survey)", "05" not in done)

	frappe.db.rollback()
	print("\n  (all test records rolled back)")

	print()
	if failures:
		print(f"=== {len(failures)} FAILURE(S) ===")
		for f in failures:
			print(f"  - {f}")
	else:
		print("=== ALL JOURNEY CHECKS PASSED ===")

	return not failures
