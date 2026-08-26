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
		or "Project Manager" in roles
	):
		return {}

	if "Project Coordinator" in roles:
		return {
			"project_coordinator": user,
		}

	if "Field Officer" in roles:
		project_names = frappe.get_all(
			"KV Project Activity",
			filters={
				"assignee": user,
				"parenttype": "KV Project",
			},
			pluck="parent",
		)

		return {
			"name": ["in", list(set(project_names)) or [""]],
		}

	return {
		"name": ["in", [""]],
	}


def get_primary_role(user, roles):
	if user == "Administrator" or "Administrator" in roles:
		return "Administrator"

	if "System Manager" in roles:
		return "System Manager"

	if "Project Manager" in roles:
		return "Project Manager"

	if "Project Coordinator" in roles:
		return "Project Coordinator"

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