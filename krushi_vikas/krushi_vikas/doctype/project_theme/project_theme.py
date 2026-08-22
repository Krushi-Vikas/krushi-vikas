from frappe.utils.nestedset import NestedSet

class ProjectTheme(NestedSet):
	nsm_parent_field = 'parent_project_theme'
