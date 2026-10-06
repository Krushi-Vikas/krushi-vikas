// Copyright (c) 2026, Krushi Vikas and contributors
// For license information, please see license.txt

// The printed form has a fixed set of rows per table. Prefilling them keeps the
// digital form in the same order as the paper one the enumerator carries.
const STANDARD_ROWS = {
    caste_demographics_table: {
        field: 'caste_category',
        values: ['SC', 'ST', 'VIMUKT BHATKYA JATI/JAMATI (VJNT)', 'OBC', 'GENERAL', 'TOTAL']
    },
    land_use_table: {
        field: 'land_type',
        values: [
            'Total area of village', 'Usable land', 'Land under ploughing',
            'Bagayati area (Irrigated)', 'Jirayat area (Rainfed)', 'Private padik land',
            'Govt. padik land', 'Area under forest', 'Gairan area / Grazing land',
            'Area under Gavthan, river, dam etc.', 'Other'
        ]
    },
    cropping_pattern_table: {
        field: 'season',
        values: ['Rainy season (Kharif)', 'Cold season (Rabi)', 'Summer', 'Annual crops']
    },
    water_sources_table: {
        field: 'water_supply_type',
        values: ['Hand Pump', 'Well', 'Private Tap', 'Public Tap', 'Other']
    },
    health_facilities_table: {
        field: 'facility',
        values: ['PHC (Primary Health Centre)', 'Sub Centre', 'Private Hospital', 'Animal Dispensary', 'Other']
    },
    education_facilities_table: {
        field: 'school_type',
        values: ['Anganwadi', 'Primary School', 'Secondary School', 'Junior College', 'Other']
    },
    public_institutions_table: {
        field: 'facility',
        values: [
            'Grampanchayat', 'Gym', 'Hostels', 'Library', 'Bus Stand', 'Market',
            'Community Hall', 'Milk Dairy', 'Storage House', 'Crematorium',
            'Post Office', 'Ground', 'Other'
        ]
    },
    livestock_table: {
        field: 'animal_type',
        values: ['Bull', 'Cow', 'Buffalo', 'Reda', 'Goat', 'Sheep', 'Hen', 'Other']
    }
};

function prefill_standard_rows(frm) {
    let added = 0;
    Object.keys(STANDARD_ROWS).forEach(function (table) {
        const spec = STANDARD_ROWS[table];
        const existing = (frm.doc[table] || []).map((r) => r[spec.field]);
        spec.values.forEach(function (value) {
            if (existing.indexOf(value) === -1) {
                const row = frm.add_child(table);
                row[spec.field] = value;
                added++;
            }
        });
        frm.refresh_field(table);
    });
    frappe.show_alert({
        message: __('Added {0} standard row(s) from the printed form.', [added]),
        indicator: 'green'
    });
}

frappe.ui.form.on('Village Profile', {
    refresh: function (frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Prefill Form Rows'), function () {
                prefill_standard_rows(frm);
            });
        }

        if (!frm.doc.__islocal && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('View Projects'), function () {
                frappe.set_route('List', 'Project', { custom_village: frm.doc.village_name });
            }, __('Navigate'));

            frm.add_custom_button(__('View Feedback Surveys'), function () {
                frappe.set_route('List', 'Feedback Survey', { village: frm.doc.village_name });
            }, __('Navigate'));

            frm.dashboard.set_headline_alert(
                __('This profile is submitted and locked. It is the baseline reference for impact comparison.'),
                'blue'
            );
        }
    },

    male_population: function (frm) {
        frm.trigger('check_population_split');
    },

    female_population: function (frm) {
        frm.trigger('check_population_split');
    },

    check_population_split: function (frm) {
        const male = frm.doc.male_population || 0;
        const female = frm.doc.female_population || 0;
        if (male && female && !frm.doc.total_population) {
            frm.set_value('total_population', male + female);
        }
    },

    validate: function (frm) {
        if (frm.doc.date_of_survey &&
            frappe.datetime.get_diff(frm.doc.date_of_survey, frappe.datetime.get_today()) > 0) {
            frappe.msgprint(__('Date of Survey cannot be in the future.'));
            frappe.validated = false;
        }
    }
});
