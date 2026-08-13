# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
import frappe
from frappe import _
from frappe.model.document import Document


class CurriculumVersion(Document):
	def validate(self):
		self._compute_total_credits()
		self._validate_against_regulation()
		self._validate_no_duplicate_courses()

	def _compute_total_credits(self):
		# Audit / mandatory-non-credit rows carry 0 credits toward the total
		self.total_credits = sum(
			row.credits for row in self.courses
			if row.course_type not in ("Audit", "Mandatory Non-Credit")
		)

	def _validate_against_regulation(self):
		reg = frappe.get_doc("Regulation", self.regulation)
		if self.status == "Active":
			if self.total_credits < reg.min_total_credits:
				frappe.throw(
					_("Total credits {0} below regulation minimum {1}").format(
						self.total_credits, reg.min_total_credits
					)
				)
			if reg.max_total_credits and self.total_credits > reg.max_total_credits:
				frappe.throw(
					_("Total credits {0} above regulation maximum {1}").format(
						self.total_credits, reg.max_total_credits
					)
				)

	def _validate_no_duplicate_courses(self):
		seen = set()
		for row in self.courses:
			key = (row.semester, row.course)
			if key in seen:
				frappe.throw(_("Course {0} appears twice in semester {1}").format(row.course, row.semester))
			seen.add(key)
