import frappe
from frappe.model.document import Document

class ConceptNote(Document):
	def on_submit(self):
		if self.status == "Approved" and not self.project:
			company = frappe.db.get_value("Company", {"is_group": 0}, "name")
			proj = frappe.new_doc("Project")
			proj.project_name = self.title
			proj.company = company
			proj.estimated_cost = self.estimated_budget
			proj.custom_thematic_area = self.thematic_area
			proj.custom_concept_note = self.name
			proj.custom_project_phase = "Proposal"
			proj.insert(ignore_permissions=True)
			self.db_set("project", proj.name)
