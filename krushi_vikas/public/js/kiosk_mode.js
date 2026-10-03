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
		const route = frappe.get_route();
		// If clicking logo or navigating leads to bare /app, redirect to krushi-dashboard
		if (!route || !route.length || (route.length === 1 && (!route[0] || route[0] === "app" || route[0] === "home"))) {
			frappe.set_route("krushi-dashboard");
			return;
		}
		if (!isRestricted()) return;
		if (!isAllowed(route)) {
			frappe.set_route("krushi-dashboard");
		}
	}

	function setupLogoRedirect() {
		// Intercept clicks on the top-left project / brand logo in Desk navbar
		$(document).on("click", ".navbar-brand, .navbar-home, a.navbar-brand, a.navbar-home, .app-logo, [data-action='home']", function (e) {
			if ($(this).closest(".dropdown-menu").length) return;
			e.preventDefault();
			e.stopImmediatePropagation();
			frappe.set_route("krushi-dashboard");
			return false;
		});

		// Ensure href attributes point to /app/krushi-dashboard instead of bare /app
		$(".navbar-brand, .navbar-home, a.navbar-brand, a.navbar-home").attr("href", "/app/krushi-dashboard");
	}

	$(document).on("app_ready", function () {
		setupLogoRedirect();
		frappe.router.on("change", function () {
			$(".navbar-brand, .navbar-home, a.navbar-brand, a.navbar-home").attr("href", "/app/krushi-dashboard");
			enforce();
		});
		enforce();
	});
})();
