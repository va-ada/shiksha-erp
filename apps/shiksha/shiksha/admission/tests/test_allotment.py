# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Checkpoint-2 Pass 1: 100 synthetic applicants vs a 60-seat matrix.

Pure-python — runs with plain pytest, no bench needed:
    python3 -m pytest apps/shiksha/shiksha/admission/tests/ -q
"""
from shiksha.admission.allotment import Applicant, allot, cancel, rank

MATRIX_60 = {"GEN": 24, "EWS": 6, "OBC": 16, "SC": 9, "ST": 5}  # 40.5/10/27/15/7.5%


def synth_applicants(n=100):
	# Deterministic synthetic cohort: interleaved categories, descending scores
	cats = ["GEN", "OBC", "SC", "GEN", "EWS", "OBC", "GEN", "ST", "SC", "OBC"]
	return [
		Applicant(f"A{i:03d}", cats[i % 10], score=1000 - i, tie_break=(i,))
		for i in range(n)
	]


def test_matrix_totals():
	assert sum(MATRIX_60.values()) == 60


def test_every_seat_filled_with_surplus_applicants():
	res = allot(synth_applicants(100), MATRIX_60)
	assert len(res["allotments"]) == 60
	for cat, pool in res["pools"].items():
		assert pool.vacant == 0, f"{cat} left {pool.vacant} vacant"


def test_reserved_topper_takes_gen_seat_not_quota():
	"""An SC candidate above the open cutoff must occupy a GEN seat (migration)."""
	apps = synth_applicants(100)
	res = allot(apps, MATRIX_60)
	# A002 is SC with the 3rd-best score overall — far above open cutoff
	assert res["allotments"]["A002"] == "GEN"


def test_category_merit_order_within_quota():
	res = allot(synth_applicants(100), MATRIX_60)
	sc_seatholders = res["pools"]["SC"].allotted
	scores = {a.applicant_id: a.score for a in synth_applicants(100)}
	got = [scores[i] for i in sc_seatholders]
	assert got == sorted(got, reverse=True), "SC quota not in merit order"


def test_determinism():
	r1 = allot(synth_applicants(100), MATRIX_60)
	r2 = allot(synth_applicants(100), MATRIX_60)
	assert r1["allotments"] == r2["allotments"]


def test_cancellation_returns_seat_to_correct_pool():
	apps = synth_applicants(100)
	by_id = {a.applicant_id: a for a in apps}
	res = allot(apps, MATRIX_60)
	# find an SC-quota seat holder and cancel them
	victim = res["pools"]["SC"].allotted[0]
	seat_cat = cancel(res, victim, by_id)
	assert seat_cat == "SC"
	assert res["pools"]["SC"].vacant == 1
	assert victim not in res["allotments"]


def test_rank_tie_break_deterministic():
	a = Applicant("A2", "GEN", 500, (1,))
	b = Applicant("A1", "GEN", 500, (1,))
	assert [x.applicant_id for x in rank([a, b])] == ["A1", "A2"]
