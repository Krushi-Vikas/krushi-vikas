// Field-level roles only ever see Krushi Vikas: the dashboard, the project
// board, and the doctype forms those two link to (KV Project, Activity,
// Task, Project Theme, KV Project Template, and the roadmap documents).
// Everything else Frappe/ERPNext ships — Home, Item, Customer, Settings,
// the app switcher's other apps — is off limits for them, enforced here
// rather than by hiding sidebar links, since a hidden link is still one
// route away and this DOM has no stable class names to hide reliably.
//
// System Manager (Administrator included, since Administrator holds every
// role) is exempt — someone still has to be able to configure the site.
(function () {
	const ALLOWED_ROUTE_ROOTS = [
		"krushi-dashboard",
		"krushi-projects",
		"krushi-activities",
		"krushi-themes",
		"kv-project",
		"kv-project-template",
		"activity",
		"task",
		"project-theme",
		"concept-note",
		"rra-report",
		"project-proposal",
		"kre",
		"activity-outcome",
		"baseline-survey",
		"village-profile",
		"feedback-survey",
		"beneficiary",
	];

	function isRestricted() {
		const roles = (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
		return !roles.includes("System Manager");
	}

	function isAllowed(route) {
		// Bare /app (the Frappe "Apps" switcher screen) is only reachable via
		// a mid-session navigation here, since login already redirects
		// straight past it — so it's just as off-limits as any other route.
		if (!route || !route.length) return false;
		const head = String(route[0] || "").toLowerCase();
		const routesToCheck = [head];

		// Desk shortcuts use List/<DocType> and Form/<DocType>/<name>, while
		// direct navigation uses the DocType's slug. Restrict both forms to
		// the same approved Krushi Vikas document set.
		if (["list", "form"].includes(head) && route[1]) {
			routesToCheck.push(String(route[1]).toLowerCase().replace(/\s+/g, "-"));
		}

		return routesToCheck.some((candidate) =>
			ALLOWED_ROUTE_ROOTS.some((root) => candidate === root || candidate.startsWith(root))
		);
	}

	function enforce() {
		if (!isRestricted()) return;
		const route = frappe.get_route();
		if (!isAllowed(route)) {
			frappe.set_route("krushi-dashboard");
		}
	}

	$(document).on("app_ready", function () {
		if (!isRestricted()) return;
		frappe.router.on("change", enforce);
		enforce();
	});
})();
