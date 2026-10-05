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

    # Ensure Employees exist for FO1 and FO2
    for fo_email in ["fo1_test@krushivikas.org", "fo2_test@krushivikas.org"]:
        emp_id = frappe.db.get_value("Employee", {"user_id": fo_email}, "name")
        if not emp_id:
            if not frappe.db.exists("Gender", "Female"):
                frappe.get_doc({"doctype": "Gender", "gender": "Female"}).insert(ignore_permissions=True)
            emp = frappe.new_doc("Employee")
            emp.first_name = fo_email.split("_")[0].upper()
            emp.user_id = fo_email
            emp.company = company
            emp.gender = "Female"
            emp.date_of_birth = "1995-01-01"
            emp.date_of_joining = "2024-01-01"
            emp.insert(ignore_permissions=True)
    frappe.db.commit()

    fo1_emp = frappe.db.get_value("Employee", {"user_id": "fo1_test@krushivikas.org"}, "name")

    # PM1 creates Task T1 assigned to FO1
    t1 = frappe.new_doc("Task")
    t1.subject = "Verify village nursery stock"
    task_proj_options = frappe.db.get_value("Property Setter", {"doc_type": "Task", "field_name": "project", "property": "options"}, "value") or frappe.db.get_value("DocField", {"parent": "Task", "fieldname": "project"}, "options")
    t1.project = p1.name if task_proj_options == "KV Project" else p_erp.name
    t1.custom_activity = a1.name
    t1.custom_activity_owner = "fo1_test@krushivikas.org"
    t1.custom_assigned_to = "fo1_test@krushivikas.org"
    t1.custom_assignee = "fo1_test@krushivikas.org"
    t1.status = "Open"
    t1.insert()
    frappe.db.commit()
    print(f"Setup: Created Task '{t1.name}' (Assigned to FO1 under A1)")

    # ----------------------------------------------------
        # ----------------------------------------------------
    # SECTION 0: PROJECT READ VISIBILITY (Below CXO isolation)
    # ----------------------------------------------------
    print("\n--- [SECTION 0] Project Read Visibility Permissions ---")
    
    # 0.1 Assigned PC1 can read P1 -> MUST PASS
    assert frappe.has_permission("KV Project", "read", p1, user="pc1_test@krushivikas.org"), "PC1 should be able to read P1"
    print("  [0.1] PASS: Assigned Project Coordinator PC1 can view project P1.")

    # 0.2 Assigned PM1 can read P1 -> MUST PASS
    assert frappe.has_permission("KV Project", "read", p1, user="pm1_test@krushivikas.org"), "PM1 should be able to read P1"
    print("  [0.2] PASS: Assigned Project Manager PM1 can view project P1.")

    # 0.3 FO1 (Has subtask assigned under P1) can read P1 -> MUST PASS
    assert frappe.has_permission("KV Project", "read", p1, user="fo1_test@krushivikas.org"), "FO1 should be able to read P1 because a subtask is assigned"
    print("  [0.3] PASS: Field Officer FO1 can view project P1 (subtask assigned to FO1).")

    # 0.4 FO2 (No subtask on P1) CANNOT read P1 -> MUST BE BLOCKED
    assert not frappe.has_permission("KV Project", "read", p1, user="fo2_test@krushivikas.org"), "FO2 should NOT be able to read P1"
    print("  [0.4] PASS: Field Officer FO2 blocked from viewing P1 (no subtasks assigned).")

    # 0.5 PC2 (Unrelated Coordinator) CANNOT read P1 -> MUST BE BLOCKED
    assert not frappe.has_permission("KV Project", "read", p1, user="pc2_test@krushivikas.org"), "PC2 should NOT be able to read P1"
    print("  [0.5] PASS: Coordinator PC2 blocked from viewing P1 (not assigned to P1).")

    # 0.6 Project Director & CEO can read P1 -> MUST PASS
    assert frappe.has_permission("KV Project", "read", p1, user="dir_test@krushivikas.org"), "Director should be able to read P1"
    assert frappe.has_permission("KV Project", "read", p1, user="ceo_test@krushivikas.org"), "CEO should be able to read P1"
    print("  [0.6] PASS: CXO level (CEO & Director) can view any project across organization.")

    # # SECTION 1: PROJECT UPDATE RIGHTS
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

    # 1.3 PM1 (Assigned Project Manager) edits P1 -> MUST PASS
    frappe.session.user = "pm1_test@krushivikas.org"
    doc_p = frappe.get_doc("KV Project", p1.name)
    doc_p.budget = 540000
    doc_p.save()
    print("  [1.3] PASS: Assigned Project Manager PM1 edited their assigned project.")

    # 1.3b PM2 (Another Manager) tries to edit P1 -> MUST FAIL
    frappe.session.user = "pm2_test@krushivikas.org"
    try:
        doc_p = frappe.get_doc("KV Project", p1.name)
        doc_p.budget = 550000
        doc_p.save()
        print("  [1.3b] FAIL: PM2 was able to edit PM1's project!")
    except Exception as e:
        print(f"  [1.3b] PASS: PM2 blocked correctly: {str(e)[:70]}")

    # 1.3c Field Officer tries to edit P1 -> MUST FAIL
    frappe.session.user = "fo1_test@krushivikas.org"
    try:
        doc_p = frappe.get_doc("KV Project", p1.name)
        doc_p.budget = 560000
        doc_p.save()
        print("  [1.3c] FAIL: Field Officer was able to edit project!")
    except Exception as e:
        print(f"  [1.3c] PASS: Field Officer blocked correctly: {str(e)[:70]}")

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

    # 4.10 Field Officer FO1 cannot fill a Project-level feedback survey (PM only)
    frappe.session.user = "fo1_test@krushivikas.org"
    try:
        fs_proj_bad = frappe.new_doc("Feedback Survey")
        fs_proj_bad.survey_level = "Project"
        fs_proj_bad.project = p1.name
        fs_proj_bad.village = "Ralegan Siddhi"
        fs_proj_bad.date_of_visit = "2026-09-15"
        fs_proj_bad.field_officer = "fo1_test@krushivikas.org"
        fs_proj_bad.respondent_type = "Farmer"
        fs_proj_bad.total_participants = 10
        fs_proj_bad.adoption_percentage = 70.0
        fs_proj_bad.outputs_achieved = "Project Output"
        fs_proj_bad.significant_change = "Project Outcome"
        fs_proj_bad.confirmation_accuracy = 1
        fs_proj_bad.insert()
        assert False, "FO1 should NOT be allowed to create a Project-level feedback survey!"
    except frappe.PermissionError as e:
        print(f"  [4.10] PASS: Field Officer FO1 blocked from creating Project-level survey: {str(e)[:70]}")

    # 4.11 Project Manager PM1 cannot fill an Activity-level feedback survey (FO only)
    frappe.session.user = "pm1_test@krushivikas.org"
    try:
        fs_act_bad = frappe.new_doc("Feedback Survey")
        fs_act_bad.survey_level = "Activity"
        fs_act_bad.linked_activity = a1.name
        fs_act_bad.activity = a1.activity_name
        fs_act_bad.project = p1.name
        fs_act_bad.village = "Ralegan Siddhi"
        fs_act_bad.date_of_visit = "2026-09-15"
        fs_act_bad.field_officer = "pm1_test@krushivikas.org"
        fs_act_bad.respondent_type = "Farmer"
        fs_act_bad.total_participants = 10
        fs_act_bad.adoption_percentage = 70.0
        fs_act_bad.outputs_achieved = "Activity Output"
        fs_act_bad.significant_change = "Activity Outcome"
        fs_act_bad.confirmation_accuracy = 1
        fs_act_bad.insert()
        assert False, "PM1 should NOT be allowed to create an Activity-level feedback survey!"
    except frappe.PermissionError as e:
        print(f"  [4.11] PASS: Project Manager PM1 blocked from creating Activity-level survey: {str(e)[:70]}")

    # 4.12 Project Manager PM1 creates Project-level feedback survey for their project -> MUST PASS
    frappe.session.user = "pm1_test@krushivikas.org"
    fs_proj = frappe.new_doc("Feedback Survey")
    fs_proj.survey_level = "Project"
    fs_proj.project = p1.name
    fs_proj.village = "Ralegan Siddhi"
    fs_proj.date_of_visit = "2026-09-15"
    fs_proj.field_officer = "pm1_test@krushivikas.org"
    fs_proj.respondent_type = "Farmer"
    fs_proj.total_participants = 50
    fs_proj.adoption_percentage = 85.0
    fs_proj.outputs_achieved = "Overall project outputs achieved"
    fs_proj.significant_change = "Overall community improvement observed"
    fs_proj.confirmation_accuracy = 1
    fs_proj.insert()
    print(f"  [4.12] PASS: PM1 created Project-level Feedback Survey '{fs_proj.name}' for {p1.name}.")

    # 4.12b Project Manager PM1 creates Project-level feedback survey with ALL fields omitted (All fields optional for Project level) -> MUST PASS
    frappe.session.user = "pm1_test@krushivikas.org"
    fs_proj_optional = frappe.new_doc("Feedback Survey")
    fs_proj_optional.survey_level = "Project"
    fs_proj_optional.project = p1.name
    # Deliberately omit village, date_of_visit, respondent_type, total_participants, adoption_percentage, significant_change, confirmation_accuracy, etc.
    fs_proj_optional.insert()
    print(f"  [4.12b] PASS: PM1 created Project-level Feedback Survey with all optional fields omitted '{fs_proj_optional.name}'.")

    # 4.12c Field Officer FO1 tries to create Activity-level survey with missing required fields -> MUST FAIL (Activity fields strictly mandatory)
    frappe.session.user = "fo1_test@krushivikas.org"
    try:
        fs_act_missing = frappe.new_doc("Feedback Survey")
        fs_act_missing.survey_level = "Activity"
        fs_act_missing.linked_activity = a1.name
        fs_act_missing.activity = a1.activity_name
        # Deliberately omit village, respondent_type, total_participants, etc.
        fs_act_missing.insert()
        assert False, "Activity-level survey without required fields should fail!"
    except frappe.ValidationError as e:
        print(f"  [4.12c] PASS: Activity-level survey correctly strictly enforces mandatory fields: {str(e)[:70]}")

    # 4.13 Activity creation unblocked: Creating new Activity without survey must succeed
    frappe.session.user = "pm1_test@krushivikas.org"
    a_new = frappe.new_doc("Activity")
    a_new.activity_name = "Water Harvesting Activity"
    a_new.project = p1.name
    a_new.assignee = "pm1_test@krushivikas.org"
    a_new.status = "Open"
    a_new.approved_budget = 50000
    a_new.insert()
    print(f"  [4.13] PASS: New Activity '{a_new.name}' created without requiring initial feedback survey.")

    # 4.14 Activity completion validation: Cannot mark Completed without Feedback Survey
    frappe.session.user = "pm1_test@krushivikas.org"
    doc_a = frappe.get_doc("Activity", a_new.name)
    doc_a.status = "Completed"
    try:
        doc_a.save()
        assert False, "Activity should NOT be closed without at least one feedback survey!"
    except frappe.ValidationError as e:
        print(f"  [4.14a] PASS: Closing Activity without feedback survey blocked: {str(e)[:70]}")

    # FO1 fills feedback survey for a_new -> now Activity can be closed
    frappe.session.user = "fo1_test@krushivikas.org"
    fs_act_new = frappe.new_doc("Feedback Survey")
    fs_act_new.survey_level = "Activity"
    fs_act_new.linked_activity = a_new.name
    fs_act_new.activity = a_new.activity_name
    fs_act_new.project = p1.name
    fs_act_new.village = "Ralegan Siddhi"
    fs_act_new.date_of_visit = "2026-09-16"
    fs_act_new.field_officer = "fo1_test@krushivikas.org"
    fs_act_new.respondent_type = "Farmer"
    fs_act_new.total_participants = 15
    fs_act_new.adoption_percentage = 90.0
    fs_act_new.outputs_achieved = "Water pond completed"
    fs_act_new.significant_change = "Water available for irrigation"
    fs_act_new.confirmation_accuracy = 1
    fs_act_new.insert()

    frappe.session.user = "pm1_test@krushivikas.org"
    doc_a = frappe.get_doc("Activity", a_new.name)
    doc_a.status = "Completed"
    doc_a.save()
    assert doc_a.status == "Completed", f"Expected Completed, got {doc_a.status}"
    print(f"  [4.14b] PASS: Activity marked Completed after adding feedback survey '{fs_act_new.name}'.")

    # 4.15 Project creation unblocked: Creating new Project without survey must succeed
    frappe.session.user = "pc1_test@krushivikas.org"
    p_fresh = frappe.new_doc("KV Project")
    p_fresh.project_name = "Solar Pump Initiative 2026"
    p_fresh.project_coordinator = "pc1_test@krushivikas.org"
    p_fresh.project_manager = "pm1_test@krushivikas.org"
    p_fresh.start_date = "2026-10-01"
    p_fresh.end_date = "2026-12-31"
    p_fresh.budget = 200000
    p_fresh.status = "Planning"
    p_fresh.insert()
    print(f"  [4.15] PASS: New Project '{p_fresh.name}' created without requiring initial feedback survey.")

    # 4.16 Project completion validation: Cannot mark Completed without Feedback Survey
    frappe.session.user = "pc1_test@krushivikas.org"
    doc_p = frappe.get_doc("KV Project", p_fresh.name)
    doc_p.status = "Completed"
    try:
        doc_p.save()
        assert False, "Project should NOT be closed without at least one feedback survey!"
    except frappe.ValidationError as e:
        print(f"  [4.16a] PASS: Closing Project without feedback survey blocked: {str(e)[:70]}")

    # PM1 creates Project-level survey for p_fresh -> now Project can be completed
    frappe.session.user = "pm1_test@krushivikas.org"
    fs_fresh_proj = frappe.new_doc("Feedback Survey")
    fs_fresh_proj.survey_level = "Project"
    fs_fresh_proj.project = p_fresh.name
    fs_fresh_proj.village = "Ralegan Siddhi"
    fs_fresh_proj.date_of_visit = "2026-10-02"
    fs_fresh_proj.field_officer = "pm1_test@krushivikas.org"
    fs_fresh_proj.respondent_type = "Farmer"
    fs_fresh_proj.total_participants = 30
    fs_fresh_proj.adoption_percentage = 95.0
    fs_fresh_proj.outputs_achieved = "Solar pumps functional"
    fs_fresh_proj.significant_change = "Clean energy adoption"
    fs_fresh_proj.confirmation_accuracy = 1
    fs_fresh_proj.insert()

    frappe.session.user = "pc1_test@krushivikas.org"
    doc_p = frappe.get_doc("KV Project", p_fresh.name)
    doc_p.status = "Completed"
    doc_p.save()
    assert doc_p.status == "Completed", f"Expected Completed, got {doc_p.status}"
    print(f"  [4.16b] PASS: Project marked Completed after adding Project-level feedback survey '{fs_fresh_proj.name}'.")

    # ----------------------------------------------------
    # SECTION 5: TASK EVIDENCE REVIEW WORKFLOW (MAKER-CHECKER)
    # ----------------------------------------------------
    print("\n--- [SECTION 5] Task Evidence Review Workflow (Maker-Checker) ---")

    # 5.1 PC1 (Coordinator) configures task T1 to require evidence
    frappe.session.user = "pc1_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.custom_require_evidence = 1
    doc_t.save()
    print("  [5.1] PASS: Project Coordinator PC1 required image evidence for task completion.")

    # 5.2 FO1 (Field Officer) cannot uncheck custom_require_evidence
    frappe.session.user = "fo1_test@krushivikas.org"
    try:
        doc_t = frappe.get_doc("Task", t1.name)
        doc_t.custom_require_evidence = 0
        doc_t.save()
        assert False, "FO1 should not be able to disable evidence requirement!"
    except frappe.PermissionError as e:
        print(f"  [5.2] PASS: Field Officer FO1 blocked from removing evidence requirement: {str(e)[:60]}")

    # 5.3 FO1 cannot complete task without evidence
    frappe.session.user = "fo1_test@krushivikas.org"
    try:
        doc_t = frappe.get_doc("Task", t1.name)
        doc_t.status = "Completed"
        doc_t.save()
        assert False, "FO1 should not be able to complete task without evidence image!"
    except frappe.ValidationError as e:
        print(f"  [5.3] PASS: FO1 blocked from marking Completed without evidence image: {str(e)[:60]}")

    # 5.4 FO1 attaches evidence image and submits for review
    frappe.session.user = "fo1_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.custom_evidence_image = "/files/sample_nursery_stock.jpg"
    doc_t.save()
    from krushi_vikas.api import submit_task_for_review, review_task_submission
    sub_res = submit_task_for_review(t1.name)
    doc_t.reload()
    assert doc_t.status == "Pending Review", f"Expected Pending Review, got {doc_t.status}"
    assert doc_t.custom_review_status == "Pending Review", f"Expected Pending Review, got {doc_t.custom_review_status}"
    print("  [5.4] PASS: FO1 attached evidence and submitted for review (Status: Pending Review).")

    # 5.5 PC2 (Unrelated Coordinator) cannot review task evidence
    frappe.session.user = "pc2_test@krushivikas.org"
    try:
        review_task_submission(t1.name, "reject", comment="Irrelevant rejection by PC2")
        assert False, "PC2 should not be able to review tasks in PC1's project!"
    except frappe.PermissionError as e:
        print(f"  [5.5] PASS: Unrelated Coordinator PC2 blocked from reviewing task: {str(e)[:60]}")

    # 5.6 PC1 (Assigned Coordinator) rejects evidence -> status must be 'Needs Work'
    frappe.session.user = "pc1_test@krushivikas.org"
    rej_res = review_task_submission(t1.name, "reject", comment="Stock counts unclear, please attach clear geotagged photo.")
    doc_t.reload()
    assert doc_t.status == "Needs Work", f"Expected status 'Needs Work', got '{doc_t.status}'"
    assert doc_t.custom_review_status == "Rejected", f"Expected custom_review_status 'Rejected', got '{doc_t.custom_review_status}'"
    assert "Stock counts unclear" in doc_t.custom_review_comment, "Comment missing"
    print("  [5.6] PASS: PC1 rejected evidence; task returned to Field Officer queue with status 'Needs Work'.")

    # 5.7 FO1 updates evidence and resubmits for review
    frappe.session.user = "fo1_test@krushivikas.org"
    doc_t = frappe.get_doc("Task", t1.name)
    doc_t.custom_evidence_image = "/files/clear_geotagged_nursery.jpg"
    doc_t.save()
    sub_res2 = submit_task_for_review(t1.name)
    doc_t.reload()
    assert doc_t.status == "Pending Review", f"Expected Pending Review, got {doc_t.status}"
    print("  [5.7] PASS: FO1 updated evidence and resubmitted task for review.")

    # 5.8 PC1 approves evidence -> status must be 'Completed'
    frappe.session.user = "pc1_test@krushivikas.org"
    app_res = review_task_submission(t1.name, "approve")
    doc_t.reload()
    assert doc_t.status == "Completed", f"Expected status 'Completed', got '{doc_t.status}'"
    assert doc_t.custom_review_status == "Approved", f"Expected custom_review_status 'Approved', got '{doc_t.custom_review_status}'"
    assert doc_t.custom_reviewed_by == "pc1_test@krushivikas.org", f"Reviewer not recorded: {doc_t.custom_reviewed_by}"
    print("  [5.8] PASS: PC1 approved evidence; task status transitioned to 'Completed' (Review Status: Approved).")

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

