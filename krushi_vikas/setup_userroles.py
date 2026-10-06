import frappe

def execute():
    setup_test_users()
    disable_unused_roles()
    frappe.db.commit()
    print("Default app, test users, and role cleanup completed successfully!")




def setup_test_users():
    print("Setting up one default test user per role...")

    role_users = [
        {"role": "System Manager",      "email": "admin@krushivikas.test"},
        {"role": "Field Officer",       "email": "fieldofficer@krushivikas.test"},
        {"role": "Project Manager",     "email": "projectmanager@krushivikas.test"},
        {"role": "Project Coordinator", "email": "projectcoordinator@krushivikas.test"},
        {"role": "Project Director",    "email": "projectdirector@krushivikas.test"},
        {"role": "CEO",                 "email": "ceo@krushivikas.test"},
    ]

    for ru in role_users:
        if not frappe.db.exists("User", ru["email"]):
            user = frappe.new_doc("User")
            user.email = ru["email"]
            user.first_name = ru["role"]
            user.send_welcome_email = 0
            user.new_password = "krushivikas.test"
            user.default_app = "krushi_vikas"
            user.default_workspace = "Krushi Dashboard"
            user.insert(ignore_permissions=True)
            user.add_roles(ru["role"])
            print(f"Created {ru['email']} with role {ru['role']}")
        else:
            user = frappe.get_doc("User", ru["email"])
            if ru["role"] not in [r.role for r in user.roles]:
                user.add_roles(ru["role"])
            user.default_app = "krushi_vikas"
            user.default_workspace = "Krushi Dashboard"
            user.save(ignore_permissions=True)
            print(f"{ru['email']} already existed — ensured role and defaults")


def disable_unused_roles():
    print("Disabling unused ERPNext/Frappe roles...")

    roles_to_keep = {
        # Your custom roles
        "Field Officer",
        "Project Manager",
        "Project Coordinator",
        "Project Director",
        "CEO",
        # Core roles required for Frappe/ERPNext to function — never disable these
        "Administrator",
        "System Manager",
        "All",
        "Guest",
        "Desk User",
    }

    all_roles = frappe.get_all("Role", fields=["name", "disabled"])
    for r in all_roles:
        if r.name not in roles_to_keep and not r.disabled:
            frappe.db.set_value("Role", r.name, "disabled", 1)
            print(f"Disabled role: {r.name}")