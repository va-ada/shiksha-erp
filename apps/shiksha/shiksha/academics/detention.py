# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Attendance-shortage detection reading thresholds from Regulation (Phase 4)."""
import frappe

from shiksha.academics.regulation_resolver import get_rule


def attendance_pct(student: str, academic_term: str) -> float:
	"""Percentage of periods present (OD-adjusted once Phase 4 lands Duty Leave)."""
	total, present = frappe.db.sql(
		"""
		select count(*), sum(case when status in ('Present', 'Half Day') then 1 else 0 end)
		from `tabStudent Attendance`
		where student = %s and docstatus = 1
		""",
		student,
	)[0]
	if not total:
		return 100.0
	return (present or 0) * 100.0 / total


def is_debarred(student: str, academic_term: str) -> bool:
	"""Below the regulation's minimum attendance and not condoned → debarred from exams."""
	threshold = get_rule(student, "min_attendance_pct")
	return attendance_pct(student, academic_term) < threshold


def refresh_shortage_alerts():
	"""Daily scheduled job — Phase 4 wires 75%/65% alerts to student, parent, mentor."""
	pass  # implemented in Phase 4
