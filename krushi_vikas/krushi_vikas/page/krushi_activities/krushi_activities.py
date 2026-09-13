import frappe
from frappe.utils import flt, getdate, nowdate

from krushi_vikas.krushi_vikas.page.krushi_dashboard.krushi_dashboard import build_scope

CARD_FIELDS = (
	"name",
	"activity_name",
	"project",
	"theme",
	"sub_theme",
	"status",
	"assignee",
	"start_date",
	"end_date",
	"approved_budget",
	"total_expenditure",
	"target",
	"achievement",
)


@frappe.whitelist()
def get_activity_cards(search=None, status=None, theme=None):
	"""Role-scoped activity cards — same scoping rule as the dashboard and
	the project board, just one level down the hierarchy.
	"""
	user = frappe.session.user
	scope = build_scope(user)

	if scope.get("task_only"):
		return empty_payload(user, scope)

	filters = {}

	if not scope["org_wide"]:
		if not scope["project_names"]:
			return empty_payload(user, scope)
		filters["project"] = ["in", list(scope["project_names"])]

	if status:
		filters["status"] = status

	if theme:
		filters["theme"] = theme

	activities = frappe.get_all(
		"Activity",
		filters=filters,
		or_filters=(
			[["activity_name", "like", f"%{search}%"], ["theme", "like", f"%{search}%"]]
			if search
			else None
		),
		fields=list(CARD_FIELDS),
		order_by="modified desc",
		limit_page_length=200,
	)

	decorate(activities)

	return {
		"user": user,
		"role_label": scope["role_label"],
		"scope_label": scope["scope_label"],
		"is_org_wide": scope["org_wide"],
		"task_only": False,
		"activities": activities,
		"can_create": frappe.has_permission("Activity", "create"),
	}


def empty_payload(user, scope):
	return {
		"user": user,
		"role_label": scope["role_label"],
		"scope_label": scope["scope_label"],
		"is_org_wide": scope["org_wide"],
		"task_only": scope.get("task_only", False),
		"activities": [],
		"can_create": False,
	}


def decorate(activities):
	if not activities:
		return

	names = [a.name for a in activities]
	project_names = {a.project for a in activities if a.project}

	project_titles = {}
	if project_names:
		project_titles = dict(
			frappe.get_all(
				"KV Project",
				filters={"name": ["in", list(project_names)]},
				fields=["name", "project_name"],
				as_list=True,
			)
		)

	task_counts = {}
	for row in frappe.get_all(
		"Activity Task Detail",
		filters={"parent": ["in", names], "parenttype": "Activity"},
		fields=["parent", "status"],
		limit_page_length=0,
	):
		bucket = task_counts.setdefault(row.parent, {"total": 0, "open": 0})
		bucket["total"] += 1
		if row.status not in ("Completed", "Cancelled"):
			bucket["open"] += 1

	today = getdate(nowdate())

	for a in activities:
		a["project_title"] = project_titles.get(a.project) or a.project
		counts = task_counts.get(a.name, {"total": 0, "open": 0})
		a["task_total"] = counts["total"]
		a["task_open"] = counts["open"]
		a["task_done_pct"] = (
			round(((counts["total"] - counts["open"]) / counts["total"]) * 100)
			if counts["total"]
			else 0
		)
		a["is_overdue"] = bool(
			a.end_date and getdate(a.end_date) < today and a.status not in ("Completed", "Cancelled")
		)
		a["achievement_pct"] = (
			round((flt(a.achievement) / flt(a.target)) * 100) if flt(a.target) else 0
		)
		a["spend_pct"] = (
			round((flt(a.total_expenditure) / flt(a.approved_budget)) * 100)
			if flt(a.approved_budget)
			else 0
		)
