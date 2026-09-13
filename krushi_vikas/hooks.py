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
	},
	"Feedback Survey": {
		"validate": "krushi_vikas.api.enforce_feedback_survey_least_privilege",
		"on_submit": "krushi_vikas.notifications.notify_feedback_survey_submitted"
	}
}

app_include_css = [
	"/assets/krushi_vikas/css/krushi_dashboard.css"
]
# Permission Hooks for Role-based Least Privilege
has_permission = {
	"KV Project": "krushi_vikas.api.has_project_permission",
	"Project": "krushi_vikas.api.has_project_permission",
	"Activity": "krushi_vikas.api.has_activity_permission",
	"Task": "krushi_vikas.api.has_task_permission",
	"Feedback Survey": "krushi_vikas.api.has_feedback_survey_permission"
}

doctype_js = {
	"Project": "public/js/project_custom.js"
}

# Loaded on every Desk page. Redirects field-level roles back to Krushi
# Vikas if they land on anything outside it (ERPNext modules, Settings,
# the app switcher) — see the file for why this is a route guard and not
# a hidden sidebar link.
app_include_js = ["/assets/krushi_vikas/js/kiosk_mode.js"]

# The login page is a website page (not Desk), so it reads web_include_*
# rather than app_include_*. Scoped entirely under .for-login in the file
# itself — see login_theme.css — so it can't affect any other website page.
web_include_css = ["/assets/krushi_vikas/css/login_theme.css?v=2"]

# Where each role lands right after logging in — everyone, including
# System Manager/Administrator, opens straight to the dashboard rather
# than Frappe's generic app-switcher screen. Only System Manager is
# exempt from kiosk_mode.js's route guard, so they can still navigate
# elsewhere afterwards to administer the site.
role_home_page = {
	"System Manager": "app/krushi-dashboard",
	"CEO": "app/krushi-dashboard",
	"Project Director": "app/krushi-dashboard",
	"Project Coordinator": "app/krushi-dashboard",
	"Project Manager": "app/krushi-dashboard",
	"Field Officer": "app/krushi-dashboard",
}

# Puts Krushi Vikas on the Frappe "Apps" switcher screen (reached at bare
# /app) with our own logo instead of leaving only ERPNext/Framework's icons
# there. sequence_id 1 sorts it first. Swapping the logo later is a single
# file overwrite at public/images/logo.png — nothing here needs to change.
add_to_apps_screen = [
	{
		"name": "krushi_vikas",
		"logo": "/assets/krushi_vikas/images/logo.png?v=2",
		"title": "Krushi Vikas",
		"route": "/app/krushi-dashboard",
		"has_permission": "krushi_vikas.api.has_krushi_vikas_app_permission",
		"sequence_id": 1,
	}
]

scheduler_events = {
	"daily": [
		"krushi_vikas.notifications.run_daily_checks"
	]
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

