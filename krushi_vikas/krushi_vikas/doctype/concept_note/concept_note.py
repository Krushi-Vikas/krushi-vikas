import frappe
from frappe.model.document import Document


class ConceptNote(Document):
	"""Step 01 of the operational roadmap.

	This used to create an ERPNext Project directly on submit, which jumped
	straight from the idea to a live project and skipped the appraisal (02),
	the proposal (03), external approval (04) and the baseline survey (05).
	It also wrote to `custom_concept_note`, a field that does not exist on
	Project, so the trail back to the note was silently lost.

	An approved note now opens an RRA Report instead, via
	krushi_vikas.api.create_rra_from_concept_note. The project is created at
	step 06 from the approved proposal, which carries the agreed budget and
	dates forward.
	"""

	def on_submit(self):
		if self.status != "Approved":
			return

		if frappe.db.exists("RRA Report", {"concept_note": self.name, "docstatus": ["<", 2]}):
			return

		frappe.msgprint(
			frappe._(
				"Concept note approved. Next step: raise an RRA Report (step 02) "
				"from the Create menu."
			),
			indicator="green",
			alert=True,
		)
