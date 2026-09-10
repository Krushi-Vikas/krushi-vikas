import frappe
from frappe.model.document import Document

# Step 02 of the journey. An appraisal only exists against a concept note
# that leadership has already accepted.
ALLOWED_CONCEPT_STATUS = ("Approved",)


class RRAReport(Document):
	def validate(self):
		self.validate_concept_note()

	def validate_concept_note(self):
		if not self.concept_note:
			return

		status, docstatus = frappe.db.get_value(
			"Concept Note", self.concept_note, ["status", "docstatus"]
		)

		if docstatus != 1:
			frappe.throw(
				frappe._("Concept Note {0} has not been submitted yet.").format(
					self.concept_note
				)
			)

		if status not in ALLOWED_CONCEPT_STATUS:
			frappe.throw(
				frappe._(
					"Concept Note {0} is {1}. An RRA Report can only be raised "
					"against an approved concept note."
				).format(self.concept_note, status or "Draft")
			)

	def on_submit(self):
		self.sync_project_journey()

	def on_cancel(self):
		self.sync_project_journey()

	def sync_project_journey(self):
		"""Nothing downstream exists yet at this stage; kept so the hook
		point is uniform across the pipeline documents."""
		return
