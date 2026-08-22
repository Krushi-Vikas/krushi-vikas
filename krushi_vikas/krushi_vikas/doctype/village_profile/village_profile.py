# -*- coding: utf-8 -*-
# Copyright (c) 2026, Krushi Vikas and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

class VillageProfile(Document):
    def validate(self):
        self.validate_dates()
        self.validate_demographics()
        self.validate_landholding()

    def validate_dates(self):
        if self.date_of_survey and getdate(self.date_of_survey) > getdate(today()):
            frappe.throw(_("Date of Survey cannot be in the future."))

    def validate_demographics(self):
        if self.total_population and self.total_population < 0:
            frappe.throw(_("Total Population cannot be negative."))

        if self.total_households and self.total_households < 0:
            frappe.throw(_("Total Households cannot be negative."))

        male = self.male_population or 0
        female = self.female_population or 0
        total = self.total_population or 0

        if male > 0 and female > 0 and total > 0:
            if (male + female) > total:
                frappe.throw(
                    _("Sum of Male ({0}) and Female ({1}) population exceeds Total Population ({2}).").format(
                        male, female, total
                    )
                )

        if self.literacy_rate_pct is not None:
            if self.literacy_rate_pct < 0 or self.literacy_rate_pct > 100:
                frappe.throw(_("Literacy Rate must be between 0% and 100%."))

    def validate_landholding(self):
        total_geo = self.total_geographical_area_ha or 0.0
        cultivable = self.cultivable_land_ha or 0.0
        irrigated = self.irrigated_area_ha or 0.0
        rainfed = self.rainfed_area_ha or 0.0

        if total_geo < 0 or cultivable < 0 or irrigated < 0 or rainfed < 0:
            frappe.throw(_("Landholding areas cannot be negative numbers."))

        if total_geo > 0 and cultivable > 0:
            if cultivable > total_geo:
                frappe.throw(
                    _("Cultivable Land ({0} Ha) cannot exceed Total Geographical Area ({1} Ha).").format(
                        cultivable, total_geo
                    )
                )

        if cultivable > 0 and (irrigated > 0 or rainfed > 0):
            if (irrigated + rainfed) > (cultivable + 0.01):
                frappe.throw(
                    _("Sum of Irrigated ({0} Ha) and Rainfed ({1} Ha) area exceeds Total Cultivable Land ({2} Ha).").format(
                        irrigated, rainfed, cultivable
                    )
                )

    def before_submit(self):
        if self.profile_status == "Draft":
            self.profile_status = "Verified"
