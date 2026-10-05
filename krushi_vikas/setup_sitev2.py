import frappe

def execute():
    setup_default_app()
    setup_test_users()
    frappe.db.commit()

def setup_default_app():
    print("Setting default app and workspace for all users...")
    frappe.db.set_value("System Settings", "System Settings", "default_app", "krushi_vikas")

    frappe.db.sql("""
        UPDATE `tabUser`
        SET default_app = %s,
            default_workspace = %s
        WHERE user_type = 'System User'
    """, ("krushi_vikas", "Krushi Vikas"))

    frappe.clear_cache()
    print("Default app and workspace set for all users.")

def setup_test_users():
    print("Setting up one default test user per role...")

    role_users = [
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
            user.new_password = "admin"
            user.default_app = "krushi_vikas"
            user.default_workspace = "Krushi Vikas"
            user.insert(ignore_permissions=True)
            user.add_roles(ru["role"])
            print(f"Created {ru['email']} with role {ru['role']}")
        else:
            user = frappe.get_doc("User", ru["email"])
            if ru["role"] not in [r.role for r in user.roles]:
                user.add_roles(ru["role"])
            user.default_app = "krushi_vikas"
            user.default_workspace = "Krushi Vikas"
            user.save(ignore_permissions=True)
            print(f"{ru['email']} already existed — ensured role and defaults")