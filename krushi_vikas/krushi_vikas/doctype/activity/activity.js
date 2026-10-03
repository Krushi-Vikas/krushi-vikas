frappe.ui.form.on("Activity", {
	onload(frm) {
		frm.set_query("theme", () => ({ filters: { is_group: 1 } }));
		frm.set_query("sub_theme", () => ({
			filters: { is_group: 0, parent_project_theme: frm.doc.theme || "" }
		}));
	},
	theme(frm) {
		frm.set_value("sub_theme", "");
	},
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(
			__("New Task"),
			function () {
				// `project` is deliberately not prefilled: Task.project links
				// to ERPNext's Project doctype, so passing a KV Project name
				// here fails link validation on save. custom_activity is the
				// link that ties a task to this activity and its project.
				frappe.new_doc("Task", {
					custom_activity: frm.doc.name,
					exp_start_date: frm.doc.start_date,
					exp_end_date: frm.doc.end_date,
					status: "Open"
				});
			},
			__("Tasks")
		);

		frm.add_custom_button(
			__("View Tasks"),
			function () {
				frappe.set_route("List", "Task", { custom_activity: frm.doc.name });
			},
			__("Tasks")
		);

		frm.page.set_inner_btn_group_as_primary(__("Tasks"));
	}
});
