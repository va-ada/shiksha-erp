# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
import frappe
from frappe import _
from frappe.model.document import Document


class CourseOutcome(Document):
	def validate(self):
		seen = set()
		for row in self.po_mapping:
			if row.program_outcome in seen:
				frappe.throw(_("Program Outcome {0} mapped twice").format(row.program_outcome))
			seen.add(row.program_outcome)
