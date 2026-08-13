# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""The ONLY sanctioned way any module reads an academic rule.

Architectural Rule 2: every academic rule resolves through Regulation, stamped
immutably on the student's Program Enrollment at admission. A 2023-batch student
is governed by 2023 rules forever, regardless of later regulations.
"""
import frappe
from frappe import _

# Whitelist of rule fields modules may request — misspellings fail loudly.
RULE_FIELDS = frozenset({
	"min_total_credits",
	"max_total_credits",
	"max_programme_duration_years",
	"min_attendance_pct",
	"condonation_min_pct",
	"condonation_fee",
	"pass_mark_pct",
	"internal_weightage_pct",
	"max_backlogs_for_promotion",
	"double_valuation_variance_pct",
	"grading_scale",
})


def get_regulation(student: str, program: str | None = None) -> str:
	"""Return the Regulation code stamped on the student's Program Enrollment."""
	filters = {"student": student, "docstatus": ("<", 2)}
	if program:
		filters["program"] = program
	reg = frappe.db.get_value("Program Enrollment", filters, "custom_regulation")
	if not reg:
		frappe.throw(
			_("No regulation stamped on enrollment for student {0}. "
			  "Enrollment is invalid — fix admission data.").format(student)
		)
	return reg


def get_rule(student: str, rule_name: str, program: str | None = None):
	"""Resolve a single academic rule for a student via their stamped regulation."""
	if rule_name not in RULE_FIELDS:
		frappe.throw(_("Unknown academic rule: {0}").format(rule_name))
	regulation = get_regulation(student, program)
	value = frappe.db.get_value("Regulation", regulation, rule_name)
	if value is None:
		frappe.throw(
			_("Regulation {0} does not define rule {1}").format(regulation, rule_name)
		)
	return value


def get_refund_pct(student: str, days_since_admission: int, program: str | None = None) -> float:
	"""Return the refund percentage for a cancellation N days after admission."""
	regulation = get_regulation(student, program)
	slabs = frappe.get_all(
		"Regulation Refund Slab",
		filters={"parent": regulation, "parenttype": "Regulation"},
		fields=["upto_days_from_admission", "refund_pct"],
		order_by="upto_days_from_admission asc",
	)
	for slab in slabs:
		if days_since_admission <= slab.upto_days_from_admission:
			return slab.refund_pct
	return 0.0  # beyond the last slab: no refund
