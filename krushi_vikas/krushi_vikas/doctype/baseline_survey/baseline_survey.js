// Copyright (c) 2026, Krushi Vikas and contributors
// For license information, please see license.txt

frappe.ui.form.on("Baseline Survey", {
	setup: function(frm) {
		frm.set_query("village_profile", () => ({ filters: { docstatus: 1 } }));
	},

	village_profile: function(frm) {
		if (!frm.doc.village_profile) return;
		frappe.db.get_value("Village Profile", frm.doc.village_profile, "village_name").then((result) => {
			frm.set_value("village", result.message.village_name);
		});
	},

	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Export to Excel / CSV"), function() {
				window.open(`/api/method/krushi_vikas.api.export_baseline_survey_excel?name=${frm.doc.name}`, "_blank");
			}, __("Actions"));
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("View Farmer Web Summary"), function() {
				window.open(`/baseline_survey?view=${frm.doc.name}`, "_blank");
			}, __("Actions"));
		}
	},

	household_members_table_add: function(frm) {
		frm.set_value("household_members", (frm.doc.household_members_table || []).length);
	},
	household_members_table_remove: function(frm) {
		frm.set_value("household_members", (frm.doc.household_members_table || []).length);
	},

	irrigated_land_acres: function(frm) {
		calculate_total_land(frm);
	},
	rainfed_land_acres: function(frm) {
		calculate_total_land(frm);
	}
});

function calculate_total_land(frm) {
	let irrigated = flt(frm.doc.irrigated_land_acres);
	let rainfed = flt(frm.doc.rainfed_land_acres);
	if (!frm.doc.total_landholding_acres || flt(frm.doc.total_landholding_acres) === 0) {
		frm.set_value("total_landholding_acres", irrigated + rainfed);
	}
}

frappe.ui.form.on("Baseline Crop Detail", {
	yield_quintals: function(frm, cdt, cdn) {
		calculate_crop_row(frm, cdt, cdn);
	},
	market_rate_per_qtl: function(frm, cdt, cdn) {
		calculate_crop_row(frm, cdt, cdn);
	},
	total_income: function(frm, cdt, cdn) {
		calculate_crop_row(frm, cdt, cdn);
	},
	cost_of_production: function(frm, cdt, cdn) {
		calculate_crop_row(frm, cdt, cdn);
	}
});

function calculate_crop_row(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let yield_qtl = flt(row.yield_quintals);
	let rate = flt(row.market_rate_per_qtl);
	let cost = flt(row.cost_of_production);

	if ((!row.total_income || flt(row.total_income) === 0) && yield_qtl > 0 && rate > 0) {
		frappe.model.set_value(cdt, cdn, "total_income", yield_qtl * rate);
	}
	let total_inc = flt(row.total_income);
	frappe.model.set_value(cdt, cdn, "net_profit", total_inc - cost);
}

frappe.ui.form.on("Baseline Livestock Detail", {
	count: function(frm) {
		let total = 0;
		(frm.doc.livestock_table || []).forEach(r => {
			total += cint(r.count);
		});
		frm.set_value("livestock_count", total);
		frm.set_value("owns_livestock", total > 0 ? "Yes" : "No");
	},
	livestock_table_remove: function(frm) {
		let total = 0;
		(frm.doc.livestock_table || []).forEach(r => {
			total += cint(r.count);
		});
		frm.set_value("livestock_count", total);
		frm.set_value("owns_livestock", total > 0 ? "Yes" : "No");
	}
});

frappe.ui.form.on("Baseline Monthly Annual Income", {
	monthly_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (flt(row.monthly_amount) > 0) {
			frappe.model.set_value(cdt, cdn, "annual_amount", flt(row.monthly_amount) * 12.0);
		}
	},
	annual_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (flt(row.annual_amount) > 0 && !flt(row.monthly_amount)) {
			frappe.model.set_value(cdt, cdn, "monthly_amount", flt(row.annual_amount) / 12.0);
		}
	}
});

frappe.ui.form.on("Baseline Monthly Annual Expenditure", {
	monthly_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (flt(row.monthly_amount) > 0) {
			frappe.model.set_value(cdt, cdn, "annual_amount", flt(row.monthly_amount) * 12.0);
		}
	},
	annual_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (flt(row.annual_amount) > 0 && !flt(row.monthly_amount)) {
			frappe.model.set_value(cdt, cdn, "monthly_amount", flt(row.annual_amount) / 12.0);
		}
	}
});
