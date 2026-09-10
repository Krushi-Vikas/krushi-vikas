frappe.pages["krushi-dashboard"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: "", single_column: true });

	const $main = $(wrapper).find(".layout-main-section");

	let selectedYear = new Date().getFullYear();
	let requestId = 0;
	let previewRole = "";
	let previewUser = "";
	let optionsLoaded = false;

	const routes = {
		projects: () => frappe.set_route("krushi-projects"),
		activities: () => frappe.set_route("List", "Activity", "List"),
		themes: () => frappe.set_route("Tree", "Project Theme"),
		beneficiaries: () => frappe.set_route("List", "Beneficiary", "List"),
		surveys: () => frappe.set_route("List", "Baseline Survey", "List"),
		proposals: () => frappe.set_route("List", "Project Proposal", "List")
	};

	const svg = {
		leaf: `<path d="M12 21V10"/><path d="M12 14C8.1 14 5 11.5 5 7c4.5 0 7 2.6 7 7Z"/><path d="M12 10c0-4 2.5-7 7-7 0 4.5-2.5 7-7 7Z"/>`,
		grid: `<rect x="3" y="3" width="7" height="7" rx="1.4"/><rect x="14" y="3" width="7" height="7" rx="1.4"/><rect x="3" y="14" width="7" height="7" rx="1.4"/><rect x="14" y="14" width="7" height="7" rx="1.4"/>`,
		folder: `<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5v-9Z"/>`,
		folderPlus: `<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5v-9Z"/><path d="M12 11v5"/><path d="M9.5 13.5h5"/>`,
		pulse: `<path d="M3 12h4l2-7 4 14 2-7h6"/>`,
		sprout: `<path d="M12 21V8"/><path d="M12 12C8 12 5 9.8 5 6c4.3 0 7 2.2 7 6Z"/><path d="M12 10c0-3.5 2.4-6 6.5-6 0 3.8-2.5 6-6.5 6Z"/><path d="M8 21h8"/>`,
		users: `<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.5 2.5-6 6-6s6 2.5 6 6"/><path d="M16 5.5a3 3 0 0 1 0 5.8"/><path d="M18 14c2 .8 3 2.5 3 5"/>`,
		clipboard: `<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2"/><path d="M9 10h6"/><path d="M9 14h6"/><path d="M9 18h3"/>`,
		calendar: `<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4"/><path d="M8 3v4"/><path d="M3 10h18"/>`,
		check: `<path d="m5 12 4 4L19 6"/>`,
		user: `<circle cx="12" cy="8" r="3.2"/><path d="M5 21c0-4 3-7 7-7s7 3 7 7"/>`,
		chart: `<path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 15 4-5 3 3 5-7"/>`,
		tasks: `<path d="M4 6.5 6 8.5 10 4.5"/><path d="M4 17.5 6 19.5 10 15.5"/><path d="M13 7h7"/><path d="M13 18h7"/>`,
		alert: `<path d="M12 4 2.5 20h19L12 4Z"/><path d="M12 10v4"/><path d="M12 17.2v.1"/>`,
		left: `<path d="m15 18-6-6 6-6"/>`,
		right: `<path d="m9 18 6-6-6-6"/>`,
		down: `<path d="m6 9 6 6 6-6"/>`,
		eye: `<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>`,
		back: `<path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-4"/>`
	};

	function icon(name) {
		return `<span class="kv-icon"><svg viewBox="0 0 24 24" aria-hidden="true">${
			svg[name] || svg.grid
		}</svg></span>`;
	}

	const esc = (value) => frappe.utils.escape_html(String(value == null ? "" : value));

	function initials(name) {
		const parts = String(name || "?").trim().split(/[\s@._-]+/).filter(Boolean);
		return ((parts[0] || "?")[0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
	}

	$main.html(`
		<div class="kv-app">

			<header class="kv-topbar">
				<div class="kv-brand">
					<div class="kv-mark">${icon("leaf")}</div>
					<div>
						<h1>Krushi Vikas</h1>
						<span>Agri &amp; Watershed Programme</span>
					</div>
				</div>

				<div class="kv-account" id="kv-account">
					<button class="kv-avatar-btn" id="kv-avatar-btn" aria-haspopup="true" aria-expanded="false">
						<span class="kv-avatar" id="kv-avatar">A</span>
						<span class="kv-avatar-meta">
							<strong id="kv-user-name">&nbsp;</strong>
							<span id="kv-user-role">&nbsp;</span>
						</span>
						<span class="kv-icon kv-caret">${
							`<svg viewBox="0 0 24 24">${svg.down}</svg>`
						}</span>
					</button>

					<div class="kv-menu is-hidden" id="kv-menu" role="menu">
						<div class="kv-menu-head">
							<span class="kv-avatar" id="kv-menu-avatar">A</span>
							<div class="kv-menu-identity">
								<strong id="kv-menu-name">&nbsp;</strong>
								<span id="kv-menu-email">&nbsp;</span>
							</div>
						</div>

						<div class="kv-menu-section is-hidden" id="kv-viewas">
							<label class="kv-menu-label">${"View dashboard as"}</label>
							<select class="kv-select" id="kv-role-select">
								<option value="">Any role</option>
							</select>
							<select class="kv-select" id="kv-user-select">
								<option value="">Myself</option>
							</select>
							<p class="kv-menu-hint">
								Renders the dashboard exactly as that person sees it.
								Read-only — your session does not change.
							</p>
						</div>

						<button class="kv-menu-action danger is-hidden" id="kv-reset">
							${icon("back")}<span>Back to my own view</span>
						</button>
					</div>
				</div>
			</header>

			<div class="kv-preview-strip is-hidden" id="kv-preview-strip">
				${icon("eye")}
				<span id="kv-preview-text"></span>
				<button id="kv-preview-exit">Exit preview</button>
			</div>

			<nav class="kv-nav">
				<button class="kv-nav-item active" data-route="overview">${icon("grid")}<span>Overview</span></button>
				<button class="kv-nav-item" data-route="projects" data-perm="project">${icon("folder")}<span>Projects</span></button>
				<button class="kv-nav-item" data-route="activities" data-perm="activity">${icon("pulse")}<span>Activities</span></button>
				<button class="kv-nav-item" data-route="proposals" data-perm="proposal">${icon("clipboard")}<span>Proposals</span></button>
				<button class="kv-nav-item" data-route="themes" data-perm="theme">${icon("sprout")}<span>Themes</span></button>
				<button class="kv-nav-item" data-route="beneficiaries" data-perm="beneficiary">${icon("users")}<span>Beneficiaries</span></button>
				<button class="kv-nav-item" data-route="surveys" data-perm="survey">${icon("tasks")}<span>Surveys</span></button>
			</nav>

			<section class="kv-hero">
				<div>
					<h2>Welcome, <span id="kv-greeting">there</span></h2>
					<p id="kv-scope-line">Plan and manage agricultural and watershed projects.</p>
				</div>

				<div class="kv-hero-actions">
					<div class="kv-year">
						<button id="kv-prev-year" title="Previous year">${icon("left")}</button>
						<strong id="kv-year">${selectedYear}</strong>
						<button id="kv-next-year" title="Next year">${icon("right")}</button>
					</div>
					<button class="kv-cta" id="kv-create">${icon("folderPlus")}<span>New Project</span></button>
				</div>
			</section>

			<section class="kv-kpis" id="kv-kpis">
				<button class="kv-kpi" data-route="projects">
					<span class="kv-kpi-chip green">${icon("folder")}</span>
					<span class="kv-kpi-body">
						<span>Projects</span><strong id="kpi-total">0</strong>
						<em id="kpi-total-sub">in <span class="kv-yr">${selectedYear}</span></em>
					</span>
				</button>
				<div class="kv-kpi">
					<span class="kv-kpi-chip blue">${icon("pulse")}</span>
					<span class="kv-kpi-body">
						<span>Active</span><strong id="kpi-active">0</strong>
						<em>in progress or deployed</em>
					</span>
				</div>
				<div class="kv-kpi">
					<span class="kv-kpi-chip amber">${icon("calendar")}</span>
					<span class="kv-kpi-body">
						<span>Planned</span><strong id="kpi-planned">0</strong>
						<em>not yet started</em>
					</span>
				</div>
				<div class="kv-kpi">
					<span class="kv-kpi-chip violet">${icon("check")}</span>
					<span class="kv-kpi-body">
						<span>Completed</span><strong id="kpi-done">0</strong>
						<em id="kpi-done-sub">&nbsp;</em>
					</span>
				</div>
			</section>

			<div class="kv-split" id="kv-split">
				<section class="kv-card">
					<div class="kv-card-head">
						<div class="kv-card-title">
							<span class="kv-title-chip">${icon("clipboard")}</span>
							<div><h3>My Work</h3><p>Assigned to you across every project</p></div>
						</div>
						<div class="kv-pills">
							<span class="kv-pill"><strong id="my-acts">0</strong><span>activities</span></span>
							<span class="kv-pill"><strong id="my-tasks-n">0</strong><span>open tasks</span></span>
							<span class="kv-pill alert is-hidden" id="overdue-pill">
								${icon("alert")}<strong id="my-overdue">0</strong><span>overdue</span>
							</span>
						</div>
					</div>
					<div class="kv-worksplit">
						<div id="my-activities-col">
							<h4 class="kv-subhead">${icon("pulse")}<span>Activities</span></h4>
							<div id="my-activities"></div>
						</div>
						<div>
							<h4 class="kv-subhead">${icon("tasks")}<span>Tasks</span></h4>
							<div id="my-tasks"></div>
						</div>
					</div>
				</section>

				<section class="kv-card" id="kv-portfolio">
					<div class="kv-card-head">
						<div class="kv-card-title">
							<span class="kv-title-chip">${icon("chart")}</span>
							<div><h3>Portfolio</h3><p>Status mix</p></div>
						</div>
					</div>
					<div id="kv-status"></div>
				</section>
			</div>

			<section class="kv-card" id="kv-plan-card" style="margin-top:18px">
				<div class="kv-card-head">
					<div class="kv-card-title">
						<span class="kv-title-chip">${icon("calendar")}</span>
						<div><h3>Annual Plan</h3><p>When each project runs through the year</p></div>
					</div>
				</div>
				<div id="kv-plan"><div class="kv-loading">Loading plan…</div></div>
			</section>

			<section class="kv-card" id="kv-recent-card">
				<div class="kv-card-head">
					<div class="kv-card-title">
						<span class="kv-title-chip">${icon("folder")}</span>
						<div><h3>Recent Projects</h3><p>Most recently scheduled</p></div>
					</div>
					<button class="kv-linkbtn" id="kv-viewall">View all ${icon("right")}</button>
				</div>
				<div id="kv-recent"></div>
			</section>

		</div>
	`);

	// ── Permissions on the nav (real session user, always) ──────────
	function applyNavPermissions() {
		const can = {
			project: frappe.model.can_read("KV Project"),
			activity: frappe.model.can_read("Activity"),
			proposal: frappe.model.can_read("Project Proposal"),
			theme: frappe.model.can_read("Project Theme"),
			beneficiary: frappe.model.can_read("Beneficiary"),
			survey: frappe.model.can_read("Baseline Survey")
		};

		$main.find("[data-perm]").each(function () {
			if (!can[$(this).data("perm")]) $(this).remove();
		});

		if (!frappe.model.can_create("KV Project")) $("#kv-create").addClass("is-hidden");
	}

	// ── Helpers ────────────────────────────────────────────────────
	function statusClass(status) {
		return {
			Planning: "s-planning", "Not Started": "s-planning", Draft: "s-planning", Open: "s-planning",
			"In Progress": "s-progress", Working: "s-progress",
			Deployed: "s-deployed", "Pending Review": "s-deployed",
			Completed: "s-completed", Approved: "s-completed",
			Cancelled: "s-cancelled", Rejected: "s-cancelled"
		}[status] || "s-planning";
	}

	function parseDate(value) {
		if (!value) return null;
		const parts = String(value).split("-");
		if (parts.length === 3) {
			return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
		}
		const d = new Date(value);
		return Number.isNaN(d.getTime()) ? null : d;
	}

	function due(value) {
		// Task.exp_end_date is a datetime in ERPNext, so trim the time part
		// before formatting or every row reads "… 00:00:00".
		if (!value) return "No due date";
		return `Due ${frappe.datetime.str_to_user(String(value).split(" ")[0])}`;
	}

	function emptySmall($el, iconName, message) {
		$el.html(`<div class="kv-empty-sm">${icon(iconName)}<span>${esc(message)}</span></div>`);
	}

	// ── Identity + account menu ────────────────────────────────────
	function renderIdentity(data) {
		const name = data.full_name || data.user || "User";

		$("#kv-avatar, #kv-menu-avatar").text(initials(name));
		$("#kv-user-name, #kv-menu-name").text(name);
		$("#kv-user-role").text(data.role_label || "User");
		$("#kv-menu-email").text(data.user || "");
		$("#kv-greeting").text(String(name).split(" ")[0]);
		$("#kv-scope-line").text(
			data.scope_label || "Plan and manage agricultural and watershed projects."
		);

		const previewing = !!data.preview;
		$("#kv-account").toggleClass("is-previewing", previewing);
		$("#kv-preview-strip").toggleClass("is-hidden", !previewing);
		$("#kv-reset").toggleClass("is-hidden", !previewing);

		if (previewing) {
			$("#kv-preview-text").text(
				`Viewing as ${name}${data.role_label ? ` · ${data.role_label}` : ""}`
			);
		}

		// Desk permission helpers answer for the real session user, so the
		// create button would lie while previewing somebody else.
		// While previewing, the desk helper answers for the real session
		// user, so the server tells us what the previewed person may do.
		const mayCreate = previewing
			? !!data.can_create_project
			: frappe.model.can_create("KV Project");

		$("#kv-create").toggleClass("is-hidden", !mayCreate);

		if (data.can_preview) {
			$("#kv-viewas").removeClass("is-hidden");
			if (!optionsLoaded) {
				optionsLoaded = true;
				loadPreviewOptions();
			}
		} else {
			$("#kv-viewas").addClass("is-hidden");
		}
	}

	function closeMenu() {
		$("#kv-account").removeClass("is-open");
		$("#kv-menu").addClass("is-hidden");
		$("#kv-avatar-btn").attr("aria-expanded", "false");
	}

	function loadPreviewOptions() {
		frappe.call({
			method: "krushi_vikas.krushi_vikas.page.krushi_dashboard.krushi_dashboard.get_preview_options",
			args: { role: previewRole || undefined },
			freeze: false,
			callback: (r) => {
				const options = r.message;
				if (!options) return;

				const $role = $("#kv-role-select");
				if ($role.find("option").length <= 1) {
					$role.append(
						options.roles
							.map((x) => `<option value="${esc(x.role)}">${esc(x.role)} · ${x.user_count}</option>`)
							.join("")
					);
					$role.val(previewRole);
				}

				$("#kv-user-select").html(
					`<option value="">Myself</option>` +
						options.users
							.map(
								(u) =>
									`<option value="${esc(u.name)}">${esc(u.full_name || u.name)} — ${esc(u.role_label)}</option>`
							)
							.join("")
				);

				if (previewUser && !options.users.some((u) => u.name === previewUser)) {
					previewUser = "";
					loadDashboard();
				}

				$("#kv-user-select").val(previewUser);
			}
		});
	}

	// ── Renderers ──────────────────────────────────────────────────
	function renderKpis(stats) {
		$("#kpi-total").text(stats.total_projects || 0);
		$("#kpi-active").text(stats.active_projects || 0);
		$("#kpi-planned").text(stats.planning_projects || 0);
		$("#kpi-done").text(stats.completed_projects || 0);
		$(".kv-yr").text(selectedYear);

		const total = stats.total_projects || 0;
		const done = stats.completed_projects || 0;
		$("#kpi-done-sub").text(total ? `${Math.round((done / total) * 100)}% of portfolio` : "—");
	}

	function renderMyWork(data) {
		const stats = data.stats || {};

		$("#my-acts").text(stats.my_open_activities || 0);
		$("#my-tasks-n").text(stats.pending_tasks || 0);
		$("#my-overdue").text(stats.overdue_tasks || 0);
		$("#overdue-pill").toggleClass("is-hidden", !(stats.overdue_tasks > 0));

		const $acts = $("#my-activities");
		const activities = data.my_activities || [];

		if (!activities.length) {
			emptySmall($acts, "pulse", "No activities assigned to you.");
		} else {
			$acts.html(
				activities
					.map(
						(a) => `
						<button class="kv-row${a.is_overdue ? " overdue" : ""}" data-activity="${esc(a.name)}">
							<span class="kv-row-dot"></span>
							<span class="kv-row-body">
								<strong>${esc(a.activity_name || a.name)}</strong>
								<span>${esc(a.project || "No project")} · ${esc(due(a.end_date))}</span>
							</span>
							<span class="kv-tag ${statusClass(a.status)}">${esc(a.status || "Draft")}</span>
						</button>`
					)
					.join("")
			);
		}

		const $tasks = $("#my-tasks");
		const tasks = data.my_tasks || [];

		if (!tasks.length) {
			emptySmall($tasks, "tasks", "No tasks assigned to you.");
		} else {
			$tasks.html(
				tasks
					.map(
						(t) => `
						<button class="kv-row${t.is_overdue ? " overdue" : ""}" data-task="${esc(t.name)}">
							<span class="kv-row-dot"></span>
							<span class="kv-row-body">
								<strong>${esc(t.subject || t.name)}</strong>
								<span>${esc(t.activity_label || "General task")} · ${esc(due(t.exp_end_date))}</span>
							</span>
							<span class="kv-tag ${statusClass(t.status)}">${esc(t.status || "Open")}</span>
						</button>`
					)
					.join("")
			);
		}
	}

	function renderStatus(stats) {
		const total = stats.total_projects || 0;

		const rows = [
			{ label: "Planning", value: stats.planning_projects || 0, cls: "s-planning" },
			{ label: "Active", value: stats.active_projects || 0, cls: "s-progress" },
			{ label: "Completed", value: stats.completed_projects || 0, cls: "s-completed" },
			{ label: "Cancelled", value: stats.cancelled_projects || 0, cls: "s-cancelled" }
		];

		$("#kv-status").html(
			rows
				.map((row) => {
					const pct = total ? Math.round((row.value / total) * 100) : 0;
					return `
						<div class="kv-stat">
							<div class="kv-stat-top">
								<span class="kv-stat-name"><i class="kv-dot ${row.cls}"></i>${row.label}</span>
								<span class="kv-stat-val"><strong>${row.value}</strong><span>${pct}%</span></span>
							</div>
							<div class="kv-bar"><i class="${row.cls}" style="width:${pct}%"></i></div>
						</div>`;
				})
				.join("")
		);
	}

	function renderPlan(projects) {
		const $plan = $("#kv-plan");
		const yearStart = new Date(selectedYear, 0, 1);
		const yearEnd = new Date(selectedYear, 11, 31);
		const totalDays = (new Date(selectedYear + 1, 0, 1) - yearStart) / 86400000;

		const visible = (projects || []).filter((p) => {
			const s = parseDate(p.start_date);
			const e = parseDate(p.end_date);
			return s && e && s <= yearEnd && e >= yearStart;
		});

		if (!visible.length) {
			$plan.html(`
				<div class="kv-empty">
					${icon("calendar")}
					<h4>Nothing scheduled for ${selectedYear}</h4>
					<p>Projects with a start and end date in this year will appear here as a timeline.</p>
				</div>`);
			return;
		}

		const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
		const cells = months.map(() => `<span></span>`).join("");

		const rows = visible
			.map((p) => {
				const s0 = parseDate(p.start_date);
				const e0 = parseDate(p.end_date);
				const s = s0 < yearStart ? yearStart : s0;
				const e = e0 > yearEnd ? yearEnd : e0;
				const left = (((s - yearStart) / 86400000) / totalDays) * 100;
				const width = ((((e - s) / 86400000) + 1) / totalDays) * 100;
				const name = esc(p.project_name || p.name);
				const owner = esc(p.project_coordinator || p.project_manager || "Unassigned");

				return `
					<div class="kv-tl-row">
						<button class="kv-tl-name" data-project="${esc(p.name)}">
							<span class="kv-row-dot"></span>
							<span class="kv-row-body">
								<strong>${name}</strong>
								<span>${owner}</span>
							</span>
						</button>
						<div class="kv-tl-track">
							<div class="kv-tl-grid">${cells}</div>
							<button class="kv-tl-bar ${statusClass(p.status)}"
								style="left:${left}%;width:${width}%"
								data-project="${esc(p.name)}" title="${name}">${name}</button>
						</div>
					</div>`;
			})
			.join("");

		$plan.html(`
			<div class="kv-timeline">
				<div class="kv-tl-head">
					<div>Project</div>
					<div class="kv-tl-months">${months.map((m) => `<div>${m}</div>`).join("")}</div>
				</div>
				${rows}
			</div>`);
	}

	function renderRecent(projects) {
		const $recent = $("#kv-recent");

		if (!projects || !projects.length) {
			emptySmall($recent, "folder", "No projects found.");
			return;
		}

		$recent.html(
			projects
				.map(
					(p) => `
					<button class="kv-row" data-project="${esc(p.name)}">
						<span class="kv-row-dot"></span>
						<span class="kv-row-body">
							<strong>${esc(p.project_name || p.name)}</strong>
							<span>${esc(p.project_manager || "No manager assigned")}</span>
						</span>
						<span class="kv-tag ${statusClass(p.status)}">${esc(p.status || "Planning")}</span>
					</button>`
				)
				.join("")
		);
	}

	function applyRoleView(data) {
		// A field officer sees their task list and nothing else: no
		// portfolio figures, no plan, no project rows.
		const tasksOnly = !!data.task_only;

		$("#kv-kpis, #kv-portfolio, #kv-recent-card").toggleClass("is-hidden", tasksOnly);
		$("#my-activities-col").toggleClass("is-hidden", tasksOnly);
		$("#kv-split").toggleClass("kv-single", tasksOnly);
		$main.find(".kv-worksplit").toggleClass("kv-single", tasksOnly);

		// The Annual Plan is an executive view. Its contents are already
		// scoped; this decides whether the panel exists at all.
		$("#kv-plan-card").toggleClass("is-hidden", !data.can_see_plan);

		// Nav is trimmed to what this person can actually act on.
		$main
			.find(
				'[data-route="projects"], [data-route="activities"],' +
					'[data-route="proposals"], [data-route="themes"],' +
					'[data-route="beneficiaries"]'
			)
			.toggleClass("is-hidden", tasksOnly);
	}

	function render(data) {
		renderIdentity(data);
		applyRoleView(data);
		renderKpis(data.stats || {});
		renderMyWork(data);
		renderStatus(data.stats || {});
		if (data.can_see_plan) renderPlan(data.projects || []);
		renderRecent(data.recent_projects || []);
	}

	// ── Data ───────────────────────────────────────────────────────
	function loadDashboard() {
		// Never drop a request: switching preview user twice in quick
		// succession used to leave the second switch silently ignored.
		// Every call fires; only the newest response is rendered.
		const ticket = ++requestId;

		$("#kv-year").text(selectedYear);
		$("#kv-plan").html(`<div class="kv-loading">Loading ${selectedYear} plan…</div>`);

		frappe.call({
			method: "krushi_vikas.krushi_vikas.page.krushi_dashboard.krushi_dashboard.get_dashboard_data",
			args: { year: selectedYear, preview_user: previewUser || undefined },
			freeze: false,
			callback: (r) => {
				if (ticket !== requestId) return;
				if (!r.message) {
					frappe.msgprint({
						title: "Dashboard",
						message: "Unable to load dashboard data.",
						indicator: "red"
					});
					return;
				}
				render(r.message);
			},
			error: () => {
				if (ticket !== requestId) return;
				$("#kv-plan").html(`<div class="kv-loading">Could not load the dashboard.</div>`);
			}
		});
	}

	// ── Events ─────────────────────────────────────────────────────
	$main.on("click", "#kv-avatar-btn", function (event) {
		event.stopPropagation();
		const open = !$("#kv-account").hasClass("is-open");
		$("#kv-account").toggleClass("is-open", open);
		$("#kv-menu").toggleClass("is-hidden", !open);
		$(this).attr("aria-expanded", String(open));
	});

	$main.on("click", "#kv-menu", (event) => event.stopPropagation());
	$(document).on("click.kvdash", closeMenu);
	$(document).on("keydown.kvdash", (event) => {
		if (event.key === "Escape") closeMenu();
	});

	$main.on("change", "#kv-role-select", function () {
		previewRole = $(this).val() || "";
		loadPreviewOptions();
	});

	$main.on("change", "#kv-user-select", function () {
		previewUser = $(this).val() || "";
		closeMenu();
		loadDashboard();
	});

	$main.on("click", "#kv-reset, #kv-preview-exit", function () {
		previewUser = "";
		previewRole = "";
		$("#kv-role-select").val("");
		$("#kv-user-select").val("");
		closeMenu();
		loadPreviewOptions();
		loadDashboard();
	});

	$main.on("click", ".kv-nav-item", function () {
		const route = $(this).data("route");
		if (route === "overview") {
			$(".kv-nav-item").removeClass("active");
			$(this).addClass("active");
			loadDashboard();
			return;
		}
		if (routes[route]) routes[route]();
	});

	$main.on("click", "#kv-create", () => frappe.new_doc("KV Project"));
	$main.on("click", "#kv-viewall", () => routes.projects());
	$main.on("click", "#kv-prev-year", () => { selectedYear -= 1; loadDashboard(); });
	$main.on("click", "#kv-next-year", () => { selectedYear += 1; loadDashboard(); });

	$main.on("click", "[data-project]", function () {
		const name = $(this).data("project");
		if (name && frappe.model.can_read("KV Project")) frappe.set_route("Form", "KV Project", name);
	});

	$main.on("click", "[data-activity]", function () {
		const name = $(this).data("activity");
		if (name && frappe.model.can_read("Activity")) frappe.set_route("Form", "Activity", name);
	});

	$main.on("click", "[data-task]", function () {
		const name = $(this).data("task");
		if (name && frappe.model.can_read("Task")) frappe.set_route("Form", "Task", name);
	});

	frappe.pages["krushi-dashboard"]._refresh = loadDashboard;

	applyNavPermissions();
	loadDashboard();
};

frappe.pages["krushi-dashboard"].on_page_show = function () {
	const page = frappe.pages["krushi-dashboard"];
	if (page && page._refresh) page._refresh();
};
