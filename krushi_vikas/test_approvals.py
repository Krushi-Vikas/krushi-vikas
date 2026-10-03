"""Hierarchical approval routing.

    bench --site krushivikas.local execute krushi_vikas.test_approvals.run

Approver depends on who raised the document, not on a fixed route.
Everything is rolled back at the end.
"""

import frappe

from krushi_vikas.approvals import approve, get_pending_approvals, reject

PM = "pm1_test@krushivikas.org"
PC = "pc1_test@krushivikas.org"
DIR = "dir_test@krushivikas.org"
CEO = "ceo_test@krushivikas.org"


def run():
	print("=== TESTING HIERARCHICAL APPROVAL ROUTING ===")
	frappe.set_user("Administrator")
	failures = []

	def check(label, condition):
		print(f"  {'PASS' if condition else 'FAIL'}  {label}")
		if not condition:
			failures.append(label)

	def blocked(fn):
		try:
			fn()
		except frappe.PermissionError:
			return True
		return False

	def raise_project(name, creator):
		frappe.set_user(creator)
		p = frappe.new_doc("KV Project")
		p.project_name = name
		p.status = "Planning"
		p.project_coordinator = PC
		p.project_manager = PM
		p.start_date = "2026-01-01"
		p.end_date = "2026-12-31"
		p.insert(ignore_permissions=True)
		p.reload()
		return p

	def waiting(p):
		p.reload()
		return p.pending_approver or p.pending_approver_role

	# ── Raised by a Project Manager: PC, then Director ────────────
	pm_project = raise_project("ZZ Approval PM", PM)
	check("a manager's project waits on its coordinator", waiting(pm_project) == PC)
	check("it shows as awaiting approval", pm_project.journey_stage == "Awaiting Approval")

	frappe.set_user(PM)
	check("the raiser cannot approve their own project",
		blocked(lambda: approve("KV Project", pm_project.name)))

	frappe.set_user(DIR)
	check("a director cannot jump ahead of the coordinator",
		blocked(lambda: approve("KV Project", pm_project.name)))

	frappe.set_user(PC)
	check("the coordinator sees it in their queue",
		pm_project.name in [i["name"] for i in get_pending_approvals()])
	approve("KV Project", pm_project.name, "Budget checked")
	check("it then waits on the director", waiting(pm_project) == "Project Director")

	frappe.set_user(DIR)
	approve("KV Project", pm_project.name)
	pm_project.reload()
	check("the director completes it", pm_project.approval_status == "Approved")
	check("the stage advances once approved", pm_project.journey_stage == "Task Assignment")

	# ── Raised by a Coordinator: straight to the Director ─────────
	pc_project = raise_project("ZZ Approval PC", PC)
	check("a coordinator's project waits on the director",
		waiting(pc_project) == "Project Director")

	# ── Raised by a Director: the CEO ────────────────────────────
	dir_project = raise_project("ZZ Approval DIR", DIR)
	check("a director's project waits on the CEO", waiting(dir_project) == "CEO")

	frappe.set_user(CEO)
	check("the CEO sees it in their queue",
		dir_project.name in [i["name"] for i in get_pending_approvals()])
	approve("KV Project", dir_project.name)
	dir_project.reload()
	check("the CEO completes it", dir_project.approval_status == "Approved")

	# ── Rejection returns it to the raiser ───────────────────────
	reject_project = raise_project("ZZ Approval Reject", PM)
	frappe.set_user(PC)
	reject("KV Project", reject_project.name, "Needs a budget")
	reject_project.reload()
	check("a rejected project is marked rejected",
		reject_project.approval_status == "Rejected")
	check("nobody is left waiting on a rejected project",
		not reject_project.pending_approver and not reject_project.pending_approver_role)
	check("its history records the rejection",
		any(r.action == "Rejected" for r in reject_project.approval_log))

	# ── Queues are per person ────────────────────────────────────
	queue_project = raise_project("ZZ Approval Queue", PM)
	frappe.set_user(PM)
	check("the raiser has an empty queue",
		queue_project.name not in [i["name"] for i in get_pending_approvals()])
	frappe.set_user("pc2_test@krushivikas.org")
	check("a different coordinator does not see it",
		queue_project.name not in [i["name"] for i in get_pending_approvals()])
	frappe.set_user(PC)
	check("the named coordinator does see it",
		queue_project.name in [i["name"] for i in get_pending_approvals()])

	frappe.set_user("Administrator")
	frappe.db.rollback()
	print("\n  (all test records rolled back)")

	print()
	if failures:
		print(f"=== {len(failures)} FAILURE(S) ===")
		for f in failures:
			print(f"  - {f}")
	else:
		print("=== ALL APPROVAL CHECKS PASSED ===")

	return not failures
