// get_tree_root was false, which stops Frappe fetching the root node — the
// tree then renders empty even though themes exist.
frappe.treeview_settings["Project Theme"] = {
	breadcrumb: "Krushi Vikas",
	title: __("Project Themes"),
	root_label: __("All Themes"),
	get_tree_nodes: "frappe.desk.treeview.get_children",
	filters: [],
	menu_items: [],
	onload: function (treeview) {
		treeview.make_tree();
	}
};
