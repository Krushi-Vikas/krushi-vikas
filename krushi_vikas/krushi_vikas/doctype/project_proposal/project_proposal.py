import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt

# Step 03. A proposal may only be drafted where the appraisal said to proceed.
ALLOWED_RRA_RECOMMENDATIONS = ("Proceed", "Proceed with Changes")


class ProjectProposal(Document):
	def validate(self):
		self.validate_rra_report()
		self.validate_dates()
		self.compute_budget()

	def validate_rra_report(self):
		if not self.rra_report:
			return

		recommendation, docstatus = frappe.db.get_value(
			"RRA Report", self.rra_report, ["recommendation", "docstatus"]
		)

		if docstatus != 1:
			frappe.throw(
				frappe._("RRA Report {0} has not been submitted yet.").format(
					self.rra_report
				)
			)

		if recommendation not in ALLOWED_RRA_RECOMMENDATIONS:
			frappe.throw(
				frappe._(
					"RRA Report {0} recommends '{1}'. A proposal can only be "
					"raised where the appraisal recommends proceeding."
				).format(self.rra_report, recommendation or "no decision")
			)

	def validate_dates(self):
		if not (self.planned_start_date and self.planned_end_date):
			return

		if date_diff(self.planned_end_date, self.planned_start_date) < 0:
			frappe.throw(frappe._("Planned end date cannot precede the start date."))

		self.duration_months = max(
			1,
			round(date_diff(self.planned_end_date, self.planned_start_date) / 30.0),
		)

	def compute_budget(self):
		"""Budget lines are the source of truth when present; a proposal
		without them may still carry a single headline figure."""
		if not self.budget_lines:
			return

		total = 0.0

		for line in self.budget_lines:
			line.amount = flt(line.unit_count) * flt(line.rate)
			total += line.amount

		self.total_budget = total

	def on_submit(self):
		frappe.db.set_value("RRA Report", self.rra_report, "proposal", self.name)

	def on_cancel(self):
		if self.kv_project:
			frappe.throw(
				frappe._(
					"Cancel or delete project {0} before cancelling this proposal."
				).format(self.kv_project)
			)

		frappe.db.set_value("RRA Report", self.rra_report, "proposal", None)
