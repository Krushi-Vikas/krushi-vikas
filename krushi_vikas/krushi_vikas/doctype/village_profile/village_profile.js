// Copyright (c) 2026, Krushi Vikas and contributors
// For license information, please see license.txt

frappe.ui.form.on('Village Profile', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('View Projects'), function() {
                frappe.set_route('List', 'Project', {'custom_village': frm.doc.village_name});
            }, __('Navigate'));

            frm.add_custom_button(__('View Feedback Surveys'), function() {
                frappe.set_route('List', 'Feedback Survey', {'village': frm.doc.village_name});
            }, __('Navigate'));
        }

        // Add summary indicators
        if (frm.doc.summer_water_scarcity_status === 'Severe / Tanker Dependent') {
            frm.dashboard.set_headline_alert(
                __('High Priority Village: Severe summer water scarcity reported. Needs urgent watershed intervention.'),
                'orange'
            );
        }
    },

    total_geographical_area_ha: function(frm) {
        frm.trigger('calculate_land_balance');
    },

    cultivable_land_ha: function(frm) {
        frm.trigger('calculate_land_balance');
    },

    irrigated_area_ha: function(frm) {
        frm.trigger('calculate_land_balance');
    },

    calculate_land_balance: function(frm) {
        let total = frm.doc.total_geographical_area_ha || 0;
        let cult = frm.doc.cultivable_land_ha || 0;
        let irri = frm.doc.irrigated_area_ha || 0;

        if (cult > 0 && irri >= 0 && !frm.doc.rainfed_area_ha) {
            let rainfed = Math.max(0, cult - irri);
            frm.set_value('rainfed_area_ha', Math.round(rainfed * 100) / 100);
        }

        if (total > 0 && cult > 0 && !frm.doc.forest_wasteland_ha) {
            let waste = Math.max(0, total - cult);
            frm.set_value('forest_wasteland_ha', Math.round(waste * 100) / 100);
        }
    },

    validate: function(frm) {
        if (frm.doc.date_of_survey && frappe.datetime.get_diff(frm.doc.date_of_survey, frappe.datetime.get_today()) > 0) {
            frappe.msgprint(__('Date of Survey cannot be in the future.'));
            frappe.validated = false;
        }
    }
});
