import frappe
from frappe.utils import flt, getdate, nowdate

from krushi_vikas.krushi_vikas.page.krushi_dashboard.krushi_dashboard import (
	build_scope,
	can_create_project,
	can_preview,
	require_preview_admin,
)

CARD_FIELDS = (
	"name",
	"project_name",
	"theme",
	"status",
	"project_phase",
	"journey_stage",
	"workflow_state",
	"project_coordinator",
	"project_manager",
	"start_date",
	"end_date",
	"budget",
	"actual_amount_spent",
	"remaining_funds",
	"proposal",
)


@frappe.whitelist()
def get_project_cards(search=None, status=None, preview_user=None):
	"""Role-scoped project cards.

	Same scoping rule as the dashboard — the board is a different shape on
	the same data, not a second set of rules.
	"""
	viewer = frappe.session.user
	preview = None

	if preview_user and preview_user != viewer:
		require_preview_admin()
		if not frappe.db.exists("User", preview_user):
			frappe.throw(frappe._("Unknown user: {0}").format(preview_user))
		preview = {"viewer": viewer, "previewing": preview_user}

	user = preview_user if preview else viewer
	scope = build_scope(user)

	# A field officer works from tasks only and has no project-level view.
	if scope.get("task_only"):
		payload = empty_payload(user, scope, preview)
		payload["task_only"] = True
		return payload

	filters = {}

	if not scope["org_wide"]:
		if not scope["project_names"]:
			return empty_payload(user, scope, preview)
		filters["name"] = ["in", list(scope["project_names"])]

	if status:
		filters["status"] = status

	projects = frappe.get_all(
		"KV Project",
		filters=filters,
		or_filters=(
			[["project_name", "like", f"%{search}%"], ["theme", "like", f"%{search}%"]]
			if search
			else None
		),
		fields=list(CARD_FIELDS),
		order_by="modified desc",
		limit_page_length=200,
	)

	decorate(projects)

	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name") or user,
		"role_label": scope["role_label"],
		"scope_label": scope["scope_label"],
		"is_org_wide": scope["org_wide"],
		"can_preview": can_preview(),
		"preview": preview,
		"task_only": False,
		"can_create_project": can_create_project(user),
		"projects": projects,
		"facets": build_facets(projects),
	}


def empty_payload(user, scope, preview):
	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name") or user,
		"role_label": scope["role_label"],
		"scope_label": scope["scope_label"],
		"is_org_wide": scope["org_wide"],
		"can_preview": can_preview(),
		"preview": preview,
		"task_only": scope.get("task_only", False),
		"can_create_project": can_create_project(user),
		"projects": [],
		"facets": {"status": {}, "total": 0},
	}


def decorate(projects):
	"""Attach the derived numbers each card shows.

	Counts are fetched in two grouped queries rather than per card, so the
	board stays flat regardless of how many projects are in scope.
	"""
	if not projects:
		return

	names = [p.name for p in projects]
	today = getdate(nowdate())

	# One pass over the activities gives both the per-project count and the
	# activity -> project map the task rollup needs.
	activity_counts = {}
	activity_to_project = {}

	for row in frappe.get_all(
		"Activity",
		filters={"project": ["in", names]},
		fields=["name", "project"],
		limit_page_length=0,
	):
		activity_to_project[row.name] = row.project
		activity_counts[row.project] = activity_counts.get(row.project, 0) + 1

	task_counts = {}

	if activity_to_project:
		for row in frappe.get_all(
			"Task",
			filters={"custom_activity": ["in", list(activity_to_project)]},
			fields=["name", "custom_activity", "status"],
			limit_page_length=0,
		):
			project = activity_to_project.get(row.custom_activity)
			if not project:
				continue
			bucket = task_counts.setdefault(project, {"total": 0, "open": 0})
			bucket["total"] += 1
			if row.status not in ("Completed", "Cancelled"):
				bucket["open"] += 1

	for project in projects:
		budget = flt(project.budget)
		spent = flt(project.actual_amount_spent)

		project["spend_pct"] = round((spent / budget) * 100) if budget else 0
		project["overspent"] = budget > 0 and spent > budget
		project["activity_count"] = activity_counts.get(project.name, 0)
		project["task_count"] = task_counts.get(project.name, {}).get("total", 0)
		project["open_task_count"] = task_counts.get(project.name, {}).get("open", 0)

		project["days_left"] = None
		project["is_overdue"] = False

		if project.end_date:
			end = getdate(project.end_date)
			project["days_left"] = (end - today).days
			project["is_overdue"] = (
				end < today and project.status not in ("Completed", "Cancelled")
			)

		project["elapsed_pct"] = elapsed_pct(project, today)

	return projects


def elapsed_pct(project, today):
	"""How far through its planned window the project is."""
	if not (project.start_date and project.end_date):
		return 0

	start = getdate(project.start_date)
	end = getdate(project.end_date)
	span = (end - start).days

	if span <= 0:
		return 100 if today >= end else 0

	return max(0, min(100, round(((today - start).days / span) * 100)))


def build_facets(projects):
	status = {}

	for project in projects:
		if project.status:
			status[project.status] = status.get(project.status, 0) + 1

	return {"status": status, "total": len(projects)}
