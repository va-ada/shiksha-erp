# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
import frappe
from frappe import _
from frappe.model.document import Document


class Regulation(Document):
	def validate(self):
		if self.max_total_credits and self.min_total_credits > self.max_total_credits:
			frappe.throw(_("Min total credits cannot exceed max total credits"))
		if self.condonation_min_pct and self.condonation_min_pct > self.min_attendance_pct:
			frappe.throw(_("Condonation floor must be below the minimum attendance threshold"))
		self._validate_refund_slabs()

	def _validate_refund_slabs(self):
		# Slabs must be contiguous, non-overlapping, ordered by days_from_admission
		prev_end = -1
		for slab in sorted(self.refund_slabs or [], key=lambda s: s.upto_days_from_admission):
			if slab.upto_days_from_admission <= prev_end:
				frappe.throw(_("Refund slabs overlap at {0} days").format(slab.upto_days_from_admission))
			if not (0 <= slab.refund_pct <= 100):
				frappe.throw(_("Refund % must be between 0 and 100"))
			prev_end = slab.upto_days_from_admission

	def on_update(self):
		# A regulation referenced by any enrollment may never weaken retroactively:
		# block edits to rule fields once Active and in use.
		if self.status == "Active" and not self.is_new():
			in_use = frappe.db.exists("Program Enrollment", {"custom_regulation": self.name})
			old = self.get_doc_before_save()
			if in_use and old:
				locked = (
					"min_total_credits", "max_total_credits", "max_programme_duration_years",
					"min_attendance_pct", "pass_mark_pct", "internal_weightage_pct",
					"max_backlogs_for_promotion",
				)
				changed = [f for f in locked if old.get(f) != self.get(f)]
				if changed:
					frappe.throw(
						_("Regulation {0} is in use by enrolled students; locked fields changed: {1}. "
						  "Create a new Regulation instead.").format(self.name, ", ".join(changed))
					)
