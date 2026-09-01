app_name = "krushi_vikas"
app_title = "Krushi Vikas"
app_publisher = "Krushi Vikas"
app_description = "Krushi Vikas Agri and Watershed Project Management"
app_email = "admin@krushivikas.org"
app_license = "mit"

# Document Events Hooks
doc_events = {
	"Task": {
		"validate": [
			"krushi_vikas.api.enforce_dependency_gate",
			"krushi_vikas.api.enforce_task_least_privilege"
		]
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

