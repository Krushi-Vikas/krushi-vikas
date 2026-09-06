frappe.pages["krushi-dashboard"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "",
		single_column: true
	});

	const $main = $(wrapper).find(".layout-main-section");

	let selectedYear = new Date().getFullYear();
	let loading = false;
	let previewRole = "";
	let previewUser = "";

	const routes = {
		dashboard: () => frappe.set_route("krushi-dashboard"),
		projects: () => frappe.set_route("List", "KV Project", "List"),
		activities: () => frappe.set_route("List", "Activity", "List"),
		themes: () => frappe.set_route("Tree", "Project Theme"),
		beneficiaries: () => frappe.set_route("List", "Beneficiary", "List"),
		surveys: () => frappe.set_route("List", "Baseline Survey", "List")
	};

	const icons = {
		plant: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M12 21V10"/>
				<path d="M12 14C8.1 14 5 11.5 5 7c4.5 0 7 2.6 7 7Z"/>
				<path d="M12 10c0-4 2.5-7 7-7 0 4.5-2.5 7-7 7Z"/>
			</svg>
		`,
		dashboard: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<rect x="3" y="3" width="7" height="7" rx="1.2"/>
				<rect x="14" y="3" width="7" height="7" rx="1.2"/>
				<rect x="3" y="14" width="7" height="7" rx="1.2"/>
				<rect x="14" y="14" width="7" height="7" rx="1.2"/>
			</svg>
		`,
		folder: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5v-9Z"/>
			</svg>
		`,
		folderPlus: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5v-9Z"/>
				<path d="M12 11v5"/>
				<path d="M9.5 13.5h5"/>
			</svg>
		`,
		activity: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M3 12h4l2-7 4 14 2-7h6"/>
			</svg>
		`,
		theme: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M12 21V8"/>
				<path d="M12 12C8 12 5 9.8 5 6c4.3 0 7 2.2 7 6Z"/>
				<path d="M12 10c0-3.5 2.4-6 6.5-6 0 3.8-2.5 6-6.5 6Z"/>
				<path d="M8 21h8"/>
			</svg>
		`,
		users: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<circle cx="9" cy="8" r="3"/>
				<path d="M3 20c0-3.5 2.5-6 6-6s6 2.5 6 6"/>
				<path d="M16 5.5a3 3 0 0 1 0 5.8"/>
				<path d="M18 14c2 .8 3 2.5 3 5"/>
			</svg>
		`,
		clipboard: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<rect x="5" y="4" width="14" height="17" rx="2"/>
				<path d="M9 4V2h6v2"/>
				<path d="M9 10h6"/>
				<path d="M9 14h6"/>
				<path d="M9 18h3"/>
			</svg>
		`,
		task: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M4 6.5 6 8.5 10 4.5"/>
				<path d="M4 17.5 6 19.5 10 15.5"/>
				<path d="M13 7h7"/>
				<path d="M13 18h7"/>
			</svg>
		`,
		alert: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M12 4 2.5 20h19L12 4Z"/>
				<path d="M12 10v4"/>
				<path d="M12 17.2v.1"/>
			</svg>
		`,
		calendar: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<rect x="3" y="5" width="18" height="16" rx="2"/>
				<path d="M16 3v4"/>
				<path d="M8 3v4"/>
				<path d="M3 10h18"/>
			</svg>
		`,
		check: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="m5 12 4 4L19 6"/>
			</svg>
		`,
		user: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<circle cx="12" cy="8" r="3"/>
				<path d="M5 21c0-4 3-7 7-7s7 3 7 7"/>
			</svg>
		`,
		chart: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M4 19V5"/>
				<path d="M4 19h16"/>
				<path d="m7 15 4-5 3 3 5-7"/>
			</svg>
		`,
		left: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="m15 18-6-6 6-6"/>
			</svg>
		`,
		right: `
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="m9 18 6-6-6-6"/>
			</svg>
		`
	};

	function icon(name) {
		return `<span class="kv-icon">${icons[name] || icons.dashboard}</span>`;
	}

	$main.html(`
		<div class="kv-dashboard">

			<header class="kv-header">
				<div class="kv-brand">
					<div class="kv-logo">
						${icon("plant")}
					</div>

					<div class="kv-brand-text">
						<h1>Krushi Vikas</h1>
					</div>
				</div>

				<div class="kv-user">
					<div class="kv-user-avatar">
						${icon("user")}
					</div>

					<div>
						<strong id="kv-user-name">Administrator</strong>
						<span id="kv-role">Administrator</span>
					</div>
				</div>
			</header>

			<nav class="kv-nav">
				<button class="kv-nav-item active" data-route="dashboard">
					${icon("dashboard")}
					<span>Overview</span>
				</button>

				<button class="kv-nav-item" data-route="projects" data-permission="project">
					${icon("folder")}
					<span>Projects</span>
				</button>

				<button class="kv-nav-item" data-route="activities" data-permission="activity">
					${icon("activity")}
					<span>Activities</span>
				</button>

				<button class="kv-nav-item" data-route="themes" data-permission="theme">
					${icon("theme")}
					<span>Themes</span>
				</button>

				<button class="kv-nav-item" data-route="beneficiaries" data-permission="beneficiary">
					${icon("users")}
					<span>Beneficiaries</span>
				</button>

				<button class="kv-nav-item" data-route="surveys" data-permission="survey">
					${icon("clipboard")}
					<span>Surveys</span>
				</button>
			</nav>

			<section class="kv-welcome">
				<div class="kv-welcome-content">
					<h2>
						Welcome,
						<span id="kv-welcome-user">Administrator</span>
					</h2>

					<p>
						Plan and manage agricultural and watershed projects.
					</p>
				</div>

				<div class="kv-welcome-actions">
					<div class="kv-year-selector">
						<button
							id="previous-year"
							class="kv-year-btn"
							title="Previous year"
							aria-label="Previous year"
						>
							${icon("left")}
						</button>

						<strong id="welcome-year">${selectedYear}</strong>

						<button
							id="next-year"
							class="kv-year-btn"
							title="Next year"
							aria-label="Next year"
						>
							${icon("right")}
						</button>
					</div>

					<button
						id="create-project"
						class="kv-create-project"
					>
						${icon("folderPlus")}
						<span>Create Project</span>
					</button>
				</div>
			</section>

			<section class="kv-preview is-hidden" id="kv-preview">

				<div class="kv-preview-controls">
					<span class="kv-preview-label">
						${icon("user")}
						<span>Viewing as</span>
					</span>

					<select class="kv-select" id="kv-preview-role">
						<option value="">Any role</option>
					</select>

					<select class="kv-select" id="kv-preview-user">
						<option value="">Myself</option>
					</select>

					<button class="kv-link-button is-hidden" id="kv-preview-reset">
						Back to my own view
					</button>
				</div>

				<div id="kv-access-matrix"></div>

			</section>

			<div class="kv-scope-banner is-hidden" id="kv-scope-banner">
				${icon("user")}
				<span id="kv-scope-text"></span>
			</div>

			<section class="kv-kpi-grid">

				<div class="kv-kpi-card kv-clickable" data-route="projects">
					<div class="kv-kpi-icon green">
						${icon("folder")}
					</div>

					<div class="kv-kpi-content">
						<span>Projects</span>
						<strong id="total-projects">0</strong>
					</div>
				</div>

				<div class="kv-kpi-card">
					<div class="kv-kpi-icon blue">
						${icon("activity")}
					</div>

					<div class="kv-kpi-content">
						<span>Active Projects</span>
						<strong id="active-projects">0</strong>
					</div>
				</div>

				<div class="kv-kpi-card">
					<div class="kv-kpi-icon amber">
						${icon("calendar")}
					</div>

					<div class="kv-kpi-content">
						<span>Planned</span>
						<strong id="planning-projects">0</strong>
					</div>
				</div>

				<div class="kv-kpi-card">
					<div class="kv-kpi-icon purple">
						${icon("check")}
					</div>

					<div class="kv-kpi-content">
						<span>Completed</span>
						<strong id="completed-projects">0</strong>
					</div>
				</div>

			</section>

			<section class="kv-card kv-mywork">

				<div class="kv-card-header">
					<div>
						<div class="kv-card-title">
							<span class="kv-title-icon">
								${icon("clipboard")}
							</span>

							<div>
								<h3>My Work</h3>
								<p>Activities and tasks assigned to you</p>
							</div>
						</div>
					</div>

					<div class="kv-count-pills">
						<span class="kv-count-pill">
							<strong id="my-open-activities">0</strong>
							<span>open activities</span>
						</span>

						<span class="kv-count-pill">
							<strong id="my-pending-tasks">0</strong>
							<span>open tasks</span>
						</span>

						<span class="kv-count-pill danger is-hidden" id="overdue-pill">
							${icon("alert")}
							<strong id="my-overdue-tasks">0</strong>
							<span>overdue</span>
						</span>
					</div>
				</div>

				<div class="kv-mywork-grid">

					<div class="kv-mywork-column">
						<h4 class="kv-subhead">
							${icon("activity")}
							<span>My Activities</span>
						</h4>

						<div id="my-activities"></div>
					</div>

					<div class="kv-mywork-column">
						<h4 class="kv-subhead">
							${icon("task")}
							<span>My Tasks</span>
						</h4>

						<div id="my-tasks"></div>
					</div>

				</div>

			</section>

			<section class="kv-card">

				<div class="kv-card-header">
					<div>
						<div class="kv-card-title">
							<span class="kv-title-icon">
								${icon("calendar")}
							</span>

							<div>
								<h3>Annual Project Plan</h3>
								<p>Plan when projects will run throughout the year.</p>
							</div>
						</div>
					</div>
				</div>

				<div id="project-gantt">
					<div class="kv-loading">
						Loading project plan...
					</div>
				</div>

			</section>

			<div class="kv-bottom-grid">

				<section class="kv-card">

					<div class="kv-card-header">
						<div>
							<div class="kv-card-title">
								<span class="kv-title-icon">
									${icon("folder")}
								</span>

								<div>
									<h3>Recent Projects</h3>
									<p>Latest project planning activity</p>
								</div>
							</div>
						</div>

						<button
							class="kv-link-button"
							id="view-all-projects"
						>
							View all
							${icon("right")}
						</button>
					</div>

					<div id="recent-projects"></div>

				</section>

				<section class="kv-card">

					<div class="kv-card-header">
						<div>
							<div class="kv-card-title">
								<span class="kv-title-icon">
									${icon("chart")}
								</span>

								<div>
									<h3>Project Status</h3>
									<p>Current annual portfolio</p>
								</div>
							</div>
						</div>
					</div>

					<div id="project-status"></div>

				</section>

			</div>

		</div>
	`);

	function getPermissions() {
		return {
			project: frappe.model.can_read("KV Project"),
			activity: frappe.model.can_read("Activity"),
			theme: frappe.model.can_read("Project Theme"),
			beneficiary: frappe.model.can_read("Beneficiary"),
			survey: frappe.model.can_read("Baseline Survey")
		};
	}

	function applyPermissions() {
		const permissions = getPermissions();

		$main.find("[data-permission]").each(function () {
			const permission = $(this).data("permission");

			if (!permissions[permission]) {
				$(this).remove();
			}
		});

		if (!frappe.model.can_create("KV Project")) {
			$("#create-project").remove();
		}
	}

	function setUser(data) {
		const user = data.user || "User";
		const displayName =
			data.full_name ||
			(user === "Administrator" ? "Administrator" : user.split("@")[0]);

		$("#kv-user-name").text(displayName);
		$("#kv-welcome-user").text(displayName);
		$("#kv-role").text(data.role_label || "User");

		const banner = $("#kv-scope-banner");
		let scopeText = data.scope_label || "";

		if (data.preview) {
			scopeText = `Previewing as ${
				data.full_name || data.user
			}. ${scopeText}`;
		}

		if (scopeText) {
			$("#kv-scope-text").text(scopeText);
			banner.removeClass("is-hidden");
			banner.toggleClass(
				"is-personal",
				!data.is_org_wide || !!data.preview
			);
			banner.toggleClass("is-preview", !!data.preview);
		} else {
			banner.addClass("is-hidden");
		}

		// Desk permission helpers always answer for the real session user,
		// so the create button would lie during a preview.
		$("#create-project").toggleClass("is-hidden", !!data.preview);
	}

	function parseDate(value) {
		if (!value) return null;

		const parts = String(value).split("-");

		if (parts.length === 3) {
			return new Date(
				Number(parts[0]),
				Number(parts[1]) - 1,
				Number(parts[2])
			);
		}

		const date = new Date(value);
		return Number.isNaN(date.getTime()) ? null : date;
	}

	function getStatusClass(status) {
		return {
			Planning: "planning",
			"In Progress": "progress",
			Deployed: "deployed",
			Completed: "completed",
			Cancelled: "cancelled"
		}[status] || "planning";
	}

	function renderPreview(data) {
		if (!data.can_preview) {
			$("#kv-preview").addClass("is-hidden");
			return;
		}

		const wasHidden = $("#kv-preview").hasClass("is-hidden");

		$("#kv-preview").removeClass("is-hidden");

		if (wasHidden) {
			loadPreviewOptions();
		}

		$("#kv-preview").toggleClass("is-active", !!data.preview);
		$("#kv-preview-reset").toggleClass("is-hidden", !data.preview);

		renderAccessMatrix(data);
	}

	function renderAccessMatrix(data) {
		const access = data.access;
		const container = $("#kv-access-matrix");

		if (!access) {
			container.empty();
			return;
		}

		const who = frappe.utils.escape_html(
			data.full_name || data.user || ""
		);

		const role = frappe.utils.escape_html(access.role_label || "User");

		const header = access.ptypes
			.map(
				(ptype) =>
					`<th>${frappe.utils.escape_html(ptype)}</th>`
			)
			.join("");

		const caveats = [];

		const rows = access.rows
			.map((row) => {
				const cells = access.ptypes
					.map((ptype) => {
						const entry = row.permissions[ptype] || {};

						if (entry.caveat) {
							caveats.push(
								`${row.doctype} · ${ptype}: ${entry.caveat}`
							);
						}

						if (entry.allowed === null) {
							return `<td><span class="kv-perm unknown">?</span></td>`;
						}

						const mark = entry.allowed ? "✓" : "✗";
						const cls = entry.allowed ? "yes" : "no";
						const note = entry.caveat ? "<sup>*</sup>" : "";

						return `<td><span class="kv-perm ${cls}">${mark}</span>${note}</td>`;
					})
					.join("");

				return `
					<tr>
						<th scope="row">${frappe.utils.escape_html(row.doctype)}</th>
						${cells}
					</tr>
				`;
			})
			.join("");

		container.html(`
			<div class="kv-access">

				<div class="kv-access-head">
					<strong>${who}</strong>
					<span class="kv-status-pill planning">${role}</span>
				</div>

				<table class="kv-access-table">
					<thead>
						<tr>
							<th scope="col">Doctype</th>
							${header}
						</tr>
					</thead>

					<tbody>
						${rows}
					</tbody>
				</table>

				${
					caveats.length
						? `<p class="kv-access-note">* ${caveats
								.map((c) => frappe.utils.escape_html(c))
								.join(" · ")}</p>`
						: ""
				}

			</div>
		`);
	}

	function loadPreviewOptions() {
		frappe.call({
			method:
				"krushi_vikas.krushi_vikas.page.krushi_dashboard.krushi_dashboard.get_preview_options",
			args: { role: previewRole || undefined },
			freeze: false,
			callback: (response) => {
				const options = response.message;

				if (!options) return;

				const $role = $("#kv-preview-role");

				if ($role.find("option").length <= 1) {
					$role.append(
						options.roles
							.map(
								(role) =>
									`<option value="${frappe.utils.escape_html(
										role.role
									)}">${frappe.utils.escape_html(
										role.role
									)} (${role.user_count})</option>`
							)
							.join("")
					);

					$role.val(previewRole);
				}

				const $user = $("#kv-preview-user");

				$user.html(
					`<option value="">Myself</option>` +
						options.users
							.map(
								(user) =>
									`<option value="${frappe.utils.escape_html(
										user.name
									)}">${frappe.utils.escape_html(
										user.full_name || user.name
									)} — ${frappe.utils.escape_html(
										user.role_label
									)}</option>`
							)
							.join("")
				);

				// The selected person may not hold the newly picked role.
				if (
					previewUser &&
					!options.users.some((user) => user.name === previewUser)
				) {
					previewUser = "";
					loadDashboard();
				}

				$user.val(previewUser);
			}
		});
	}

	function getActivityStatusClass(status) {
		return {
			Draft: "planning",
			Planned: "planning",
			Open: "planning",
			"In Progress": "progress",
			Completed: "completed",
			Cancelled: "cancelled"
		}[status] || "planning";
	}

	function getTaskStatusClass(status) {
		return {
			Open: "planning",
			Working: "progress",
			"Pending Review": "deployed",
			Overdue: "cancelled",
			Completed: "completed",
			Cancelled: "cancelled"
		}[status] || "planning";
	}

	function formatDueDate(value) {
		if (!value) return "No due date";

		return `Due ${frappe.datetime.str_to_user(value)}`;
	}

	function emptyState(container, iconName, message) {
		container.html(`
			<div class="kv-empty-small">
				${icon(iconName)}
				<span>${message}</span>
			</div>
		`);
	}

	function renderMyWork(data) {
		const stats = data.stats || {};

		$("#my-open-activities").text(stats.my_open_activities || 0);
		$("#my-pending-tasks").text(stats.pending_tasks || 0);
		$("#my-overdue-tasks").text(stats.overdue_tasks || 0);

		$("#overdue-pill").toggleClass(
			"is-hidden",
			!(stats.overdue_tasks > 0)
		);

		renderMyActivities(data.my_activities || []);
		renderMyTasks(data.my_tasks || []);
	}

	function renderMyActivities(activities) {
		const container = $("#my-activities");

		if (!activities.length) {
			emptyState(
				container,
				"activity",
				"No activities are assigned to you."
			);

			return;
		}

		container.html(
			activities
				.map((activity) => {
					const name = frappe.utils.escape_html(
						activity.activity_name || activity.name
					);

					const project = frappe.utils.escape_html(
						activity.project || "No project"
					);

					const status = frappe.utils.escape_html(
						activity.status || "Draft"
					);

					const activityId = frappe.utils.escape_html(
						activity.name
					);

					return `
						<button
							class="kv-work-item${activity.is_overdue ? " overdue" : ""}"
							data-activity="${activityId}"
						>
							<span class="kv-work-info">
								<strong>${name}</strong>
								<span>${project} · ${formatDueDate(activity.end_date)}</span>
							</span>

							<span class="kv-status-pill ${getActivityStatusClass(activity.status)}">
								${status}
							</span>
						</button>
					`;
				})
				.join("")
		);
	}

	function renderMyTasks(tasks) {
		const container = $("#my-tasks");

		if (!tasks.length) {
			emptyState(
				container,
				"task",
				"No tasks are assigned to you."
			);

			return;
		}

		container.html(
			tasks
				.map((task) => {
					const subject = frappe.utils.escape_html(
						task.subject || task.name
					);

					const activity = frappe.utils.escape_html(
						task.activity_label || "General task"
					);

					const status = frappe.utils.escape_html(
						task.status || "Open"
					);

					const taskId = frappe.utils.escape_html(task.name);

					return `
						<button
							class="kv-work-item${task.is_overdue ? " overdue" : ""}"
							data-task="${taskId}"
						>
							<span class="kv-work-info">
								<strong>${subject}</strong>
								<span>${activity} · ${formatDueDate(task.exp_end_date)}</span>
							</span>

							<span class="kv-status-pill ${getTaskStatusClass(task.status)}">
								${status}
							</span>
						</button>
					`;
				})
				.join("")
		);
	}

	function renderStats(stats) {
		$("#total-projects").text(stats.total_projects || 0);
		$("#active-projects").text(stats.active_projects || 0);
		$("#planning-projects").text(stats.planning_projects || 0);
		$("#completed-projects").text(stats.completed_projects || 0);
	}

	function renderGantt(projects) {
		const container = $("#project-gantt");

		const yearStart = new Date(selectedYear, 0, 1);
		const yearEnd = new Date(selectedYear, 11, 31);
		const totalDays =
			(new Date(selectedYear + 1, 0, 1) - yearStart) /
			86400000;

		const visibleProjects = projects.filter((project) => {
			const start = parseDate(project.start_date);
			const end = parseDate(project.end_date);

			return (
				start &&
				end &&
				start <= yearEnd &&
				end >= yearStart
			);
		});

		if (!visibleProjects.length) {
			container.html(`
				<div class="kv-empty">
					<div class="kv-empty-icon">
						${icon("calendar")}
					</div>

					<h4>No projects planned for ${selectedYear}</h4>

					<p>
						Create a project with a start and end date
						to add it to the annual plan.
					</p>
				</div>
			`);

			return;
		}

		const months = [
			"Jan", "Feb", "Mar", "Apr",
			"May", "Jun", "Jul", "Aug",
			"Sep", "Oct", "Nov", "Dec"
		];

		const monthGrid = months
			.map(() => `<div class="kv-gantt-grid"></div>`)
			.join("");

		const rows = visibleProjects
			.map((project) => {
				const originalStart = parseDate(project.start_date);
				const originalEnd = parseDate(project.end_date);

				const start =
					originalStart < yearStart
						? yearStart
						: originalStart;

				const end =
					originalEnd > yearEnd
						? yearEnd
						: originalEnd;

				const startDay =
					(start - yearStart) / 86400000;

				const duration =
					((end - start) / 86400000) + 1;

				const left =
					(startDay / totalDays) * 100;

				const width =
					(duration / totalDays) * 100;

				const name = frappe.utils.escape_html(
					project.project_name || project.name
				);

				const assignedTo = frappe.utils.escape_html(
					project.project_coordinator ||
						project.project_manager ||
						"Unassigned"
				);

				const theme = frappe.utils.escape_html(
					project.theme || "No theme"
				);

				const projectId = frappe.utils.escape_html(
					project.name
				);

				return `
					<div class="kv-gantt-row">

						<button
							class="kv-gantt-project"
							data-project="${projectId}"
						>
							<span class="kv-project-dot"></span>

							<span class="kv-gantt-project-info">
								<strong>${name}</strong>
								<span>${theme} · ${assignedTo}</span>
							</span>
						</button>

						<div class="kv-gantt-track">
							${monthGrid}

							<button
								class="kv-project-bar ${getStatusClass(project.status)}"
								style="left:${left}%; width:${width}%"
								data-project="${projectId}"
								title="${name}"
							>
								${name}
							</button>
						</div>

					</div>
				`;
			})
			.join("");

		container.html(`
			<div class="kv-gantt">

				<div class="kv-gantt-header">
					<div class="kv-gantt-project-column">
						Project
					</div>

					<div class="kv-gantt-months">
						${months
							.map(
								(month) =>
									`<div class="kv-gantt-month">${month}</div>`
							)
							.join("")}
					</div>
				</div>

				<div class="kv-gantt-body">
					${rows}
				</div>

			</div>
		`);
	}

	function renderRecentProjects(projects) {
		const container = $("#recent-projects");

		if (!projects.length) {
			container.html(`
				<div class="kv-empty-small">
					${icon("folder")}
					<span>No projects found.</span>
				</div>
			`);

			return;
		}

		const html = projects
			.map((project) => {
				const name = frappe.utils.escape_html(
					project.project_name || project.name
				);

				const manager = frappe.utils.escape_html(
					project.project_manager || "No manager assigned"
				);

				const status = frappe.utils.escape_html(
					project.status || "Planning"
				);

				const projectId = frappe.utils.escape_html(
					project.name
				);

				return `
					<button
						class="kv-project-item"
						data-project="${projectId}"
					>
						<span class="kv-project-item-icon">
							${icon("plant")}
						</span>

						<span class="kv-project-info">
							<strong>${name}</strong>
							<span>${manager}</span>
						</span>

						<span class="kv-status-pill ${getStatusClass(project.status)}">
							${status}
						</span>

						${icon("right")}
					</button>
				`;
			})
			.join("");

		container.html(html);
	}

	function renderStatus(stats) {
		const total = stats.total_projects || 0;

		const statuses = [
			{
				label: "Planning",
				value: stats.planning_projects || 0,
				className: "planning"
			},
			{
				label: "In Progress",
				value: stats.active_projects || 0,
				className: "progress"
			},
			{
				label: "Completed",
				value: stats.completed_projects || 0,
				className: "completed"
			},
			{
				label: "Cancelled",
				value: stats.cancelled_projects || 0,
				className: "cancelled"
			}
		];

		$("#project-status").html(
			statuses
				.map((item) => {
					const percentage = total
						? Math.round((item.value / total) * 100)
						: 0;

					return `
						<div class="kv-status-row">

							<div class="kv-status-label">
								<span class="kv-status-dot ${item.className}"></span>
								<span>${item.label}</span>
							</div>

							<div class="kv-status-value">
								<strong>${item.value}</strong>
								<span>${percentage}%</span>
							</div>

						</div>
					`;
				})
				.join("")
		);
	}

	function render(data) {
		setUser(data);
		renderPreview(data);
		renderStats(data.stats || {});
		renderMyWork(data);
		renderGantt(data.projects || []);
		renderRecentProjects(data.recent_projects || []);
		renderStatus(data.stats || {});
	}

	function loadDashboard() {
		if (loading) return;

		loading = true;

		$("#welcome-year").text(selectedYear);

		$("#project-gantt").html(`
			<div class="kv-loading">
				Loading ${selectedYear} project plan...
			</div>
		`);

		frappe.call({
			method:
				"krushi_vikas.krushi_vikas.page.krushi_dashboard.krushi_dashboard.get_dashboard_data",
			args: {
				year: selectedYear,
				preview_user: previewUser || undefined
			},
			freeze: false,
			callback: (response) => {
				loading = false;

				if (!response.message) {
					frappe.msgprint({
						title: "Dashboard Error",
						message: "Unable to load dashboard data.",
						indicator: "red"
					});

					return;
				}

				render(response.message);
			},
			error: () => {
				loading = false;

				frappe.msgprint({
					title: "Dashboard Error",
					message: "Unable to load Krushi Vikas dashboard.",
					indicator: "red"
				});
			}
		});
	}

	function refreshDashboard() {
		loadDashboard();
	}

	$main.on("click", ".kv-nav-item", function () {
		const route = $(this).data("route");

		if (route === "dashboard") {
			$(".kv-nav-item").removeClass("active");
			$(this).addClass("active");
			refreshDashboard();
			return;
		}

		if (routes[route]) {
			routes[route]();
		}
	});

	$main.on("click", "#create-project", function () {
		if (!frappe.model.can_create("KV Project")) {
			frappe.msgprint({
				title: "Permission Denied",
				message: "You do not have permission to create a project.",
				indicator: "red"
			});

			return;
		}

		frappe.new_doc("KV Project");
	});

	$main.on("click", "#previous-year", function () {
		selectedYear -= 1;
		loadDashboard();
	});

	$main.on("click", "#next-year", function () {
		selectedYear += 1;
		loadDashboard();
	});

	$main.on("click", ".kv-clickable", function () {
		const route = $(this).data("route");

		if (routes[route]) {
			routes[route]();
		}
	});

	$main.on("click", "[data-project]", function () {
		const project = $(this).data("project");

		if (!project || !frappe.model.can_read("KV Project")) {
			return;
		}

		frappe.set_route("Form", "KV Project", project);
	});

	$main.on("change", "#kv-preview-role", function () {
		previewRole = $(this).val() || "";
		loadPreviewOptions();
	});

	$main.on("change", "#kv-preview-user", function () {
		previewUser = $(this).val() || "";
		loadDashboard();
	});

	$main.on("click", "#kv-preview-reset", function () {
		previewUser = "";
		previewRole = "";
		$("#kv-preview-role").val("");
		$("#kv-preview-user").val("");
		loadPreviewOptions();
		loadDashboard();
	});

	$main.on("click", "[data-activity]", function () {
		const activity = $(this).data("activity");

		if (!activity || !frappe.model.can_read("Activity")) {
			return;
		}

		frappe.set_route("Form", "Activity", activity);
	});

	$main.on("click", "[data-task]", function () {
		const task = $(this).data("task");

		if (!task || !frappe.model.can_read("Task")) {
			return;
		}

		frappe.set_route("Form", "Task", task);
	});

	$main.on("click", "#view-all-projects", function () {
		if (frappe.model.can_read("KV Project")) {
			routes.projects();
		}
	});

	frappe.pages["krushi-dashboard"]._refresh = refreshDashboard;

	applyPermissions();
	loadDashboard();
};

frappe.pages["krushi-dashboard"].on_page_show = function (wrapper) {
	const page = frappe.pages["krushi-dashboard"];

	if (page && page._refresh) {
		page._refresh();
	}
};