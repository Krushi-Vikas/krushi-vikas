import frappe
from datetime import date


@frappe.whitelist()
def get_dashboard_data(year=None):
	year = int(year or date.today().year)

	user = frappe.session.user
	roles = frappe.get_roles(user)

	role_label = get_primary_role(user, roles)
	project_filters = get_project_filters(user, roles)

	year_start = f"{year}-01-01"
	year_end = f"{year}-12-31"

	filters = {
		**project_filters,
		"start_date": ["<=", year_end],
		"end_date": [">=", year_start],
	}

	projects = frappe.get_all(
		"KV Project",
		filters=filters,
		fields=[
			"name",
			"project_name",
			"theme",
			"project_phase",
			"status",
			"project_manager",
			"project_coordinator",
			"start_date",
			"end_date",
			"budget",
			"actual_amount_spent",
			"remaining_funds",
		],
		order_by="start_date asc",
	)

	project_names = [project.name for project in projects]

	stats = get_project_stats(projects, project_names)

	recent_projects = sorted(
		projects,
		key=lambda project: project.start_date or date.min,
		reverse=True,
	)[:5]

	return {
		"user": user,
		"roles": roles,
		"role_label": role_label,
		"year": year,
		"stats": stats,
		"projects": projects,
		"recent_projects": recent_projects,
	}


def get_project_filters(user, roles):
	if (
		user == "Administrator"
		or "System Manager" in roles
		or "Administrator" in roles
		or "CEO" in roles
		or "Project Director" in roles
	):
		return {}

	projects = set()

	if "Project Coordinator" in roles:
		projects.update(frappe.get_all("KV Project", filters={"project_coordinator": user}, pluck="name"))
	if "Project Manager" in roles:
		projects.update(frappe.get_all("KV Project", filters={"project_manager": user}, pluck="name"))

	# Activities assigned to user in KV Project Activity child table
	act_projects = frappe.get_all(
		"KV Project Activity",
		filters={"assignee": user, "parenttype": "KV Project"},
		pluck="parent"
	)
	projects.update(act_projects)

	# Standalone Activity assigned to user
	standalone_acts = frappe.get_all("Activity", filters={"assignee": user}, fields=["project"])
	for a in standalone_acts:
		if a.project:
			projects.add(a.project)
			kv_name = frappe.db.get_value("KV Project", {"project_name": a.project}, "name")
			if kv_name:
				projects.add(kv_name)

	# Tasks assigned to user (either direct user email or linked employee)
	emp_ids = frappe.get_all("Employee", filters={"user_id": user}, pluck="name") or []
	task_targets = [user] + emp_ids

	tasks = frappe.get_all(
		"Task",
		filters={"custom_activity_owner": ["in", task_targets]},
		fields=["project", "custom_activity"]
	)
	for t in tasks:
		if t.project:
			projects.add(t.project)
			kv_name = frappe.db.get_value("KV Project", {"project_name": t.project}, "name")
			if kv_name:
				projects.add(kv_name)
			erp_name = frappe.db.get_value("Project", t.project, "project_name")
			if erp_name:
				kv_name_erp = frappe.db.get_value("KV Project", {"project_name": erp_name}, "name")
				if kv_name_erp:
					projects.add(kv_name_erp)
		if t.custom_activity:
			p_name = frappe.db.get_value("Activity", t.custom_activity, "project")
			if p_name:
				projects.add(p_name)
				kv_name = frappe.db.get_value("KV Project", {"project_name": p_name}, "name")
				if kv_name:
					projects.add(kv_name)

	# Tasks assigned via Frappe _assign
	assigned_tasks = frappe.db.sql(
		"""SELECT project, custom_activity FROM `tabTask` WHERE _assign LIKE %s""",
		(f"%{user}%",),
		as_dict=True
	)
	for t in assigned_tasks:
		if t.project:
			projects.add(t.project)
			kv_name = frappe.db.get_value("KV Project", {"project_name": t.project}, "name")
			if kv_name:
				projects.add(kv_name)
		if t.custom_activity:
			p_name = frappe.db.get_value("Activity", t.custom_activity, "project")
			if p_name:
				projects.add(p_name)
				kv_name = frappe.db.get_value("KV Project", {"project_name": p_name}, "name")
				if kv_name:
					projects.add(kv_name)

	valid_projects = [p for p in projects if p and frappe.db.exists("KV Project", p)]
	return {
		"name": ["in", valid_projects or [""]],
	}


def get_primary_role(user, roles):
	if user == "Administrator" or "Administrator" in roles:
		return "Administrator"

	if "System Manager" in roles:
		return "System Manager"

	if "CEO" in roles:
		return "CEO"

	if "Project Director" in roles:
		return "Project Director"

	if "Project Coordinator" in roles:
		return "Project Coordinator"

	if "Project Manager" in roles:
		return "Project Manager"

	if "Field Officer" in roles:
		return "Field Officer"

	return "User"


def get_project_stats(projects, project_names):
	status_counts = {
		"Planning": 0,
		"In Progress": 0,
		"Deployed": 0,
		"Completed": 0,
		"Cancelled": 0,
	}

	for project in projects:
		if project.status in status_counts:
			status_counts[project.status] += 1

	activity_count = 0

	if project_names:
		activity_count = frappe.db.count(
			"KV Project Activity",
			{
				"parent": ["in", project_names],
				"parenttype": "KV Project",
			},
		)

	return {
		"total_projects": len(projects),
		"active_projects": (
			status_counts["In Progress"]
			+ status_counts["Deployed"]
		),
		"planning_projects": status_counts["Planning"],
		"completed_projects": status_counts["Completed"],
		"cancelled_projects": status_counts["Cancelled"],
		"activities": activity_count,
		"pending_tasks": 0,
	}