import frappe


@frappe.whitelist()
def get_theme_cards(search=None):
	"""Every Theme with its Sub-themes and how many Activities use each,
	as one flat structure the card gallery groups client-side.
	"""
	theme_filters = {"is_group": 1}
	if search:
		theme_filters["theme_name"] = ["like", f"%{search}%"]

	themes = frappe.get_all(
		"Project Theme",
		filters=theme_filters,
		fields=["name", "theme_name", "description"],
		order_by="theme_name asc",
	)

	sub_themes = frappe.get_all(
		"Project Theme",
		filters={"is_group": 0},
		fields=["name", "theme_name", "parent_project_theme"],
		order_by="theme_name asc",
	)

	usage = {}
	for row in frappe.get_all(
		"Activity", fields=["theme", "sub_theme"], limit_page_length=0
	):
		if row.theme:
			usage[row.theme] = usage.get(row.theme, 0) + 1
		if row.sub_theme:
			usage[row.sub_theme] = usage.get(row.sub_theme, 0) + 1

	by_parent = {}
	for st in sub_themes:
		by_parent.setdefault(st.parent_project_theme, []).append(
			{"name": st.name, "theme_name": st.theme_name, "usage": usage.get(st.name, 0)}
		)

	for t in themes:
		t["usage"] = usage.get(t.name, 0)
		t["sub_themes"] = by_parent.get(t.name, [])

	return {
		"themes": themes,
		"can_create": frappe.has_permission("Project Theme", "create"),
	}
