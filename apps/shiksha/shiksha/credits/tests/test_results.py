# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Checkpoint-6 Pass 1: SGPA/CGPA against hand-calculated values."""
import pytest

from shiksha.credits.results import (
	CourseResult,
	cgpa,
	classification,
	credits_earned,
	evaluate,
	grade_for,
	sgpa,
	total_pct,
)

RULES = dict(pass_mark_pct=40.0, internal_weightage_pct=40.0)


def cr(course, credits, im, em, ctype="Core"):
	return CourseResult(course, credits, im, 40, em, 60, ctype)


def test_total_pct_weighting():
	# internal 40/40 = 100%, external 30/60 = 50%; 40% weight → 100*.4 + 50*.6 = 70
	r = cr("CS101", 4, 40, 30)
	assert total_pct(r, 40.0) == pytest.approx(70.0)


def test_grade_boundaries():
	assert grade_for(90.0) == ("O", 10.0)
	assert grade_for(89.99) == ("A+", 9.0)
	assert grade_for(40.0) == ("P", 4.0)
	assert grade_for(39.99) == ("F", 0.0)


def test_absent_yields_AB_not_F():
	g = evaluate(CourseResult("CS101", 4, 30, 40, None, 60), **RULES)
	assert g["letter"] == "AB" and not g["passed"] and g["reason"] == "Absent"


def test_min_external_rule_fails_despite_high_total():
	"""Strong internals must not rescue a student below the external minimum."""
	r = cr("CS102", 4, 40, 12)  # ext 20%, total = 100*.4 + 20*.6 = 52 (above pass)
	g = evaluate(r, **RULES, min_external_pct=35.0)
	assert not g["passed"]
	assert "External" in g["reason"]


def test_pass_when_above_both_minimums():
	# internal 32/40 = 80%, external 36/60 = 60% → 80*.4 + 60*.6 = 68 → B+
	g = evaluate(cr("CS103", 4, 32, 36), **RULES, min_external_pct=35.0)
	assert g["passed"] and g["letter"] == "B+" and g["pct"] == 68.0


def test_sgpa_hand_computed():
	rows = [cr("A", 4, 40, 54), cr("B", 3, 32, 36), cr("C", 3, 20, 24)]
	graded = [(r, evaluate(r, **RULES)) for r in rows]
	# A: 100*.4 + 90*.6 = 94   → O  = 10
	# B: 80*.4  + 60*.6 = 68   → B+ = 7
	# C: 50*.4  + 40*.6 = 44   → P  = 4
	# (10*4 + 7*3 + 4*3) / 10 = (40+21+12)/10 = 7.3
	assert sgpa(graded) == 7.3


def test_audit_course_excluded_from_sgpa():
	rows = [cr("A", 4, 40, 54), cr("AUD", 2, 40, 54, "Audit")]
	graded = [(r, evaluate(r, **RULES)) for r in rows]
	assert sgpa(graded) == 10.0, "audit course wrongly moved the GPA"


def test_failed_course_consumes_credits_in_denominator():
	rows = [cr("A", 4, 40, 54), cr("F1", 4, 4, 6)]  # second fails hard
	graded = [(r, evaluate(r, **RULES)) for r in rows]
	# (10*4 + 0*4) / 8 = 5.0 — the backlog must depress SGPA
	assert sgpa(graded) == 5.0


def test_credits_earned_excludes_failures_and_audits():
	rows = [cr("A", 4, 40, 54), cr("F1", 4, 4, 6), cr("AUD", 2, 40, 54, "Audit")]
	graded = [(r, evaluate(r, **RULES)) for r in rows]
	assert credits_earned(graded) == 4


def test_cgpa_credit_weighted():
	# sem1: 8.0 over 20 credits, sem2: 9.0 over 22 credits
	# (8*20 + 9*22) / 42 = (160 + 198) / 42 = 8.52
	assert cgpa([(8.0, 20), (9.0, 22)]) == 8.52


def test_cgpa_empty_is_zero_not_crash():
	assert cgpa([]) == 0.0


@pytest.mark.parametrize("val,expected", [
	(8.0, "First Class with Distinction"),
	(7.5, "First Class with Distinction"),
	(7.49, "First Class"),
	(6.5, "First Class"),
	(6.0, "Second Class"),
	(5.2, "Pass Class"),
	(4.9, "Fail"),
])
def test_classification_boundaries(val, expected):
	assert classification(val) == expected
