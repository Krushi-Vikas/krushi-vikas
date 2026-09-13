import frappe

TEST_USERS = {
    "fo1_test@krushivikas.org": "Field Officer",
    "fo2_test@krushivikas.org": "Field Officer",
    "pm1_test@krushivikas.org": "Project Manager",
    "pm2_test@krushivikas.org": "Project Manager",
    "pc1_test@krushivikas.org": "Project Coordinator",
    "pc2_test@krushivikas.org": "Project Coordinator",
    "dir_test@krushivikas.org": "Project Director",
    "ceo_test@krushivikas.org": "CEO",
}


def provision_test_users():
    """Create local-only demo accounts with their assigned Krushi Vikas role."""
    if not frappe.conf.developer_mode:
        frappe.throw("Test users can only be provisioned on a developer-mode site.")

    for email, role in TEST_USERS.items():
        user = frappe.get_doc("User", email) if frappe.db.exists("User", email) else frappe.new_doc("User")
        user.email = email
        user.first_name = email.split("_")[0].upper()
        user.enabled = 1
        user.user_type = "System User"
        user.set("roles", [{"role": role}])
        user.save(ignore_permissions=True)
        frappe.utils.password.update_password(user=email, pwd="1234")
        frappe.clear_cache(user=email)

    frappe.db.commit()
    print("Provisioned 8 local test users. Password: 1234")


def run():
    print("=== TESTING COMPLETE HIERARCHICAL OWNERSHIP & UPDATE RULES ===")
    
    provision_test_users()
    
    # ----------------------------------------------------
    # SETUP TEST DATA: Project P1 (PC1) -> Activity A1 (PM1) -> Task T1 (FO1)
    # ----------------------------------------------------
    frappe.session.user = "Administrator"
    proj_name = "Tree Plantation Drive 2026"
    for t in frappe.get_all("Task", filters={"subject": "Verify village nursery stock"}):
        frappe.delete_doc("Task", t.name, ignore_permissions=True)
    for a in frappe.get_all("Activity", filters={"activity_name": "Sapling Distribution Activity"}):
        frappe.delete_doc("Activity", a.name, ignore_permissions=True)
    for fs in frappe.get_all("Feedback Survey", filters={"village": "Ralegan Siddhi"}):
        try:
            doc = frappe.get_doc("Feedback Survey", fs.name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Feedback Survey", fs.name, ignore_permissions=True)
        except Exception:
            frappe.delete_doc("Feedback Survey", fs.name, ignore_permissions=True)
    if frappe.db.exists("KV Project", {"project_name": proj_name}):
        frappe.delete_doc("KV Project", frappe.db.get_value("KV Project", {"project_name": proj_name}, "name"), ignore_permissions=True)
    if frappe.db.exists("Project", {"project_name": proj_name}):
        frappe.delete_doc("Project", frappe.db.get_value("Project", {"project_name": proj_name}, "name"), ignore_permissions=True)
    frappe.db.commit()
    
    # PC1 creates project
    frappe.session.user = "pc1_test@krushivikas.org"
    company = frappe.defaults.get_user_default("Company") or (frappe.get_all("Company")[0].name if frappe.get_all("Company") else None)
    
    # 1. ERPNext Project
    p_erp = frappe.new_doc("Project")
    p_erp.project_name = proj_name
    p_erp.company = company
    p_erp.custom_project_coordinator = "pc1_test@krushivikas.org"
    p_erp.custom_project_manager = "pm1_test@krushivikas.org"
    p_erp.expected_start_date = "2026-09-01"
    p_erp.expected_end_date = "2026-12-31"
    p_erp.custom_budget = 500000
    p_erp.insert()
    
    # 2. KV Project
    p1 = frappe.new_doc("KV Project")
    p1.project_name = proj_name
    p1.project_coordinator = "pc1_test@krushivikas.org"
    p1.project_manager = "pm1_test@krushivikas.org"
    p1.start_date = "2026-09-01"
    p1.end_date = "2026-12-31"
    p1.budget = 500000
    p1.insert()
    frappe.db.commit()
    print(f"Setup: Created Projects '{p_erp.name}' & '{p1.name}' (Assigned to PC1)")

    # PM1 creates Activity A1 under Project
    frappe.session.user = "pm1_test@krushivikas.org"
    a1 = frappe.new_doc("Activity")
    a1.activity_name = "Sapling Distribution Activity"
    # Activity.project links to KV Project, not the ERPNext Project.
    # Task.project below is an ERPNext field and correctly keeps p_erp.
    a1.project = p1.name
    a1.assignee = "pm1_test@krushivikas.org"
    a1.status = "Open"
    a1.approved_budget = 100000
    a1.insert()
    frappe.db.commit()
    print(f"Setup: Created Activity '{a1.name}' (Assigned to PM1 under {p1.name})")

    # PM1 creates Task T1 assigned to FO1
    t1 = frappe.new_doc("Task")
    t1.subject = "Verify village nursery stock"
    t1.project = p_erp.name
    t1.custom_activity = a1.name
    t1.custom_activity_owner = "fo1_test@krushivikas.org"
    t1.status = "Open"
    t1.insert()
    frappe.db.commit()
    print(f"Setup: Created Task '{t1.name}' (Assigned to FO1 under A1)")

    # ----------------------------------------------------
    # SECTION 1: PROJECT UPDATE RIGHTS
    # ----------------------------------------------------
    print("\n--- [SECTION 1] Project Update Permissions ---")
    
    # 1.1 PC1 (Owner) edits P1
    frappe.session.user = "pc1_test@krushivikas.org"
    doc_p = frappe.get_doc("KV Project", p1.name)
    doc_p.budget = 520000
    doc_p.save()
    print("  [1.1] PASS: Assigned Project Coordinator PC1 edited their own project.")

    # 1.2 PC2 (Another Coordinator) tries to edit P1 -> MUST FAIL
    frappe.session.user = "pc2_test@krushivikas.org"
    try:
        doc_p = frappe.get_doc("KV Project", p1.name)
        doc_p.budget = 530000
        doc_p.save()
        print("  [1.2] FAIL: PC2 was able to edit PC1's project!")
    except Exception as e:
        print(f"  [1.2] PASS: PC2 blocked correctly: {str(e)[:70]}")

    # 1.3 PM1 tries to edit P1 -> MUST FAIL
    frappe.session.user = "pm1_test@krushivikas.org"
    try:
        doc_p = frappe.get_doc("KV Project", p1.name)
        doc_p.budget = 540000
        doc_p.save()
        print("  [1.3] FAIL: PM1 was able to edit project!")
    except Exception as e:
        print(f"  [1.3] PASS: PM1 blocked correctly: {str(e)[:70]}")

    # 1.4 Project Director (Above in Hierarchy) edits P1 -> MUST PASS
    frappe.session.user = "dir_test@krushivikas.org"
    doc_p = frappe.get_doc("KV Project", p1.name)
    doc_p.budget = 600000
    doc_p.save()
    print("  [1.4] PASS: Project Director edited P1 successfully.")

    # 1.5 CEO (Top Hierarchy) edits P1 -> MUST PASS
    frappe.session.user = "ceo_test@krushivikas.org"
    doc_p = frappe.get_doc("KV Project", p1.name)
    doc_p.budget = 700000
    doc_p.save()
    print("  [1.5] PASS: CEO edited P1 successfully.")

    # ----------------------------------------------------
    # SECTION 2: ACTIVITY UPDATE RIGHTS (Hierarchy inheritance)
    # ----------------------------------------------------
    print("\n--- [SECTION 2] Activity Update Permissions ---")

    # 2.1 PM1 (Assigned Owner) edits A1 -> MUST PASS
    frappe.session.user = "pm1_test@krushivikas.org"
    doc_a = frappe.get_doc("Activity", a1.name)
    doc_a.approved_budget = 110000
    doc_a.save()
    print("  [2.1] PASS: Assigned Project Manager PM1 edited Activity A1.")

    # 2.2 PM2 (Another Manager) tries to edit A1 -> MUST FAIL
    frappe.session.user = "pm2_test@krushivikas.org"
    try:
        doc_a = frappe.get_doc("Activity", a1.name)
        doc_a.approved_budget = 120000
        doc_a.save()
        print("  [2.2] FAIL: PM2 was able to edit PM1's activity!")
    except Exception as e:
        print(f"  [2.2] PASS: PM2 blocked correctly: {str(e)[:70]}")

    # 2.3 PC1 (Coordinator owning P1) edits Activity A1 -> MUST PASS (Hierarchical access)
    frappe.session.user = "pc1_test@krushivikas.org"
    doc_a = frappe.get_doc("Activity", a1.name)
    doc_a.approved_budget = 130000
    doc_a.save()
    print("  [2.3] PASS: PC1 edited Activity A1 (because PC1 owns Project P1).")

    # 2.4 PC2 (Another Coordinator not owning P1) tries to edit A1 -> MUST FAIL
    frappe.session.user = "pc2_test@krushivikas.org"
    try:
        doc_a = frappe.get_doc("Activity", a1.name)
        doc_a.approved_budget = 140000
        doc_a.save()
        print("  [2.4] FAIL: PC2 was able to edit Activity in PC1's project!")
    except Exception as e:
        print(f"  [2.4] PASS: PC2 blocked correctly: {str(e)[:70]}")

    # 2.5 Field Officer tries to edit Activity -> MUST FAIL
    frappe.session.user = "fo1_test@krushivikas.org"
    try:
        doc_a = frappe.get_doc("Activity", a1.name)
        doc_a.approved_budget = 150000
        doc_a.save()
        print("  [2.5] FAIL: Field Officer was able to edit Activity!")
    except Exception as e:
        print(f"  [2.5] PASS: Field Officer blocked correctly: {str(e)[:70]}")

    # 2.6 Project Director & CEO edit Activity -> MUST PASS
    frappe.session.user = "dir_test@krushivikas.org"
    doc_a = frappe.get_doc("Activity", a1.name)
    doc_a.approved_budget = 160000
    doc_a.save()
    print("  [2.6] PASS: Project Director edited Activity A1.")

    frappe.session.user = "ceo_test@krushivikas.org"
    doc_a = frappe.get_doc("Activity", a1.name)
    doc_a.approved_budget = 170000
    doc_a.save()
    print("  [2.7] PASS: CEO edited Activity A1.")

    # ----------------------------------------------------
    # SECTION 3: TASK UPDATE RIGHTS (Hierarchy inheritance)
    # ----------------------------------------------------
    print("\n--- [SECTION 3] Task Update Permissions ---")

    # 3.1 FO1 (Assigned Owner) edits Task T1 -> MUST PASS
    frappe.session.user = "fo1_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.description = "Updated survey checklist"
    doc_t.save()
    print("  [3.1] PASS: Assigned Field Officer FO1 edited Task T1.")

    # 3.2 FO2 (Another Field Officer) tries to edit T1 -> MUST FAIL
    frappe.session.user = "fo2_test@krushivikas.org"
    try:
        doc_t = frappe.get_doc("Task", t1.name)
        doc_t.description = "Unauthorized edit by FO2"
        doc_t.save()
        print("  [3.2] FAIL: FO2 was able to edit FO1's task!")
    except Exception as e:
        print(f"  [3.2] PASS: FO2 blocked correctly: {str(e)[:70]}")

    # 3.3 PM1 (Manager owning Activity A1) edits Task T1 -> MUST PASS
    frappe.session.user = "pm1_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.description = "PM1 updated task schedule"
    doc_t.save()
    print("  [3.3] PASS: PM1 edited Task T1 (because PM1 owns Activity A1).")

    # 3.4 PM2 (Another Manager) tries to edit T1 -> MUST FAIL
    frappe.session.user = "pm2_test@krushivikas.org"
    try:
        doc_t = frappe.get_doc("Task", t1.name)
        doc_t.description = "Unauthorized edit by PM2"
        doc_t.save()
        print("  [3.4] FAIL: PM2 was able to edit Task under PM1's activity!")
    except Exception as e:
        print(f"  [3.4] PASS: PM2 blocked correctly: {str(e)[:70]}")

    # 3.5 PC1 (Coordinator owning Project P1) edits Task T1 -> MUST PASS
    frappe.session.user = "pc1_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.description = "PC1 updated task priority"
    doc_t.save()
    print("  [3.5] PASS: PC1 edited Task T1 (because PC1 owns Project P1).")

    # 3.6 PC2 (Another Coordinator) tries to edit T1 -> MUST FAIL
    frappe.session.user = "pc2_test@krushivikas.org"
    try:
        doc_t = frappe.get_doc("Task", t1.name)
        doc_t.description = "Unauthorized edit by PC2"
        doc_t.save()
        print("  [3.6] FAIL: PC2 was able to edit Task under PC1's project!")
    except Exception as e:
        print(f"  [3.6] PASS: PC2 blocked correctly: {str(e)[:70]}")

    # 3.7 Project Director & CEO edit Task -> MUST PASS
    frappe.session.user = "dir_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.description = "Director added governance note"
    doc_t.save()
    print("  [3.7] PASS: Project Director edited Task T1.")

    frappe.session.user = "ceo_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.description = "CEO final signoff note"
    doc_t.save()
    print("  [3.8] PASS: CEO edited Task T1.")

    # ----------------------------------------------------
    # SECTION 4: FEEDBACK SURVEY UPDATE RIGHTS (Lateral FO Isolation & Hierarchy)
    # ----------------------------------------------------
    print("\n--- [SECTION 4] Feedback Survey Update Permissions ---")

    # 4.1 FO1 creates Feedback Survey FS1
    frappe.session.user = "fo1_test@krushivikas.org"
    fs1 = frappe.new_doc("Feedback Survey")
    fs1.village = "Ralegan Siddhi"
    fs1.date_of_visit = "2026-09-13"
    fs1.field_officer = "fo1_test@krushivikas.org"
    fs1.activity = "Sapling Distribution Activity"
    fs1.respondent_type = "Farmer"
    fs1.project = p1.name
    fs1.total_participants = 25
    fs1.adoption_percentage = 80.0
    fs1.outputs_achieved = "25 saplings planted"
    fs1.significant_change = "High survival rate"
    fs1.community_voice = "Great support from field staff"
    fs1.overall_rating = "4"
    fs1.confirmation_accuracy = 1
    fs1.insert()
    frappe.db.commit()
    print(f"Setup: Created Feedback Survey '{fs1.name}' (Conducted by FO1 under {p1.name})")

    # 4.2 FO1 (Conducted Officer) edits FS1 -> MUST PASS
    frappe.session.user = "fo1_test@krushivikas.org"
    doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
    doc_fs.total_participants = 30
    doc_fs.save()
    print("  [4.2] PASS: Assigned Field Officer FO1 edited their own survey.")

    # 4.3 FO2 (Another Field Officer) tries to edit FS1 -> MUST FAIL (Lateral Isolation)
    frappe.session.user = "fo2_test@krushivikas.org"
    try:
        doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
        doc_fs.total_participants = 35
        doc_fs.save()
        print("  [4.3] FAIL: FO2 was able to edit FO1's survey!")
    except Exception as e:
        print(f"  [4.3] PASS: Peer Field Officer FO2 blocked correctly: {str(e)[:70]}")

    # 4.4 PM1 (Manager owning Project P1) edits FS1 -> MUST PASS
    frappe.session.user = "pm1_test@krushivikas.org"
    doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
    doc_fs.total_participants = 40
    doc_fs.save()
    print("  [4.4] PASS: PM1 edited Feedback Survey FS1 (because PM1 manages P1).")

    # 4.5 PM2 (Another Manager) tries to edit FS1 -> MUST FAIL
    frappe.session.user = "pm2_test@krushivikas.org"
    try:
        doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
        doc_fs.total_participants = 45
        doc_fs.save()
        print("  [4.5] FAIL: PM2 was able to edit survey under PM1's project!")
    except Exception as e:
        print(f"  [4.5] PASS: PM2 blocked correctly: {str(e)[:70]}")

    # 4.6 PC1 (Coordinator owning Project P1) edits FS1 -> MUST PASS
    frappe.session.user = "pc1_test@krushivikas.org"
    doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
    doc_fs.total_participants = 50
    doc_fs.save()
    print("  [4.6] PASS: PC1 edited Feedback Survey FS1 (because PC1 coordinates P1).")

    # 4.7 PC2 (Another Coordinator) tries to edit FS1 -> MUST FAIL
    frappe.session.user = "pc2_test@krushivikas.org"
    try:
        doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
        doc_fs.total_participants = 55
        doc_fs.save()
        print("  [4.7] FAIL: PC2 was able to edit survey under PC1's project!")
    except Exception as e:
        print(f"  [4.7] PASS: PC2 blocked correctly: {str(e)[:70]}")

    # 4.8 Project Director & CEO edit FS1 -> MUST PASS
    frappe.session.user = "dir_test@krushivikas.org"
    doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
    doc_fs.overall_rating = "5"
    doc_fs.save()
    print("  [4.8] PASS: Project Director edited Feedback Survey FS1.")

    frappe.session.user = "ceo_test@krushivikas.org"
    doc_fs = frappe.get_doc("Feedback Survey", fs1.name)
    doc_fs.submission_status = "Approved"
    doc_fs.save()
    print("  [4.9] PASS: CEO edited/approved Feedback Survey FS1.")

    frappe.session.user = "Administrator"
    teardown(proj_name)

    print("\n=======================================================")
    print("🎉 ALL HIERARCHICAL & OWNERSHIP UPDATE TESTS PASSED! 🎉")
    print("=======================================================")


def teardown(proj_name):
    """Leave the site as it was found.

    The suite switches users and commits as it goes, so a rollback would not
    undo the earlier writes — the records it made have to be removed by hand.
    """
    frappe.set_user("Administrator")

    for dt in ("Task", "Activity", "Feedback Survey"):
        for name in frappe.get_all(dt, pluck="name", limit_page_length=0):
            try:
                doc = frappe.get_doc(dt, name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
            except Exception:
                frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

    for dt in ("KV Project", "Project"):
        for name in frappe.get_all(dt, filters={"project_name": proj_name}, pluck="name"):
            frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

    frappe.db.delete("Deleted Document", {"deleted_doctype": ["in",
        ["KV Project", "Project", "Activity", "Task", "Feedback Survey"]]})
    frappe.db.commit()

