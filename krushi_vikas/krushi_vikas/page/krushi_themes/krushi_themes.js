frappe.pages["krushi-themes"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: "", single_column: true });

	const $main = $(wrapper).find(".layout-main-section");
	let requestId = 0;
	let searchTimer = null;

	const svg = {
		sprout: `<path d="M12 21V8"/><path d="M12 12C8 12 5 9.8 5 6c4.3 0 7 2.2 7 6Z"/><path d="M12 10c0-3.5 2.4-6 6.5-6 0 3.8-2.5 6-6.5 6Z"/><path d="M8 21h8"/>`,
		sproutPlus: `<path d="M11 21V8"/><path d="M11 12C7 12 4 9.8 4 6c4.3 0 7 2.2 7 6Z"/><path d="M7 21h6"/><path d="M18 8v6"/><path d="M15 11h6"/>`,
		search: `<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>`,
		back: `<path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-4"/>`,
		grid: `<rect x="3" y="3" width="7" height="7" rx="1.4"/><rect x="14" y="3" width="7" height="7" rx="1.4"/><rect x="3" y="14" width="7" height="7" rx="1.4"/><rect x="14" y="14" width="7" height="7" rx="1.4"/>`
	};

	const icon = (n) =>
		`<span class="kv-icon"><svg viewBox="0 0 24 24" aria-hidden="true">${svg[n] || svg.grid}</svg></span>`;
	const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));

	$main.html(`
		<div class="kvp kvt">
			<header class="kvp-head">
				<div>
					<h1>Themes &amp; Sub-Themes</h1>
					<p>The catalog every project selects from — one project usually spans several.</p>
				</div>
				<div class="kvp-actions">
					<button class="kvp-btn" id="kvt-dash">${icon("back")}<span>Dashboard</span></button>
					<button class="kvp-btn primary is-hidden" id="kvt-new">${icon("sproutPlus")}<span>New Theme</span></button>
				</div>
			</header>

			<div class="kvp-toolbar">
				<div class="kvp-search">
					${icon("search")}
					<input type="text" class="kvp-input" id="kvt-q" placeholder="Search themes…" autocomplete="off">
				</div>
				<span class="kvp-count" id="kvt-count"></span>
			</div>

			<div id="kvt-body">
				<div class="kvp-grid">
					${Array.from({ length: 4 }, () => `<div class="kvp-skel"></div>`).join("")}
				</div>
			</div>
		</div>
	`);

	function themeCard(t) {
		const subs = t.sub_themes || [];
		return `
			<div class="kvp-card kvt-card">
				<div class="kvp-card-top">
					<div class="kvp-card-title">
						<strong>${esc(t.theme_name)}</strong>
						<span>${t.usage} ${t.usage === 1 ? "activity" : "activities"} tagged directly</span>
					</div>
				</div>

				${t.description ? `<p class="kvt-desc">${esc(t.description)}</p>` : ""}

				<div class="kvt-subrow">
					${
						subs.length
							? subs
									.map(
										(s) =>
											`<span class="kvp-theme-chip" data-subtheme="${esc(s.name)}">${esc(
												s.theme_name
											)}${s.usage ? ` · ${s.usage}` : ""}</span>`
									)
									.join("")
							: `<span class="kvp-theme-chip is-empty">No sub-themes yet</span>`
					}
				</div>
			</div>`;
	}

	function render(data) {
		$("#kvt-new").toggleClass("is-hidden", !data.can_create);

		const themes = data.themes || [];
		$("#kvt-count").text(themes.length === 1 ? "1 theme" : `${themes.length} themes`);

		if (!themes.length) {
			$("#kvt-body").html(`
				<div class="kvp-empty">
					${icon("sprout")}
					<h4>No themes yet</h4>
					<p>${
						data.can_create
							? "Create the first Theme — Project Managers and Coordinators will pick from it, never create their own."
							: "Ask a Director or Administrator to set up the theme catalog."
					}</p>
				</div>`);
			return;
		}

		$("#kvt-body").html(`<div class="kvp-grid">${themes.map(themeCard).join("")}</div>`);
	}

	function load() {
		const ticket = ++requestId;
		const search = $("#kvt-q").val();

		frappe.call({
			method: "krushi_vikas.krushi_vikas.page.krushi_themes.krushi_themes.get_theme_cards",
			args: { search: search || undefined },
			freeze: false,
			callback: (r) => {
				if (ticket !== requestId) return;
				if (r.message) render(r.message);
			}
		});
	}

	$main.on("input", "#kvt-q", function () {
		clearTimeout(searchTimer);
		searchTimer = setTimeout(load, 260);
	});

	$main.on("click", "#kvt-dash", () => frappe.set_route("krushi-dashboard"));
	$main.on("click", "#kvt-new", () => frappe.new_doc("Project Theme", { is_group: 1 }));

	$main.on("click", ".kvt-card > .kvp-card-top", function () {
		// no-op target reserved for future drill-down; cards are read-mostly
	});

	$main.on("click", "[data-subtheme]", function (event) {
		event.stopPropagation();
		if (frappe.model.can_read("Project Theme")) {
			frappe.set_route("Form", "Project Theme", $(this).data("subtheme"));
		}
	});

	frappe.pages["krushi-themes"]._refresh = load;
	load();
};

frappe.pages["krushi-themes"].on_page_show = function () {
	const page = frappe.pages["krushi-themes"];
	if (page && page._refresh) page._refresh();
};
