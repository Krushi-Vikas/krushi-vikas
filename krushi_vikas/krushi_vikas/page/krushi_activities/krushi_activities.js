frappe.pages["krushi-activities"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: "", single_column: true });

	const $main = $(wrapper).find(".layout-main-section");

	let requestId = 0;
	let searchTimer = null;
	const filters = { search: "", status: "" };

	const svg = {
		pulse: `<path d="M3 12h4l2-7 4 14 2-7h6"/>`,
		pulsePlus: `<path d="M3 12h4l2-7 4 14 2-7h4"/><path d="M19 9v6"/><path d="M16 12h6"/>`,
		search: `<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>`,
		tasks: `<path d="M4 6.5 6 8.5 10 4.5"/><path d="M4 17.5 6 19.5 10 15.5"/><path d="M13 7h7"/><path d="M13 18h7"/>`,
		clock: `<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>`,
		alert: `<path d="M12 4 2.5 20h19L12 4Z"/><path d="M12 10v4"/><path d="M12 17.2v.1"/>`,
		user: `<circle cx="12" cy="8" r="3.2"/><path d="M5 21c0-4 3-7 7-7s7 3 7 7"/>`,
		grid: `<rect x="3" y="3" width="7" height="7" rx="1.4"/><rect x="14" y="3" width="7" height="7" rx="1.4"/><rect x="3" y="14" width="7" height="7" rx="1.4"/><rect x="14" y="14" width="7" height="7" rx="1.4"/>`,
		back: `<path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-4"/>`
	};

	const icon = (n) =>
		`<span class="kv-icon"><svg viewBox="0 0 24 24" aria-hidden="true">${svg[n] || svg.grid}</svg></span>`;

	const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));

	function initials(name) {
		const parts = String(name || "?").trim().split(/[\s@._-]+/).filter(Boolean);
		return ((parts[0] || "?")[0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
	}

	const statusClass = (s) =>
		({
			Draft: "s-planning",
			Open: "s-planning",
			"In Progress": "s-progress",
			Completed: "s-completed",
			Cancelled: "s-cancelled"
		}[s] || "s-planning");

	$main.html(`
		<div class="kvp kva">
			<header class="kvp-head">
				<div>
					<h1>Activities</h1>
					<p id="kva-sub">Every activity you are responsible for.</p>
				</div>
				<div class="kvp-actions">
					<button class="kvp-btn" id="kva-dash">${icon("back")}<span>Dashboard</span></button>
					<button class="kvp-btn" id="kva-list">${icon("grid")}<span>Table view</span></button>
					<button class="kvp-btn primary" id="kva-new">${icon("pulsePlus")}<span>New Activity</span></button>
				</div>
			</header>

			<div class="kvp-scope is-hidden" id="kva-scope">
				${icon("user")}<span id="kva-scope-text"></span>
			</div>

			<div class="kvp-toolbar">
				<div class="kvp-search">
					${icon("search")}
					<input type="text" class="kvp-input" id="kva-q"
						placeholder="Search activities or themes…" autocomplete="off">
				</div>

				<select class="kvp-select" id="kva-status">
					<option value="">All statuses</option>
					<option value="Draft">Draft</option>
					<option value="Open">Open</option>
					<option value="In Progress">In Progress</option>
					<option value="Completed">Completed</option>
					<option value="Cancelled">Cancelled</option>
				</select>

				<span class="kvp-count" id="kva-count"></span>
			</div>

			<div id="kva-body">
				<div class="kvp-grid">
					${Array.from({ length: 6 }, () => `<div class="kvp-skel"></div>`).join("")}
				</div>
			</div>
		</div>
	`);

	function themeChips(a) {
		const chips = [a.theme, a.sub_theme].filter(Boolean);
		if (!chips.length) return `<span class="kvp-theme-chip is-empty">No theme set</span>`;
		return chips.map((t) => `<span class="kvp-theme-chip">${esc(t)}</span>`).join("");
	}

	function progressMeter(a) {
		if (!a.task_total) {
			return `
				<div class="kvp-meter">
					<div class="kvp-meter-top"><span>No checklist steps yet</span></div>
					<div class="kvp-track"><i style="width:0"></i></div>
				</div>`;
		}

		return `
			<div class="kvp-meter">
				<div class="kvp-meter-top">
					<span>${a.task_total - a.task_open} of ${a.task_total} steps done</span>
					<b>${a.task_done_pct}%</b>
				</div>
				<div class="kvp-track"><i style="width:${a.task_done_pct}%"></i></div>
			</div>`;
	}

	function card(a) {
		return `
			<button class="kvp-card ${statusClass(a.status)}" data-activity="${esc(a.name)}">
				<div class="kvp-card-top">
					<div class="kvp-card-title">
						<strong>${esc(a.activity_name || a.name)}</strong>
						<span class="kvp-theme-chips">${themeChips(a)}</span>
					</div>
					<span class="kvp-tag ${statusClass(a.status)}">${esc(a.status || "Draft")}</span>
				</div>

				<div class="kva-project">${icon("grid")}${esc(a.project_title || a.project || "No project")}</div>

				${progressMeter(a)}

				<div class="kvp-facts">
					<span class="kvp-fact">${icon("tasks")}<b>${a.task_open || 0}</b> open steps</span>
					${
						a.target
							? `<span class="kvp-fact">${icon("pulse")}<b>${a.achievement || 0}</b> / ${a.target} (${a.achievement_pct}%)</span>`
							: ""
					}
					${
						a.approved_budget
							? `<span class="kvp-fact">${esc(format_currency(a.total_expenditure || 0))} of ${esc(format_currency(a.approved_budget))}</span>`
							: ""
					}
					${
						a.is_overdue
							? `<span class="kvp-fact due late">${icon("alert")}Overdue</span>`
							: a.end_date
							? `<span class="kvp-fact due">${icon("clock")}${esc(
									frappe.datetime.str_to_user(a.end_date)
							  )}</span>`
							: ""
					}
				</div>

				<div class="kvp-facts" style="border-top:0;padding-top:0">
					<span class="kvp-who">
						<span class="kvp-chip">${esc(initials(a.assignee || "?"))}</span>
						${esc(a.assignee || "Unassigned")}
					</span>
				</div>
			</button>`;
	}

	function render(data) {
		$("#kva-sub").text("Every activity you are responsible for.");

		const scoped = !data.is_org_wide;
		$("#kva-scope")
			.toggleClass("is-hidden", !data.scope_label)
			.toggleClass("org", !scoped);
		$("#kva-scope-text").text(data.scope_label || "");

		$("#kva-new").toggleClass("is-hidden", !data.can_create);

		if (data.task_only) {
			$(".kvp-toolbar").addClass("is-hidden");
			$("#kva-count").text("");
			$("#kva-body").html(`
				<div class="kvp-empty">
					${icon("tasks")}
					<h4>Tasks only</h4>
					<p>Your work is tracked as tasks. Open the dashboard to see everything assigned to you.</p>
				</div>`);
			return;
		}

		$(".kvp-toolbar").removeClass("is-hidden");

		const activities = data.activities || [];
		$("#kva-count").text(activities.length === 1 ? "1 activity" : `${activities.length} activities`);

		if (!activities.length) {
			const filtered = filters.search || filters.status;
			$("#kva-body").html(`
				<div class="kvp-empty">
					${icon("pulse")}
					<h4>${filtered ? "Nothing matches those filters" : "No activities yet"}</h4>
					<p>${
						filtered
							? "Try clearing the search or choosing a different status."
							: "Add an activity from inside a project to see it here."
					}</p>
				</div>`);
			return;
		}

		$("#kva-body").html(`<div class="kvp-grid">${activities.map(card).join("")}</div>`);
	}

	function load() {
		const ticket = ++requestId;

		frappe.call({
			method: "krushi_vikas.krushi_vikas.page.krushi_activities.krushi_activities.get_activity_cards",
			args: { search: filters.search || undefined, status: filters.status || undefined },
			freeze: false,
			callback: (r) => {
				if (ticket !== requestId) return;
				if (r.message) render(r.message);
			},
			error: () => {
				if (ticket !== requestId) return;
				$("#kva-body").html(`<div class="kvp-loading">Could not load activities.</div>`);
			}
		});
	}

	$main.on("input", "#kva-q", function () {
		const value = $(this).val();
		clearTimeout(searchTimer);
		searchTimer = setTimeout(() => {
			filters.search = value;
			load();
		}, 260);
	});

	$main.on("change", "#kva-status", function () { filters.status = $(this).val(); load(); });

	$main.on("click", "#kva-new", () => frappe.new_doc("Activity"));
	$main.on("click", "#kva-dash", () => frappe.set_route("krushi-dashboard"));
	$main.on("click", "#kva-list", () => frappe.set_route("List", "Activity", "List"));

	$main.on("click", "[data-activity]", function () {
		frappe.set_route("Form", "Activity", $(this).data("activity"));
	});

	frappe.pages["krushi-activities"]._refresh = load;
	load();
};

frappe.pages["krushi-activities"].on_page_show = function () {
	const page = frappe.pages["krushi-activities"];
	if (page && page._refresh) page._refresh();
};
