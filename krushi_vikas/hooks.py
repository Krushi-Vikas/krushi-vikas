app_name = "krushi_vikas"
app_title = "Krushi Vikas"
app_publisher = "Krushi Vikas"
app_description = "Krushi Vikas Agri and Watershed Project Management"
app_email = "admin@krushivikas.org"
app_license = "mit"

# Task, Project and Project Type come from ERPNext. Without this, installing
# krushi_vikas onto a bench that has no ERPNext leaves every link field and
# custom field dangling.
required_apps = ["erpnext"]

# Roles, DocPerms, custom fields, the workspace and the workflows all live in
# the database, not in the doctype JSON. setup_site.run() creates them and is
# idempotent, so a fresh install gets a working site and an existing site is
# repaired by the next migrate.
after_install = "krushi_vikas.setup_site.run"
after_migrate = "krushi_vikas.setup_site.run"

# Document Events Hooks
doc_events = {
	"Task": {
		"validate": [
			"krushi_vikas.api.enforce_dependency_gate",
			"krushi_vikas.api.enforce_task_least_privilege"
		],
		"on_trash": "krushi_vikas.api.cleanup_activity_task_row"
	},
	"Activity Outcome": {
		"on_update_after_submit": "krushi_vikas.api.push_actual_to_kre",
		"on_submit": "krushi_vikas.api.push_actual_to_kre"
	},
	"Project": {
		"validate": "krushi_vikas.api.validate_project_finances_and_activities",
		"on_update": "krushi_vikas.api.sync_project_activities"
	},
	"KV Project": {
		"validate": "krushi_vikas.api.enforce_project_least_privilege"
	},
	"Activity": {
		"validate": "krushi_vikas.api.enforce_activity_least_privilege"
	}
}

# Permission Hooks for Role-based Least Privilege
has_permission = {
	"KV Project": "krushi_vikas.api.has_project_permission",
	"Project": "krushi_vikas.api.has_project_permission",
	"Activity": "krushi_vikas.api.has_activity_permission",
	"Task": "krushi_vikas.api.has_task_permission"
}

doctype_js = {
	"Project": "public/js/project_custom.js"
}

# Website Route Rules
website_route_rules = [
	{"from_route": "/task_list", "to_route": "task_list"},
	{"from_route": "/tasks", "to_route": "task_list"},
]

# Fixtures for deployment & version control
fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "Krushi Vikas"]]},
	{"dt": "Property Setter", "filters": [["module", "=", "Krushi Vikas"]]},
	{"dt": "Role", "filters": [["name", "in", [
		"Field Officer", "Project Manager", "Project Coordinator",
		"Project Director", "CEO"
	]]]}
]

