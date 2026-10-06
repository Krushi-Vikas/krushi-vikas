"""Demo data for a fresh site.

    bench --site <site> execute krushi_vikas.sample_data.run

Creates three projects with an activity and a task each, spread across the
test coordinators, managers and field officers, so the dashboard and the
project board have something to render. Idempotent — existing projects are
left alone.
"""

import frappe


def run():
	frappe.set_user("Administrator")
	theme = (frappe.get_all("Project Theme", pluck="name") or [None])[0]

	specs = [
		("Watershed Restoration 2026", "pc1_test@krushivikas.org", "pm1_test@krushivikas.org",
		 "In Progress", 2500000, 900000, "2026-01-01", "2026-12-31"),
		("Drip Irrigation Rollout", "pc1_test@krushivikas.org", "pm1_test@krushivikas.org",
		 "Planning", 1200000, 0, "2026-04-01", "2027-03-31"),
		("Farmer Producer Org Support", "pc2_test@krushivikas.org", None,
		 "In Progress", 800000, 700000, "2026-02-01", "2026-11-30"),
	]

	for name, coord, mgr, status, budget, spent, start, end in specs:
		if frappe.db.exists("KV Project", name):
			continue
		p = frappe.new_doc("KV Project")
		p.project_name = name; p.theme = theme; p.status = status
		p.project_coordinator = coord; p.project_manager = mgr
		p.budget = budget; p.actual_amount_spent = spent
		p.start_date = start; p.end_date = end
		p.insert()

		act = frappe.new_doc("Activity")
		act.activity_name = f"{name} — field works"
		act.project = p.name; act.assignee = mgr or coord; act.status = "Open"
		act.start_date = start; act.end_date = end
		act.insert()

		task = frappe.new_doc("Task")
		task.subject = f"Site survey for {name}"
		task.custom_activity = act.name
		task.custom_activity_owner = "fo1_test@krushivikas.org"
		task.status = "Working"
		task.exp_end_date = end
		task.insert()

	frappe.db.commit()
	print("KV Projects:", frappe.db.count("KV Project"))
	print("Activities  :", frappe.db.count("Activity"))
	print("Tasks       :", frappe.db.count("Task"))
