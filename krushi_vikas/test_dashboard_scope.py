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

	# Field Officer reaches Project A through the planned activity row.
	frappe.set_user("fo1_test@krushivikas.org")
	data = get_dashboard_data(year)
	names = project_names(data)
	check("FO1 sees Project A", PROJECT_A in names)
	check("FO1 does NOT see Project B", PROJECT_B not in names)
	check("FO1 stats are personal", "my_tasks" in data["stats"])

	# Project Director is org-wide.
	frappe.set_user("dir_test@krushivikas.org")
	data = get_dashboard_data(year)
	names = project_names(data)
	check("Director sees Project A", PROJECT_A in names)
	check("Director sees Project B", PROJECT_B in names)
	check("Director scope is org-wide", data["is_org_wide"] is True)

	# A user with no Krushi Vikas role sees nothing.
	frappe.set_user("Administrator")
	scope = build_scope("pc1_test@krushivikas.org", roles=["Guest"])
	check("Unroled user gets an empty scope", scope["project_names"] == set())

	frappe.set_user("Administrator")

	print()
	if failures:
		print(f"=== {len(failures)} FAILURE(S) ===")
		for failure in failures:
			print(f"  - {failure}")
	else:
		print("=== ALL DASHBOARD SCOPE CHECKS PASSED ===")

	return not failures


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
