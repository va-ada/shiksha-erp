# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""doc_events handlers wired in shiksha/hooks.py — never patch upstream apps."""
import frappe
from frappe import _


def stamp_regulation(doc, method=None):
	"""Program Enrollment.validate — stamp the active regulation once; immutable after."""
	if doc.get("custom_regulation"):
		old = doc.get_doc_before_save()
		if old and old.get("custom_regulation") and old.custom_regulation != doc.custom_regulation:
			frappe.throw(
				_("Regulation is stamped at admission and immutable. "
				  "Enrollment {0} is governed by {1} forever.").format(doc.name, old.custom_regulation)
			)
		return
	# Auto-stamp: the Active regulation whose curriculum covers this program
	active = frappe.db.get_value(
		"Curriculum Version",
		{"program": doc.program, "status": "Active"},
		"regulation",
	)
	if active:
		doc.custom_regulation = active


def validate_course_credits(doc, method=None):
	"""Course.validate — credits must equal the L-T-P derivation when hours are set.

	Convention (AICTE): 1 credit per lecture hour, 1 per tutorial hour, 0.5 per practical hour.
	"""
	lh = doc.get("custom_lecture_hours") or 0
	th = doc.get("custom_tutorial_hours") or 0
	ph = doc.get("custom_practical_hours") or 0
	credits = doc.get("custom_credits")
	if (lh or th or ph) and credits is not None:
		expected = lh + th + ph * 0.5
		if abs(credits - expected) > 0.01:
			frappe.throw(
				_("Credits {0} do not match L-T-P {1}-{2}-{3} (expected {4})").format(
					credits, lh, th, ph, expected
				)
			)
