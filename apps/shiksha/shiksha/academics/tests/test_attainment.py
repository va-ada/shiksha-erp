# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Checkpoint-10.D Pass 1: CO/PO attainment on a cohort with hand-computed values."""
from shiksha.academics.attainment import (
	COResult,
	attainment_gap,
	co_attainment_level,
	po_attainment,
)


def test_co_level_3_when_70pct_cross_target():
	# 8 of 10 students (80%) score >= 60% of 100 → level 3
	scores = tuple([65] * 8 + [40] * 2)
	co = COResult("CO1", max_marks=100, scores=scores)
	assert co_attainment_level(co) == 3


def test_co_level_2_boundary():
	# exactly 60% of cohort attains → level 2
	scores = tuple([60] * 6 + [30] * 4)
	assert co_attainment_level(COResult("CO2", 100, scores)) == 2


def test_co_level_1_boundary():
	scores = tuple([60] * 5 + [30] * 5)  # 50% attain → level 1
	assert co_attainment_level(COResult("CO3", 100, scores)) == 1


def test_co_level_0_when_below_all_thresholds():
	scores = tuple([60] * 4 + [10] * 6)  # 40% attain → level 0
	assert co_attainment_level(COResult("CO4", 100, scores)) == 0


def test_co_empty_cohort_is_zero_not_crash():
	assert co_attainment_level(COResult("CO5", 100, ())) == 0


def test_po_weighted_average_hand_computed():
	co_levels = {"CO1": 3, "CO2": 2, "CO3": 1}
	matrix = {
		"CO1": {"PO1": 3, "PO2": 1},
		"CO2": {"PO1": 2},
		"CO3": {"PO2": 3},
	}
	got = po_attainment(co_levels, matrix)
	# PO1 = (3*3 + 2*2) / (3+2) = 13/5 = 2.6
	# PO2 = (3*1 + 1*3) / (1+3) = 6/4  = 1.5
	assert got == {"PO1": 2.6, "PO2": 1.5}


def test_unassessed_co_excluded_not_zeroed():
	"""A CO not assessed this cycle must not drag the PO down as if it scored 0."""
	matrix = {"CO1": {"PO1": 3}, "CO2": {"PO1": 3}}
	only_co1 = po_attainment({"CO1": 3}, matrix)
	assert only_co1 == {"PO1": 3.0}, "unassessed CO2 wrongly counted"


def test_gap_analysis_flags_only_below_target():
	gaps = attainment_gap({"PO1": 2.6, "PO2": 1.5, "PO3": 2.0}, target=2.0)
	assert gaps == {"PO2": 0.5}
