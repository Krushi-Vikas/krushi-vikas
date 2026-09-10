import frappe
from datetime import date

# Roles that may see the entire portfolio. Mirrors the hierarchy enforced in
# krushi_vikas.api.has_project_permission so the dashboard never shows a user
# something they could not open anyway.
ORG_WIDE_ROLES = ("Administrator", "System Manager", "CEO", "Project Director")

# Most senior role first — the first match becomes the user's primary role.
ROLE_PRIORITY = (
	"Administrator",
	"System Manager",
	"CEO",
	"Project Director",
	"Project Coordinator",
	"Project Manager",
	"Field Officer",
)

OPEN_TASK_STATUSES = ("Open", "Working", "Pending Review", "Overdue")
CLOSED_TASK_STATUSES = ("Completed", "Cancelled")


# Roles an Administrator may preview. Ordered most senior first.
PREVIEWABLE_ROLES = (
	"CEO",
	"Project Director",
	"Project Coordinator",
	"Project Manager",
	"Field Officer",
)

@frappe.whitelist()
def get_dashboard_data(year=None, preview_user=None):
	"""Role-scoped dashboard payload.

	Every user gets the same shape, but the rows are limited to what that
	person is actually responsible for. Scoping happens here, server side —
	the client never sends a user or a filter.

	`preview_user` renders the dashboard as somebody else. It is read-only
	and restricted to administrators; the session is never switched.
	"""
	year = int(year or date.today().year)

	viewer = frappe.session.user
	preview = None

	if preview_user and preview_user != viewer:
		require_preview_admin()
		if not frappe.db.exists("User", preview_user):
			frappe.throw(frappe._("Unknown user: {0}").format(preview_user))
		preview = {"viewer": viewer, "previewing": preview_user}

	user = preview_user if preview else viewer
	roles = frappe.get_roles(user)
	scope = build_scope(user, roles)

	year_start = f"{year}-01-01"
	year_end = f"{year}-12-31"

	projects = get_scoped_projects(scope, year_start, year_end)
	project_names = [project.name for project in projects]

	my_activities = get_my_activities(user)
	my_tasks = get_my_tasks(user)

	stats = get_project_stats(projects, project_names, my_activities, my_tasks)

	recent_projects = sorted(
		projects,
		key=lambda project: project.start_date or date.min,
		reverse=True,
	)[:5]

	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name") or user,
		"roles": roles,
		"role_label": scope["role_label"],
		"is_org_wide": scope["org_wide"],
		"scope_label": scope["scope_label"],
		"year": year,
		"stats": stats,
		"projects": projects,
		"recent_projects": recent_projects,
		"my_activities": my_activities,
		"my_tasks": my_tasks,
		"preview": preview,
		"can_preview": can_preview(),
	}


# ─────────────────────────────────────────────
# Administrator role preview
# ─────────────────────────────────────────────

def can_preview(user=None):
	"""Only administrators may render the dashboard as somebody else."""
	user = user or frappe.session.user

	if user == "Administrator":
		return True

	return "System Manager" in frappe.get_roles(user)


def require_preview_admin():
	if not can_preview():
		frappe.throw(
			frappe._("Only administrators can preview another role."),
			frappe.PermissionError,
		)


@frappe.whitelist()
def get_preview_options(role=None):
	"""Roles an administrator can preview, and the people holding them.

	Scoping is per person, not per role — a Project Coordinator with no
	projects sees an empty dashboard — so the role picker narrows the user
	list rather than standing in for a user.
	"""
	require_preview_admin()

	roles = []

	for role_name in PREVIEWABLE_ROLES:
		roles.append(
			{
				"role": role_name,
				"user_count": frappe.db.count(
					"Has Role", {"role": role_name, "parenttype": "User"}
				),
				"is_org_wide": role_name in ORG_WIDE_ROLES,
			}
		)

	users = get_users_for_role(role)

	return {"roles": roles, "users": users, "selected_role": role}


def get_users_for_role(role=None):
	role_filter = [role] if role else list(PREVIEWABLE_ROLES)

	user_ids = frappe.get_all(
		"Has Role",
		filters={"role": ["in", role_filter], "parenttype": "User"},
		pluck="parent",
	)

	if not user_ids:
		return []

	users = frappe.get_all(
		"User",
		filters={"name": ["in", list(set(user_ids))], "enabled": 1},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)

	for user in users:
		user_roles = frappe.get_roles(user.name)
		user["role_label"] = get_primary_role(user.name, set(user_roles))

	return users


def build_scope(user, roles=None):
	"""Work out exactly which projects this user is allowed to see.

	Returns a dict with:
	  org_wide     — True when no project filtering applies
	  project_names— explicit set of KV Project names (only when not org_wide)
	  role_label   — primary role, for display
	  scope_label  — human sentence explaining the filter
	"""
	roles = set(roles if roles is not None else frappe.get_roles(user))
	role_label = get_primary_role(user, roles)

	if user == "Administrator" or roles.intersection(ORG_WIDE_ROLES):
		return {
			"org_wide": True,
			"project_names": None,
			"role_label": role_label,
			"scope_label": "Showing all projects across the organisation.",
		}

	project_names = set()

	if "Project Coordinator" in roles:
		# A coordinator owns the projects assigned to them, plus anything
		# they created themselves.
		project_names.update(
			frappe.get_all(
				"KV Project",
				or_filters=[
					["project_coordinator", "=", user],
					["owner", "=", user],
				],
				pluck="name",
			)
		)

	if "Project Manager" in roles:
		# A manager is named on the project, or owns activities inside it.
		project_names.update(
			frappe.get_all("KV Project", filters={"project_manager": user}, pluck="name")
		)
		project_names.update(projects_from_activities(user))

	if "Field Officer" in roles:
		# A field officer only reaches a project through the work assigned
		# to them: an activity, a planned activity row, or a task.
		project_names.update(projects_from_activities(user))
		project_names.update(projects_from_tasks(user))

	scope_label = (
		"Showing only the projects assigned to you."
		if project_names
		else "No projects are assigned to you yet."
	)

	return {
		"org_wide": False,
		"project_names": project_names,
		"role_label": role_label,
		"scope_label": scope_label,
	}


def projects_from_activities(user):
	"""KV Projects reachable through activities assigned to this user."""
	names = set(
		frappe.get_all("Activity", filters={"assignee": user}, pluck="project") or []
	)

	# The planning rows inside KV Project.activities carry their own assignee.
	names.update(
		frappe.get_all(
			"KV Project Activity",
			filters={"assignee": user, "parenttype": "KV Project"},
			pluck="parent",
		)
		or []
	)

	names.discard(None)
	names.discard("")
	return names


def projects_from_tasks(user):
	"""KV Projects reachable through tasks assigned to this user."""
	activity_names = {
		task.custom_activity
		for task in get_assigned_tasks(user, fields=["custom_activity"])
		if task.custom_activity
	}

	if not activity_names:
		return set()

	names = set(
		frappe.get_all(
			"Activity",
			filters={"name": ["in", list(activity_names)]},
			pluck="project",
		)
		or []
	)

	names.discard(None)
	names.discard("")
	return names


def get_assigned_tasks(user, fields, limit=None):
	"""Tasks this user is personally on — via the Krushi Vikas owner field or
	Frappe's own ToDo assignment."""
	return frappe.get_all(
		"Task",
		or_filters=[
			["custom_activity_owner", "=", user],
			["_assign", "like", f"%{user}%"],
		],
		fields=fields,
		limit_page_length=limit or 0,
	)


def get_primary_role(user, roles):
	if user == "Administrator":
		return "Administrator"

	for role in ROLE_PRIORITY:
		if role in roles:
			return role

	return "User"


# ─────────────────────────────────────────────
# Scoped queries
# ─────────────────────────────────────────────

def get_scoped_projects(scope, year_start, year_end):
	filters = {
		"start_date": ["<=", year_end],
		"end_date": [">=", year_start],
	}

	if not scope["org_wide"]:
		if not scope["project_names"]:
			return []
		filters["name"] = ["in", list(scope["project_names"])]

	return frappe.get_all(
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


def get_my_activities(user):
	"""Activities this user personally owns — shown to every role, including
	org-wide ones, so the "My Work" panel is always about the person."""
	activities = frappe.get_all(
		"Activity",
		filters={"assignee": user},
		fields=[
			"name",
			"activity_name",
			"project",
			"status",
			"start_date",
			"end_date",
			"planned_budget",
			"actual_expenditure",
		],
		order_by="end_date asc",
		limit_page_length=25,
	)

	today = date.today()

	for activity in activities:
		activity["is_overdue"] = is_overdue(
			activity.end_date, activity.status, ("Completed", "Cancelled"), today
		)

	return activities


def get_my_tasks(user):
	tasks = get_assigned_tasks(
		user,
		fields=[
			"name",
			"subject",
			"status",
			"priority",
			"project",
			"custom_activity",
			"exp_start_date",
			"exp_end_date",
		],
		limit=50,
	)

	activity_names = [task.custom_activity for task in tasks if task.custom_activity]
	activity_labels = {}

	if activity_names:
		activity_labels = {
			row.name: row.activity_name
			for row in frappe.get_all(
				"Activity",
				filters={"name": ["in", list(set(activity_names))]},
				fields=["name", "activity_name"],
			)
		}

	today = date.today()

	for task in tasks:
		task["activity_label"] = activity_labels.get(
			task.custom_activity, task.custom_activity or ""
		)
		task["is_overdue"] = is_overdue(
			task.exp_end_date, task.status, CLOSED_TASK_STATUSES, today
		)

	# Open work first, then by due date — nulls last.
	tasks.sort(
		key=lambda task: (
			task.status in CLOSED_TASK_STATUSES,
			task.exp_end_date or date.max,
		)
	)

	return tasks


def is_overdue(due_date, status, closed_statuses, today):
	if not due_date or status in closed_statuses:
		return False

	if isinstance(due_date, str):
		due_date = frappe.utils.getdate(due_date)

	return due_date < today


# ─────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────

def get_project_stats(projects, project_names, my_activities, my_tasks):
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
	planned_activity_count = 0

	if project_names:
		activity_count = frappe.db.count("Activity", {"project": ["in", project_names]})
		planned_activity_count = frappe.db.count(
			"KV Project Activity",
			{
				"parent": ["in", project_names],
				"parenttype": "KV Project",
			},
		)

	open_tasks = [task for task in my_tasks if task.status not in CLOSED_TASK_STATUSES]

	return {
		"total_projects": len(projects),
		"active_projects": (
			status_counts["In Progress"] + status_counts["Deployed"]
		),
		"planning_projects": status_counts["Planning"],
		"completed_projects": status_counts["Completed"],
		"cancelled_projects": status_counts["Cancelled"],
		"activities": activity_count,
		"planned_activities": planned_activity_count,
		"my_activities": len(my_activities),
		"my_open_activities": len(
			[a for a in my_activities if a.status not in ("Completed", "Cancelled")]
		),
		"my_tasks": len(my_tasks),
		"pending_tasks": len(open_tasks),
		"overdue_tasks": len([task for task in my_tasks if task.is_overdue]),
	}
