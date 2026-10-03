(function () {
	const SCOPED_ROUTE_ROOTS = ["baseline-survey", "village-profile"];
	const SCOPED_DOCTYPES = ["Baseline Survey", "Village Profile"];
	const BODY_CLASS = "kv-mobile-grid-reorder";
	const registeredRowTypes = new Set();

	function showRowToolbar(frm) {
		if (!SCOPED_DOCTYPES.includes(frm.doctype)) return;
		$(frm.wrapper)
			.find(".grid-row-open .grid-header-toolbar button.hidden-xs, .grid-row-open .grid-footer-toolbar.hidden-xs")
			.removeClass("hidden-xs");
	}

	function registerRowToolbars(frm) {
		frm.meta.fields.forEach((field) => {
			if (field.fieldtype !== "Table" || !field.options || registeredRowTypes.has(field.options)) return;
			registeredRowTypes.add(field.options);
			frappe.ui.form.on(field.options, { form_render: showRowToolbar });
		});
	}

	SCOPED_DOCTYPES.forEach((doctype) => {
		frappe.ui.form.on(doctype, { refresh: registerRowToolbars });
	});

	function isScopedRoute(route) {
		if (!route || !route.length) return false;
		const head = String(route[0] || "").toLowerCase();
		if (head === "form" && route[1]) {
			const doctypeSlug = String(route[1]).toLowerCase().replace(/\s+/g, "-");
			return SCOPED_ROUTE_ROOTS.includes(doctypeSlug);
		}
		return SCOPED_ROUTE_ROOTS.includes(head);
	}

	function apply() {
		document.body.classList.toggle(BODY_CLASS, isScopedRoute(frappe.get_route()));
	}

	$(document).on("app_ready", function () {
		frappe.router.on("change", apply);
		apply();
	});
})();
