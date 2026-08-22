import frappe
from frappe.model.document import Document

class KRE(Document):
	def validate(self):
		if self.target_value is not None and self.baseline_value is not None:
			span = (self.target_value or 0) - (self.baseline_value or 0)
			done = (self.current_value or 0) - (self.baseline_value or 0)
			self.achievement_pct = (done / span * 100) if span > 0 else (100 if done >= 0 else 0)
			if self.achievement_pct >= 100:
				self.status = "Completed"
			elif self.achievement_pct >= 70:
				self.status = "On Track"
			elif self.achievement_pct >= 40:
				self.status = "At Risk"
			elif self.achievement_pct > 0:
				self.status = "Critical"
