# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Checkpoint-3 Pass 1: fee arithmetic to the paise."""
from datetime import date

import pytest

from shiksha.finance_ext.fee_engine import (
	FeeComponent,
	Instalment,
	StudentFeeProfile,
	applicable_components,
	build_instalments,
	late_fee,
	outstanding,
	total_payable,
)
from shiksha.finance_ext.money import Money

R = Money.from_rupees


# ---------- Money ----------

def test_no_float_drift():
	assert R("0.10") + R("0.20") == R("0.30")


def test_float_rupees_refused():
	with pytest.raises(TypeError):
		R(1234.50)


def test_rupee_formatting():
	assert R("1234.50").rupees == "1234.50"
	assert R(1234).rupees == "1234.00"
	assert Money(5).rupees == "0.05"


def test_pct_rounds_half_up():
	# 10% of 1234.55 = 123.455 -> 123.46 (half-up, not banker's)
	assert R("1234.55").apply_pct(10).rupees == "123.46"


def test_multiply_by_float_refused():
	with pytest.raises(TypeError):
		R("100.00") * 1.5


# ---------- Component selection ----------

RULES = [
	{"component": "Tuition", "program": "BTECH-CSE", "amount_paise": 12000000},          # ₹1,20,000 base
	{"component": "Tuition", "program": "BTECH-CSE", "category": "SC", "amount_paise": 3000000},   # ₹30,000
	{"component": "Tuition", "program": "BTECH-CSE", "quota": "MANAGEMENT", "amount_paise": 25000000},
	{"component": "Exam", "amount_paise": 250000},                                        # ₹2,500 everyone
	{"component": "Hostel", "hosteller": True, "amount_paise": 8000000},                  # ₹80,000
	{"component": "Caution Deposit", "amount_paise": 500000, "refundable": True},
]


def test_base_profile_gets_base_tuition():
	p = StudentFeeProfile("BTECH-CSE", "2023", "GEN", "STATE", hosteller=False)
	comps = {c.name: c.amount for c in applicable_components(p, RULES)}
	assert comps["Tuition"] == R("120000")
	assert "Hostel" not in comps


def test_more_specific_rule_wins_for_sc():
	p = StudentFeeProfile("BTECH-CSE", "2023", "SC", "STATE", hosteller=False)
	comps = {c.name: c.amount for c in applicable_components(p, RULES)}
	assert comps["Tuition"] == R("30000"), "SC concessional tuition not applied"


def test_hosteller_gets_hostel_component():
	p = StudentFeeProfile("BTECH-CSE", "2023", "GEN", "STATE", hosteller=True)
	comps = {c.name: c.amount for c in applicable_components(p, RULES)}
	assert comps["Hostel"] == R("80000")


def test_sc_hosteller_management_total_hand_computed():
	"""The exact Checkpoint-3 assertion: SC + hosteller + management quota."""
	p = StudentFeeProfile("BTECH-CSE", "2023", "SC", "MANAGEMENT", hosteller=True)
	comps = applicable_components(p, RULES)
	names = {c.name: c.amount for c in comps}
	# SC rule and MANAGEMENT rule are both specificity 2 — SC listed first, so
	# the later equally-specific rule does NOT displace it (strict > comparison).
	assert names["Tuition"] == R("30000")
	# 30000 + 2500 + 80000 + 5000 = 117500
	assert total_payable(comps) == R("117500")


def test_concession_never_produces_negative_bill():
	comps = [FeeComponent("Tuition", R("10000"))]
	assert total_payable(comps, [R("15000")]) == R("0")


# ---------- Instalments ----------

DUE = [date(2026, 7, 1), date(2026, 10, 1), date(2027, 1, 1)]


def test_remainder_lands_on_first_instalment():
	# ₹1000.00 over 3 -> 333.34 + 333.33 + 333.33
	inst = build_instalments(R("1000"), DUE)
	assert [i.amount.rupees for i in inst] == ["333.34", "333.33", "333.33"]
	assert sum((i.amount for i in inst), Money(0)) == R("1000")


def test_instalments_sum_exactly_to_total():
	for total in ("50000", "117500", "0.01", "99999.99"):
		inst = build_instalments(R(total), DUE)
		assert sum((i.amount for i in inst), Money(0)) == R(total)


def test_no_due_dates_raises():
	with pytest.raises(ValueError):
		build_instalments(R("1000"), [])


# ---------- Late fees ----------

SLABS = ((7, R("500")), (30, R("2000")), (60, R("5000")))


def test_no_late_fee_when_paid_on_time():
	i = Instalment(date(2026, 7, 1), R("10000"), SLABS)
	assert late_fee(i, date(2026, 7, 1)) == R("0")
	assert late_fee(i, date(2026, 6, 25)) == R("0")


def test_late_fee_uses_highest_crossed_slab_not_cumulative():
	i = Instalment(date(2026, 7, 1), R("10000"), SLABS)
	assert late_fee(i, date(2026, 7, 5)) == R("0")      # 4 days, below first slab
	assert late_fee(i, date(2026, 7, 8)) == R("500")    # 7 days
	assert late_fee(i, date(2026, 7, 31)) == R("2000")  # 30 days — NOT 500+2000
	assert late_fee(i, date(2026, 9, 30)) == R("5000")  # 91 days


def test_outstanding_after_partial_payment():
	inst = build_instalments(R("117500"), DUE)
	assert outstanding(inst, [R("50000")]) == R("67500")
	assert outstanding(inst, [R("117500")]) == R("0")
