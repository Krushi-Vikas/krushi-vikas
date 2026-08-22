app_name = "krushi_vikas"
app_title = "Krushi Vikas"
app_publisher = "Krushi Vikas"
app_description = "Krushi Vikas Agri and Watershed Project Management"
app_email = "admin@krushivikas.org"
app_license = "mit"

# Document Events Hooks
doc_events = {
	"Task": {
		"validate": "krushi_vikas.api.enforce_dependency_gate"
	},
	"Activity Outcome": {
		"on_update_after_submit": "krushi_vikas.api.push_actual_to_kre",
		"on_submit": "krushi_vikas.api.push_actual_to_kre"
	},
	"Project": {
		"validate": "krushi_vikas.api.validate_project_finances_and_activities",
		"on_update": "krushi_vikas.api.sync_project_activities"
	}
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
		"Field Officer", "Project Coordinator", "Project Manager",
		"Project Director", "CEO"
	]]]}
]

