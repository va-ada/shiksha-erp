# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Checkpoint-1 Pass 2 smoke test — exercises the real DocTypes on a live site.

    bench --site erp.localhost execute shiksha.academics.smoke.run
"""
import frappe


def _academic_year():
	existing = frappe.get_all("Academic Year", limit=1)
	if existing:
		return existing[0].name
	doc = frappe.get_doc(
		doctype="Academic Year", academic_year_name="2023-24",
		year_start_date="2023-07-01", year_end_date="2024-06-30",
	).insert(ignore_permissions=True)
	return doc.name


def run():
	frappe.set_user("Administrator")
	year = _academic_year()
	results = []

	# 1. Create two regulations with genuinely different rules
	for code, pass_pct, dur in (("R21", 35.0, 6), ("R23", 40.0, 8)):
		if frappe.db.exists("Regulation", code):
			frappe.delete_doc("Regulation", code, force=True)
		frappe.get_doc(
			doctype="Regulation", regulation_code=code,
			regulation_title=f"B.Tech Regulation {code}",
			effective_from_year=year, min_total_credits=160, max_total_credits=176,
			max_programme_duration_years=dur, min_attendance_pct=75.0,
			condonation_min_pct=65.0, pass_mark_pct=pass_pct,
			internal_weightage_pct=40.0, max_backlogs_for_promotion=4,
			double_valuation_variance_pct=15.0, status="Active",
			refund_slabs=[
				{"upto_days_from_admission": 15, "refund_pct": 100, "description": "Full"},
				{"upto_days_from_admission": 30, "refund_pct": 50, "description": "Half"},
				{"upto_days_from_admission": 60, "refund_pct": 10, "description": "Nominal"},
			],
		).insert(ignore_permissions=True)
	frappe.db.commit()

	r21 = frappe.db.get_value("Regulation", "R21", "pass_mark_pct")
	r23 = frappe.db.get_value("Regulation", "R23", "pass_mark_pct")
	results.append(("two regulations resolve different pass marks", r21 == 35.0 and r23 == 40.0, f"R21={r21} R23={r23}"))

	# 2. Refund slab resolution via the resolver's slab lookup
	slabs = frappe.get_all(
		"Regulation Refund Slab", filters={"parent": "R23"},
		fields=["upto_days_from_admission", "refund_pct"],
		order_by="upto_days_from_admission asc",
	)
	def pct_at(day):
		for s in slabs:
			if day <= s.upto_days_from_admission:
				return s.refund_pct
		return 0.0
	ok = pct_at(10) == 100 and pct_at(20) == 50 and pct_at(45) == 10 and pct_at(90) == 0
	results.append(("refund slabs resolve by day band", ok, f"d10={pct_at(10)} d20={pct_at(20)} d45={pct_at(45)} d90={pct_at(90)}"))

	# 3. Validation actually fires: min > max credits must be rejected
	rejected = False
	try:
		frappe.get_doc(
			doctype="Regulation", regulation_code="RBADSMOKE", regulation_title="Bad",
			effective_from_year=year, min_total_credits=200, max_total_credits=160,
			max_programme_duration_years=8, min_attendance_pct=75.0,
			pass_mark_pct=40.0,
		).insert(ignore_permissions=True)
	except frappe.ValidationError:
		rejected = True
	results.append(("min>max credits rejected", rejected, "ValidationError raised" if rejected else "NOT REJECTED"))

	# 4. Overlapping refund slabs rejected
	rejected = False
	try:
		frappe.get_doc(
			doctype="Regulation", regulation_code="RBADSLAB", regulation_title="BadSlab",
			effective_from_year=year, min_total_credits=160,
			max_programme_duration_years=8, min_attendance_pct=75.0, pass_mark_pct=40.0,
			refund_slabs=[
				{"upto_days_from_admission": 15, "refund_pct": 100},
				{"upto_days_from_admission": 15, "refund_pct": 50},
			],
		).insert(ignore_permissions=True)
	except frappe.ValidationError:
		rejected = True
	results.append(("overlapping refund slabs rejected", rejected, "ValidationError raised" if rejected else "NOT REJECTED"))

	# 5. Condonation floor above threshold rejected
	rejected = False
	try:
		frappe.get_doc(
			doctype="Regulation", regulation_code="RBADCOND", regulation_title="BadCond",
			effective_from_year=year, min_total_credits=160,
			max_programme_duration_years=8, min_attendance_pct=75.0,
			condonation_min_pct=80.0, pass_mark_pct=40.0,
		).insert(ignore_permissions=True)
	except frappe.ValidationError:
		rejected = True
	results.append(("condonation floor above threshold rejected", rejected, "ValidationError raised" if rejected else "NOT REJECTED"))

	frappe.db.rollback()

	print("\n=== Checkpoint 1 — Pass 2 (live site) ===")
	passed = 0
	for name, ok, detail in results:
		print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ({detail})")
		passed += bool(ok)
	print(f"=== {passed}/{len(results)} passed ===\n")
	return passed == len(results)
