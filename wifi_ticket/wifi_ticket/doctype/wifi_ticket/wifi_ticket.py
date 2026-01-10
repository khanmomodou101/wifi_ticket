# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WifiTicket(Document):
	def validate(self):
		if self.plan:
		    self.amount = frappe.db.get_value("Wifi Plan", self.plan, "price")
