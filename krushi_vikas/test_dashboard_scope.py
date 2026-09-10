"""Dashboard scoping checks.

Run with:
    bench --site krushivikas.local execute krushi_vikas.test_dashboard_scope.run

Verifies that get_dashboard_data only returns the projects a given user is
actually responsible for, per role.
"""

import frappe
from datetime import date

from krushi_vikas.krushi_vikas.page.krushi_dashboard.krushi_dashboard import (
	build_scope,
	get_dashboard_data,
	get_preview_options,
)

TEST_USERS = {
	"pc1_test@krushivikas.org": "Project Coordinator",
	"pc2_test@krushivikas.org": "Project Coordinator",
	"pm1_test@krushivikas.org": "Project Manager",
	"fo1_test@krushivikas.org": "Field Officer",
	"dir_test@krushivikas.org": "Project Director",
}

PROJECT_A = "Dashboard Scope Test A"
PROJECT_B = "Dashboard Scope Test B"


def run():
	print("=== TESTING ROLE-SCOPED DASHBOARD ===")

	frappe.set_user("Administrator")
	ensure_users()
	ensure_projects()
	frappe.db.commit()

	failures = []

	def check(label, condition):
		print(f"  {'PASS' if condition else 'FAIL'}  {label}")
		if not condition:
			failures.append(label)

	year = date.today().year

	# Coordinator 1 owns Project A only.
	frappe.set_user("pc1_test@krushivikas.org")
	data = get_dashboard_data(year)
	names = project_names(data)
	check("PC1 sees Project A", PROJECT_A in names)
	check("PC1 does NOT see Project B", PROJECT_B not in names)
	check("PC1 scope is personal", data["is_org_wide"] is False)
	check("PC1 role label", data["role_label"] == "Project Coordinator")

	# Coordinator 2 owns Project B only — the mirror case.
	frappe.set_user("pc2_test@krushivikas.org")
	names = project_names(get_dashboard_data(year))
	check("PC2 sees Project B", PROJECT_B in names)
	check("PC2 does NOT see Project A", PROJECT_A not in names)

	# Project Manager is named on Project A only. This is the case the old
	# dashboard got wrong — managers used to see the whole portfolio.
	frappe.set_user("pm1_test@krushivikas.org")
	data = get_dashboard_data(year)
	names = project_names(data)
	check("PM1 sees Project A", PROJECT_A in names)
	check("PM1 does NOT see Project B", PROJECT_B not in names)
	check("PM1 is not org-wide", data["is_org_wide"] is False)

	# Field Officer works from tasks only — no project level at all now.
	frappe.set_user("fo1_test@krushivikas.org")
	data = get_dashboard_data(year)
	check("FO1 stats are personal", "my_tasks" in data["stats"])
	check("FO1 is task-only", data["task_only"] is True)
	check("FO1 sees no projects at all", not project_names(data))
	check("FO1 has no Annual Plan", data["can_see_plan"] is False)
	check("FO1 cannot create projects", data["can_create_project"] is False)

	# Coordinators and managers are scoped but keep project-level views.
	frappe.set_user("pc1_test@krushivikas.org")
	pc = get_dashboard_data(year)
	check("PC is not task-only", pc["task_only"] is False)
	check("PC has no Annual Plan", pc["can_see_plan"] is False)

	# Project Director is scoped like everyone below them: only what is
	# assigned. They keep the Annual Plan panel.
	frappe.set_user("dir_test@krushivikas.org")
	data = get_dashboard_data(year)
	names = project_names(data)
	check("Director is NOT org-wide", data["is_org_wide"] is False)
	check("Director sees nothing unassigned", not (names & {PROJECT_A, PROJECT_B}))
	check("Director keeps the Annual Plan", data["can_see_plan"] is True)

	# Assigning a project to the director brings it into their scope.
	frappe.set_user("Administrator")
	assign_project(PROJECT_A, "dir_test@krushivikas.org")
	frappe.set_user("dir_test@krushivikas.org")
	check("Director sees a project assigned to them",
		PROJECT_A in project_names(get_dashboard_data(year)))

	# CEO stays org-wide.
	frappe.set_user("ceo_test@krushivikas.org")
	data = get_dashboard_data(year)
	check("CEO is org-wide", data["is_org_wide"] is True)
	check("CEO keeps the Annual Plan", data["can_see_plan"] is True)

	# A user with no Krushi Vikas role sees nothing.
	frappe.set_user("Administrator")
	scope = build_scope("pc1_test@krushivikas.org", roles=["Guest"])
	check("Unroled user gets an empty scope", scope["project_names"] == set())

	# ── Administrator role preview ───────────────────────────
	frappe.set_user("Administrator")

	own = get_dashboard_data(year)
	check("Admin may preview", own["can_preview"] is True)
	check("Admin's own view is not a preview", own["preview"] is None)

	as_fo = get_dashboard_data(year, preview_user="fo1_test@krushivikas.org")
	check("Preview reports the previewed user", as_fo["user"] == "fo1_test@krushivikas.org")
	check("Preview applies that user's role", as_fo["role_label"] == "Field Officer")
	# A field officer is task-only, so previewing one shows no projects at
	# all — the preview must reproduce their view, not a softened version.
	check("Preview reproduces the task-only view", as_fo["task_only"] is True)
	check("Preview shows a field officer no projects", not project_names(as_fo))
	check("Preview hides the plan from a field officer", as_fo["can_see_plan"] is False)

	# Previewing a coordinator still narrows to their own projects.
	as_pc = get_dashboard_data(year, preview_user="pc1_test@krushivikas.org")
	check(
		"Preview narrows a coordinator to their own projects",
		PROJECT_A in project_names(as_pc) and PROJECT_B not in project_names(as_pc),
	)
	check("Preview records who is previewing", as_fo["preview"]["viewer"] == "Administrator")
	check("Preview does NOT switch the session", frappe.session.user == "Administrator")

	from krushi_vikas.api import has_project_permission, has_task_permission

	fo = "fo1_test@krushivikas.org"
	check("FO cannot create projects",
		has_project_permission(None, "create", fo) is False)
	check("FO cannot write projects",
		has_project_permission(None, "write", fo) is False)
	check("FO can write tasks",
		bool(has_task_permission(None, "write", fo)) is True)

	options = get_preview_options("Field Officer")
	check(
		"Role filter lists only that role's users",
		"fo1_test@krushivikas.org" in [u["name"] for u in options["users"]]
		and "pc1_test@krushivikas.org" not in [u["name"] for u in options["users"]],
	)

	# ── The preview must be administrator-only ───────────────
	frappe.set_user("pc1_test@krushivikas.org")
	check("Non-admin cannot preview", get_dashboard_data(year)["can_preview"] is False)
	check(
		"Non-admin is blocked from previewing another user",
		raises_permission_error(
			lambda: get_dashboard_data(year, preview_user="fo1_test@krushivikas.org")
		),
	)
	check(
		"Non-admin is blocked from listing preview options",
		raises_permission_error(get_preview_options),
	)

	frappe.set_user("Administrator")

	print()
	if failures:
		print(f"=== {len(failures)} FAILURE(S) ===")
		for failure in failures:
			print(f"  - {failure}")
	else:
		print("=== ALL DASHBOARD SCOPE CHECKS PASSED ===")

	return not failures


def assign_project(project_name, user):
	"""Frappe's own assignment — how a director is given a project."""
	name = frappe.get_all("KV Project", filters={"project_name": project_name}, pluck="name")[0]

	if frappe.db.exists("ToDo", {"reference_type": "KV Project",
			"reference_name": name, "allocated_to": user}):
		return

	todo = frappe.new_doc("ToDo")
	todo.reference_type = "KV Project"
	todo.reference_name = name
	todo.allocated_to = user
	todo.description = f"Own {project_name}"
	todo.insert(ignore_permissions=True)
	frappe.db.commit()


def raises_permission_error(fn):
	try:
		fn()
	except frappe.PermissionError:
		return True
	return False


def project_names(data):
	return {project.get("project_name") for project in data["projects"]}


def ensure_users():
	for email, role in TEST_USERS.items():
		if not frappe.db.exists("User", email):
			user = frappe.new_doc("User")
			user.email = email
			user.first_name = email.split("_")[0].upper()
			user.enabled = 1
			user.user_type = "System User"
			user.append("roles", {"role": role})
			user.insert(ignore_permissions=True)
			continue

		user = frappe.get_doc("User", email)
		if role not in [r.role for r in user.roles]:
			user.append("roles", {"role": role})
			user.save(ignore_permissions=True)


def ensure_projects():
	year = date.today().year

	specs = [
		{
			"project_name": PROJECT_A,
			"project_coordinator": "pc1_test@krushivikas.org",
			"project_manager": "pm1_test@krushivikas.org",
			"field_officer": "fo1_test@krushivikas.org",
		},
		{
			"project_name": PROJECT_B,
			"project_coordinator": "pc2_test@krushivikas.org",
			"project_manager": None,
			"field_officer": None,
		},
	]

	for spec in specs:
		existing = frappe.get_all(
			"KV Project", filters={"project_name": spec["project_name"]}, pluck="name"
		)

		for name in existing:
			frappe.delete_doc("KV Project", name, force=True, ignore_permissions=True)

		project = frappe.new_doc("KV Project")
		project.project_name = spec["project_name"]
		project.status = "In Progress"
		project.project_coordinator = spec["project_coordinator"]
		project.project_manager = spec["project_manager"]
		project.start_date = f"{year}-01-01"
		project.end_date = f"{year}-12-31"

		if spec["field_officer"]:
			project.append(
				"activities",
				{
					"activity_name": "Scope test activity",
					"assignee": spec["field_officer"],
					"status": "In Progress",
					"start_date": f"{year}-01-01",
					"end_date": f"{year}-12-31",
				},
			)

		project.insert(ignore_permissions=True)
