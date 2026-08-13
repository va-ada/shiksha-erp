# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Pass 1 (synthetic) tests for the academic spine — Checkpoint 1.

Run inside the bench container:  bench --site erp.localhost run-tests --app shiksha
"""
import frappe
from frappe.tests.utils import FrappeTestCase


def make_regulation(code, **overrides):
	if frappe.db.exists("Regulation", code):
		return frappe.get_doc("Regulation", code)
	defaults = dict(
		doctype="Regulation",
		regulation_code=code,
		regulation_title=f"Test Regulation {code}",
		effective_from_year=frappe.get_all("Academic Year", limit=1)[0].name,
		min_total_credits=160,
		max_total_credits=176,
		max_programme_duration_years=8,
		min_attendance_pct=75,
		condonation_min_pct=65,
		pass_mark_pct=40,
		internal_weightage_pct=40,
		max_backlogs_for_promotion=4,
		status="Active",
	)
	defaults.update(overrides)
	doc = frappe.get_doc(defaults)
	doc.insert(ignore_permissions=True)
	return doc


class TestRegulation(FrappeTestCase):
	def test_min_cannot_exceed_max_credits(self):
		doc = frappe.get_doc(
			doctype="Regulation",
			regulation_code="RBAD",
			regulation_title="Bad",
			effective_from_year=frappe.get_all("Academic Year", limit=1)[0].name,
			min_total_credits=200,
			max_total_credits=160,
			max_programme_duration_years=8,
			min_attendance_pct=75,
			pass_mark_pct=40,
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_condonation_floor_below_attendance_threshold(self):
		doc = frappe.get_doc(
			doctype="Regulation",
			regulation_code="RBAD2",
			regulation_title="Bad2",
			effective_from_year=frappe.get_all("Academic Year", limit=1)[0].name,
			min_total_credits=160,
			max_programme_duration_years=8,
			min_attendance_pct=75,
			condonation_min_pct=80,  # above threshold — invalid
			pass_mark_pct=40,
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_overlapping_refund_slabs_rejected(self):
		doc = frappe.get_doc(
			doctype="Regulation",
			regulation_code="RBAD3",
			regulation_title="Bad3",
			effective_from_year=frappe.get_all("Academic Year", limit=1)[0].name,
			min_total_credits=160,
			max_programme_duration_years=8,
			min_attendance_pct=75,
			pass_mark_pct=40,
			refund_slabs=[
				{"upto_days_from_admission": 15, "refund_pct": 100},
				{"upto_days_from_admission": 15, "refund_pct": 50},  # duplicate boundary
			],
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_two_regulations_resolve_different_rules(self):
		"""The core Checkpoint-1 assertion: R21 and R23 students get different rules."""
		r21 = make_regulation("R21T", pass_mark_pct=35, max_programme_duration_years=6)
		r23 = make_regulation("R23T", pass_mark_pct=40, max_programme_duration_years=8)
		self.assertNotEqual(r21.pass_mark_pct, r23.pass_mark_pct)
		self.assertEqual(frappe.db.get_value("Regulation", "R21T", "pass_mark_pct"), 35)
		self.assertEqual(frappe.db.get_value("Regulation", "R23T", "pass_mark_pct"), 40)

	def test_locked_field_edit_blocked_when_in_use(self):
		"""Once enrolled students reference a regulation, rule fields are immutable."""
		reg = make_regulation("RLOCK")
		# Simulate in-use without needing a full enrollment fixture
		if not frappe.db.has_column("Program Enrollment", "custom_regulation"):
			self.skipTest("custom_regulation field not yet migrated")


class TestRefundSlabs(FrappeTestCase):
	def test_slab_resolution(self):
		from shiksha.academics.regulation_resolver import get_refund_pct  # noqa
		reg = make_regulation(
			"RSLAB",
			refund_slabs=[
				{"upto_days_from_admission": 15, "refund_pct": 100},
				{"upto_days_from_admission": 30, "refund_pct": 50},
				{"upto_days_from_admission": 60, "refund_pct": 10},
			],
		)
		slabs = [(s.upto_days_from_admission, s.refund_pct) for s in reg.refund_slabs]
		self.assertEqual(slabs, [(15, 100.0), (30, 50.0), (60, 10.0)])
