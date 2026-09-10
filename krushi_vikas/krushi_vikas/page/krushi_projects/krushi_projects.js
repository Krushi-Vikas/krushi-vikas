frappe.pages["krushi-projects"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: "", single_column: true });

	const $main = $(wrapper).find(".layout-main-section");

	let loading = false;
	let searchTimer = null;
	const filters = { search: "", status: "", stage: "", group: "none", sort: "recent" };

	const svg = {
		folder: `<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5v-9Z"/>`,
		folderPlus: `<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5v-9Z"/><path d="M12 11v5"/><path d="M9.5 13.5h5"/>`,
		search: `<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>`,
		pulse: `<path d="M3 12h4l2-7 4 14 2-7h6"/>`,
		tasks: `<path d="M4 6.5 6 8.5 10 4.5"/><path d="M4 17.5 6 19.5 10 15.5"/><path d="M13 7h7"/><path d="M13 18h7"/>`,
		clock: `<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>`,
		alert: `<path d="M12 4 2.5 20h19L12 4Z"/><path d="M12 10v4"/><path d="M12 17.2v.1"/>`,
		user: `<circle cx="12" cy="8" r="3.2"/><path d="M5 21c0-4 3-7 7-7s7 3 7 7"/>`,
		grid: `<rect x="3" y="3" width="7" height="7" rx="1.4"/><rect x="14" y="3" width="7" height="7" rx="1.4"/><rect x="3" y="14" width="7" height="7" rx="1.4"/><rect x="14" y="14" width="7" height="7" rx="1.4"/>`,
		back: `<path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-4"/>`,
		flag: `<path d="M5 21V4"/><path d="M5 5h11l-2 3.5L16 12H5"/>`,
		check: `<path d="m5 12 4 4L19 6"/>`
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
			Planning: "s-planning",
			"In Progress": "s-progress",
			Deployed: "s-deployed",
			Completed: "s-completed",
			Cancelled: "s-cancelled"
		}[s] || "s-planning");

	$main.html(`
		<div class="kvp">

			<header class="kvp-head">
				<div>
					<h1>Projects</h1>
					<p id="kvp-sub">Every project you are responsible for.</p>
				</div>
				<div class="kvp-actions">
					<button class="kvp-btn" id="kvp-dash">${icon("back")}<span>Dashboard</span></button>
					<button class="kvp-btn" id="kvp-list">${icon("grid")}<span>Table view</span></button>
					<button class="kvp-btn primary" id="kvp-new">${icon("folderPlus")}<span>New Project</span></button>
				</div>
			</header>

			<div class="kvp-scope is-hidden" id="kvp-scope">
				${icon("user")}<span id="kvp-scope-text"></span>
			</div>

			<div class="kvp-toolbar">
				<div class="kvp-search">
					${icon("search")}
					<input type="text" class="kvp-input" id="kvp-q"
						placeholder="Search projects or themes…" autocomplete="off">
				</div>

				<select class="kvp-select" id="kvp-status">
					<option value="">All statuses</option>
					<option value="Planning">Planning</option>
					<option value="In Progress">In Progress</option>
					<option value="Deployed">Deployed</option>
					<option value="Completed">Completed</option>
					<option value="Cancelled">Cancelled</option>
				</select>

				<select class="kvp-select" id="kvp-stage">
					<option value="">All stages</option>
				</select>

				<select class="kvp-select" id="kvp-sort">
					<option value="recent">Recently updated</option>
					<option value="ending">Ending soonest</option>
					<option value="budget">Largest budget</option>
					<option value="name">Name A–Z</option>
				</select>

				<select class="kvp-select" id="kvp-group">
					<option value="none">No grouping</option>
					<option value="stage">Group by stage</option>
					<option value="status">Group by status</option>
				</select>

				<span class="kvp-count" id="kvp-count"></span>
			</div>

			<div id="kvp-body">
				<div class="kvp-grid">
					${Array.from({ length: 6 }, () => `<div class="kvp-skel"></div>`).join("")}
				</div>
			</div>

		</div>
	`);

	// ── Card ───────────────────────────────────────────────────────
	function stageChip(project) {
		const stage = project.journey_stage;
		if (!stage) return "";

		let cls = "";
		let mark = "flag";

		if (stage === "Closed") {
			cls = " closed";
			mark = "check";
		} else if (stage.startsWith("07")) {
			cls = " pending";
		}

		return `<span class="kvp-stage${cls}">${icon(mark)}${esc(stage)}</span>`;
	}

	function dueFact(project) {
		if (!project.end_date) return "";

		if (project.is_overdue) {
			return `<span class="kvp-fact due late">${icon("alert")}${Math.abs(
				project.days_left
			)}d overdue</span>`;
		}

		if (project.status === "Completed" || project.status === "Cancelled") {
			return `<span class="kvp-fact due">${icon("clock")}${esc(
				frappe.datetime.str_to_user(project.end_date)
			)}</span>`;
		}

		return `<span class="kvp-fact due">${icon("clock")}${project.days_left}d left</span>`;
	}

	function budgetMeter(project) {
		if (!project.budget) {
			return `
				<div class="kvp-meter">
					<div class="kvp-meter-top"><span>No budget set</span></div>
					<div class="kvp-track"><i style="width:0"></i></div>
				</div>`;
		}

		const pct = project.spend_pct || 0;
		const cls = project.overspent ? "over" : pct >= 80 ? "warn" : "";

		return `
			<div class="kvp-meter">
				<div class="kvp-meter-top">
					<span>Spent <b>${esc(
						format_currency(project.actual_amount_spent || 0)
					)}</b> of ${esc(format_currency(project.budget))}</span>
					<b>${pct}%</b>
				</div>
				<div class="kvp-track"><i class="${cls}" style="width:${Math.min(pct, 100)}%"></i></div>
			</div>`;
	}

	function timeMeter(project) {
		if (!(project.start_date && project.end_date)) return "";

		const pct = project.elapsed_pct || 0;

		return `
			<div class="kvp-meter">
				<div class="kvp-meter-top">
					<span>${esc(frappe.datetime.str_to_user(project.start_date))} → ${esc(
						frappe.datetime.str_to_user(project.end_date)
					)}</span>
					<b>${pct}%</b>
				</div>
				<div class="kvp-track"><i class="time" style="width:${pct}%"></i></div>
			</div>`;
	}

	function card(project) {
		const owner = project.project_coordinator || project.project_manager;

		return `
			<button class="kvp-card ${statusClass(project.status)}" data-project="${esc(project.name)}">

				<div class="kvp-card-top">
					<div class="kvp-card-title">
						<strong>${esc(project.project_name || project.name)}</strong>
						<span>${esc(project.theme || "No theme")}</span>
					</div>
					<span class="kvp-tag ${statusClass(project.status)}">${esc(project.status || "Planning")}</span>
				</div>

				${stageChip(project)}
				${budgetMeter(project)}
				${timeMeter(project)}

				<div class="kvp-facts">
					<span class="kvp-fact">${icon("pulse")}<b>${project.activity_count || 0}</b> activities</span>
					<span class="kvp-fact">${icon("tasks")}<b>${project.open_task_count || 0}</b> open</span>
					${dueFact(project)}
				</div>

				<div class="kvp-facts" style="border-top:0;padding-top:0">
					<span class="kvp-who">
						<span class="kvp-chip">${esc(initials(owner || "?"))}</span>
						${esc(owner || "Unassigned")}
					</span>
				</div>

			</button>`;
	}

	// ── Sorting & grouping ─────────────────────────────────────────
	function sortProjects(projects) {
		const list = projects.slice();

		if (filters.sort === "name") {
			list.sort((a, b) =>
				String(a.project_name || a.name).localeCompare(String(b.project_name || b.name))
			);
		} else if (filters.sort === "budget") {
			list.sort((a, b) => (b.budget || 0) - (a.budget || 0));
		} else if (filters.sort === "ending") {
			// Undated projects sink to the bottom rather than sorting as epoch.
			list.sort((a, b) => {
				if (!a.end_date && !b.end_date) return 0;
				if (!a.end_date) return 1;
				if (!b.end_date) return -1;
				return String(a.end_date).localeCompare(String(b.end_date));
			});
		}

		return list;
	}

	function groupProjects(projects, stageOrder) {
		if (filters.group === "none") return [["", projects]];

		const key = filters.group === "stage" ? "journey_stage" : "status";
		const buckets = new Map();

		projects.forEach((project) => {
			const value = project[key] || "Unassigned";
			if (!buckets.has(value)) buckets.set(value, []);
			buckets.get(value).push(project);
		});

		const order =
			filters.group === "stage"
				? stageOrder
				: ["Planning", "In Progress", "Deployed", "Completed", "Cancelled"];

		const sorted = [];

		order.forEach((value) => {
			if (buckets.has(value)) {
				sorted.push([value, buckets.get(value)]);
				buckets.delete(value);
			}
		});

		buckets.forEach((value, name) => sorted.push([name, value]));

		return sorted;
	}

	// ── Render ─────────────────────────────────────────────────────
	function render(data) {
		const projects = sortProjects(data.projects || []);

		$("#kvp-sub").text(
			data.preview
				? `Viewing as ${data.full_name} · ${data.role_label}`
				: "Every project you are responsible for."
		);

		const scoped = !data.is_org_wide;
		$("#kvp-scope")
			.toggleClass("is-hidden", !data.scope_label)
			.toggleClass("org", !scoped);
		$("#kvp-scope-text").text(data.scope_label || "");

		if (!frappe.model.can_create("KV Project") || data.preview) {
			$("#kvp-new").addClass("is-hidden");
		} else {
			$("#kvp-new").removeClass("is-hidden");
		}

		const $stage = $("#kvp-stage");
		if ($stage.find("option").length <= 1) {
			$stage.append(
				(data.stage_order || [])
					.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`)
					.join("")
			);
			$stage.val(filters.stage);
		}

		const total = projects.length;
		$("#kvp-count").text(
			total === 1 ? "1 project" : `${total} projects`
		);

		if (!total) {
			const filtered = filters.search || filters.status || filters.stage;
			$("#kvp-body").html(`
				<div class="kvp-empty">
					${icon("folder")}
					<h4>${filtered ? "Nothing matches those filters" : "No projects yet"}</h4>
					<p>${
						filtered
							? "Try clearing the search or choosing a different status."
							: esc(
									data.is_org_wide
										? "Create a project, or approve a proposal to generate one."
										: "Projects assigned to you will appear here."
							  )
					}</p>
				</div>`);
			return;
		}

		const groups = groupProjects(projects, data.stage_order || []);

		$("#kvp-body").html(
			groups
				.map(([label, items]) => {
					const heading = label
						? `<div class="kvp-group-label">${esc(label)}<b>${items.length}</b></div>`
						: "";
					return `${heading}<div class="kvp-grid">${items.map(card).join("")}</div>`;
				})
				.join("")
		);
	}

	// ── Data ───────────────────────────────────────────────────────
	function load() {
		if (loading) return;
		loading = true;

		frappe.call({
			method: "krushi_vikas.krushi_vikas.page.krushi_projects.krushi_projects.get_project_cards",
			args: {
				search: filters.search || undefined,
				status: filters.status || undefined,
				stage: filters.stage || undefined
			},
			freeze: false,
			callback: (r) => {
				loading = false;
				if (r.message) render(r.message);
			},
			error: () => {
				loading = false;
				$("#kvp-body").html(`<div class="kvp-loading">Could not load projects.</div>`);
			}
		});
	}

	// ── Events ─────────────────────────────────────────────────────
	$main.on("input", "#kvp-q", function () {
		const value = $(this).val();
		clearTimeout(searchTimer);
		searchTimer = setTimeout(() => {
			filters.search = value;
			load();
		}, 260);
	});

	$main.on("change", "#kvp-status", function () { filters.status = $(this).val(); load(); });
	$main.on("change", "#kvp-stage", function () { filters.stage = $(this).val(); load(); });
	$main.on("change", "#kvp-sort", function () { filters.sort = $(this).val(); load(); });
	$main.on("change", "#kvp-group", function () { filters.group = $(this).val(); load(); });

	$main.on("click", "#kvp-new", () => frappe.new_doc("KV Project"));
	$main.on("click", "#kvp-dash", () => frappe.set_route("krushi-dashboard"));
	$main.on("click", "#kvp-list", () => frappe.set_route("List", "KV Project", "List"));

	$main.on("click", "[data-project]", function () {
		frappe.set_route("Form", "KV Project", $(this).data("project"));
	});

	frappe.pages["krushi-projects"]._refresh = load;
	load();
};

frappe.pages["krushi-projects"].on_page_show = function () {
	const page = frappe.pages["krushi-projects"];
	if (page && page._refresh) page._refresh();
};
