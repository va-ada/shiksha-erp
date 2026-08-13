# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Dues gate consumed by exam registration, result release, hostel allotment, no-dues."""
import frappe


def has_blocking_dues(student: str) -> bool:
	"""True if the student has any unpaid Fees past due date (Phase 3 will extend
	with instalment plans and late-fee slabs)."""
	outstanding = frappe.db.sql(
		"""
		select coalesce(sum(outstanding_amount), 0)
		from `tabFees`
		where student = %s and docstatus = 1 and due_date < curdate()
		""",
		student,
	)[0][0]
	return outstanding > 0


def send_due_reminders():
	"""Daily scheduled job — Phase 3 wires SMS/email at T-7, T-1, T+1, T+7."""
	pass  # implemented in Phase 3 (needs DLT-registered SMS templates)
