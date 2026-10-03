import frappe
from frappe.utils.nestedset import NestedSet

class ProjectTheme(NestedSet):
	nsm_parent_field = 'parent_project_theme'

	def on_trash(self):
		"""Clear every reference to this Theme/Sub-Theme before the base
		NestedSet delete runs its own link-integrity check.

		Activity, the project's own Activities grid, and a template's
		Activity rows all carry a Link field to Project Theme — any of
		them still pointing here blocks the delete outright, the same
		class of bug fixed earlier for Activity/Task. A theme in active
		use should still be deletable; the activities that used it just
		go back to having none set, same as if it were never chosen.
		"""
		affected_projects = frappe.get_all(
			"Activity",
			or_filters=[["theme", "=", self.name], ["sub_theme", "=", self.name]],
			pluck="project",
		)

		for doctype in ("Activity", "KV Project Activity", "KV Project Template Activity"):
			for field in ("theme", "sub_theme"):
				frappe.db.set_value(doctype, {field: self.name}, field, None, update_modified=False)

		frappe.db.set_value("Task", {"custom_theme": self.name}, "custom_theme", None, update_modified=False)

		if affected_projects:
			from krushi_vikas.krushi_vikas.doctype.kv_project.kv_project import (
				recompute_themes_covered_db,
			)

			for project in set(filter(None, affected_projects)):
				recompute_themes_covered_db(project)

		super().on_trash()
