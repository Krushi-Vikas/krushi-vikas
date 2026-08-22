import frappe
from frappe.model.document import Document
from frappe.utils import flt

class KVProject(Document):
    def validate(self):
        if self.start_date and self.end_date and str(self.end_date) < str(self.start_date):
            frappe.throw("End Date cannot be before Start Date for KV Project.")
            
        # Calculate remaining funds
        b = flt(self.budget)
        spent = flt(self.actual_amount_spent)
        self.remaining_funds = b - spent
        
        # Validate activity dates
        for act in self.get("activities") or []:
            if act.start_date and act.end_date and str(act.end_date) < str(act.start_date):
                frappe.throw(f"Activity '{act.activity_name}': End Date cannot be before Start Date.")
