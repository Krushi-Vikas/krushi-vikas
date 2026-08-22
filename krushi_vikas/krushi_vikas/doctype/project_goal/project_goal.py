import frappe
from frappe.model.document import Document

class ProjectGoal(Document):
	def validate(self):
		total_weight = sum([float(d.weightage or 0) for d in self.objectives])
		if self.objectives and abs(total_weight - 100.0) > 0.01:
			frappe.throw(f"Total objective weightage must equal 100%. Current total: {total_weight}%")
		
		weighted_ach = 0.0
		for obj in self.objectives:
			if obj.kre:
				ach = frappe.db.get_value("KRE", obj.kre, "achievement_pct") or 0.0
				obj.achievement_pct = ach
				weighted_ach += (ach * float(obj.weightage or 0) / 100.0)
		self.actual_completion_pct = weighted_ach
