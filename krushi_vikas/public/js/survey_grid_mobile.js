(function () {
	const SCOPED_ROUTE_ROOTS = ["baseline-survey", "village-profile"];
	const BODY_CLASS = "kv-mobile-grid-reorder";

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
