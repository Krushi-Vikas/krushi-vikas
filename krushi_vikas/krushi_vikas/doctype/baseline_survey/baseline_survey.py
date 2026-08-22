# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint

class BaselineSurvey(Document):
	def validate(self):
		self.calculate_family_members()
		self.calculate_crop_financials()
		self.calculate_livestock_totals()
		self.calculate_income_expenditure()
		self.validate_landholdings()

	def calculate_family_members(self):
		if self.get("household_members_table"):
			self.household_members = len(self.household_members_table)

	def calculate_crop_financials(self):
		if self.get("crops_table"):
			for row in self.crops_table:
				if (not flt(row.total_income) or flt(row.total_income) == 0) and flt(row.yield_quintals) > 0 and flt(row.market_rate_per_qtl) > 0:
					row.total_income = flt(row.yield_quintals) * flt(row.market_rate_per_qtl)
				row.net_profit = flt(row.total_income) - flt(row.cost_of_production)

	def calculate_livestock_totals(self):
		if self.get("livestock_table"):
			total_animals = sum(cint(row.count) for row in self.livestock_table if row.count)
			self.livestock_count = total_animals
			self.owns_livestock = "Yes" if total_animals > 0 else "No"

	def calculate_income_expenditure(self):
		if self.get("family_income_table"):
			for row in self.family_income_table:
				if flt(row.monthly_amount) > 0 and not flt(row.annual_amount):
					row.annual_amount = flt(row.monthly_amount) * 12.0
				elif flt(row.annual_amount) > 0 and not flt(row.monthly_amount):
					row.monthly_amount = flt(row.annual_amount) / 12.0

		if self.get("family_expenditure_table"):
			for row in self.family_expenditure_table:
				if flt(row.monthly_amount) > 0 and not flt(row.annual_amount):
					row.annual_amount = flt(row.monthly_amount) * 12.0
				elif flt(row.annual_amount) > 0 and not flt(row.monthly_amount):
					row.monthly_amount = flt(row.annual_amount) / 12.0

	def validate_landholdings(self):
		total = flt(self.total_landholding_acres)
		irrigated = flt(self.irrigated_land_acres)
		rainfed = flt(self.rainfed_land_acres)
		if (irrigated + rainfed) > 0 and total == 0:
			self.total_landholding_acres = irrigated + rainfed

	def on_submit(self):
		self.submission_status = "Submitted"
		self.db_set("submission_status", "Submitted")

	def on_cancel(self):
		self.submission_status = "Draft"
		self.db_set("submission_status", "Draft")
