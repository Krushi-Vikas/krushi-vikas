# -*- coding: utf-8 -*-
# Copyright (c) 2026, Krushi Vikas and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

TOTAL_VILLAGE_AREA_ROW = "Total area of village"


class VillageProfile(Document):
    def validate(self):
        self.stamp_field_officer()
        self.validate_dates()
        self.validate_demographics()
        self.validate_caste_breakdown()
        self.validate_household_counts()
        self.validate_land_use()

    def stamp_field_officer(self):
        # Step 05 is collected in the field, so the collector is taken from the
        # session rather than typed in.
        if not self.field_officer:
            self.field_officer = frappe.session.user

    def validate_dates(self):
        if self.date_of_survey and getdate(self.date_of_survey) > getdate(today()):
            frappe.throw(_("Date of Survey cannot be in the future."))

    def validate_demographics(self):
        if (self.total_population or 0) < 0:
            frappe.throw(_("Total Population cannot be negative."))

        if (self.total_households or 0) < 0:
            frappe.throw(_("Village Families (Total Households) cannot be negative."))

        male = self.male_population or 0
        female = self.female_population or 0
        total = self.total_population or 0

        if male and female and total and (male + female) > total:
            frappe.throw(
                _("Sum of Men ({0}) and Women ({1}) exceeds Total Population ({2}).").format(
                    male, female, total
                )
            )

    def validate_caste_breakdown(self):
        """The paper form carries its own TOTAL row, so it is checked against
        the village totals rather than silently disagreeing with them."""
        rows = [r for r in (self.caste_demographics_table or []) if r.caste_category != "TOTAL"]
        if not rows:
            return

        caste_population = sum(r.population or 0 for r in rows)
        caste_families = sum(r.total_families or 0 for r in rows)

        if self.total_population and caste_population > self.total_population:
            frappe.msgprint(
                _("Caste-wise population ({0}) exceeds Total Population ({1}). Please re-check section 3.").format(
                    caste_population, self.total_population
                ),
                indicator="orange",
                alert=True,
            )

        if self.total_households and caste_families > self.total_households:
            frappe.msgprint(
                _("Caste-wise families ({0}) exceeds Village Families ({1}). Please re-check section 3.").format(
                    caste_families, self.total_households
                ),
                indicator="orange",
                alert=True,
            )

    def validate_household_counts(self):
        """Counts that are expressed as 'number of families' cannot exceed the
        number of families in the village."""
        if not self.total_households:
            return

        family_fields = (
            "families_with_toilets",
            "families_without_toilets",
            "families_toilet_not_using",
            "families_constructing_toilets",
            "families_on_public_drainage",
            "families_having_shoshkhadda",
            "families_having_kitchen_garden",
            "families_no_pds_connection",
            "families_worm_compost_unit",
            "families_throwing_waste_open",
            "families_using_dustbin",
            "families_using_firewood",
            "families_using_gas",
            "families_using_kerosene",
            "families_using_biogas",
            "families_using_smokeless_hearth",
            "families_having_shet_tali",
            "families_having_wells",
            "families_having_borewells",
            "families_having_animals",
            "families_having_job_cards",
            "migrated_families_for_job",
            "families_with_govt_servant",
            "families_with_private_servant",
            "organic_farming_families",
        )

        for fieldname in family_fields:
            value = self.get(fieldname) or 0
            if value > self.total_households:
                label = self.meta.get_label(fieldname)
                frappe.throw(
                    _("{0} ({1}) cannot exceed Village Families ({2}).").format(
                        label, value, self.total_households
                    )
                )

    def validate_land_use(self):
        """Row 1 of the land table is the village total; the remaining rows are
        subdivisions of it."""
        rows = self.land_use_table or []
        if not rows:
            return

        total_row = next((r for r in rows if r.land_type == TOTAL_VILLAGE_AREA_ROW), None)
        if not total_row or not total_row.area:
            return

        subdivisions = sum(r.area or 0 for r in rows if r is not total_row)
        if subdivisions > (total_row.area + 0.01):
            frappe.msgprint(
                _("Land subdivisions ({0}) exceed Total area of village ({1}). Please re-check section 4.").format(
                    subdivisions, total_row.area
                ),
                indicator="orange",
                alert=True,
            )

    def before_submit(self):
        # Submitting locks the record. Step 06 reads it as the 'before' picture,
        # so the ingesting user is recorded at the point it becomes immutable.
        if self.profile_status == "Draft":
            self.profile_status = "Submitted"
        self.approved_by = frappe.session.user
