# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Result processing: grade → grade point → SGPA/CGPA (Phase 6.1).

Pure functions. Every threshold arrives as an argument resolved from the
student's stamped Regulation — nothing here hardcodes an academic rule
(Architectural Rule 2).

UGC 10-point scale is the default convention; a Regulation may override the
scale entirely via its linked Grading Scale.
"""
from dataclasses import dataclass

# UGC-standard 10-point scale: (min_pct, letter, grade_point)
UGC_10_POINT = (
	(90.0, "O", 10.0),
	(80.0, "A+", 9.0),
	(70.0, "A", 8.0),
	(60.0, "B+", 7.0),
	(50.0, "B", 6.0),
	(45.0, "C", 5.0),
	(40.0, "P", 4.0),
	(0.0, "F", 0.0),
)


@dataclass(frozen=True)
class CourseResult:
	course: str
	credits: float
	internal_marks: float
	internal_max: float
	external_marks: float | None      # None = absent
	external_max: float
	course_type: str = "Core"         # Audit / Mandatory Non-Credit earn no grade points


def total_pct(r: CourseResult, internal_weightage_pct: float) -> float:
	"""Weighted total on a 100 scale."""
	int_pct = (r.internal_marks / r.internal_max * 100.0) if r.internal_max else 0.0
	ext_pct = (
		(r.external_marks / r.external_max * 100.0)
		if (r.external_max and r.external_marks is not None)
		else 0.0
	)
	w = internal_weightage_pct / 100.0
	return int_pct * w + ext_pct * (1 - w)


def grade_for(pct: float, scale=UGC_10_POINT) -> tuple[str, float]:
	for min_pct, letter, point in scale:
		if pct >= min_pct:
			return letter, point
	return "F", 0.0


def evaluate(
	r: CourseResult,
	*,
	pass_mark_pct: float,
	internal_weightage_pct: float,
	min_external_pct: float = 0.0,
	scale=UGC_10_POINT,
) -> dict:
	"""Grade one course. Returns letter, grade point, pass flag, and the reason
	on failure — the reason is printed on the grade card, so it must be exact."""
	if r.external_marks is None:
		return {"letter": "AB", "point": 0.0, "passed": False, "reason": "Absent"}

	pct = total_pct(r, internal_weightage_pct)
	ext_pct = (r.external_marks / r.external_max * 100.0) if r.external_max else 0.0

	# Many regulations require a separate minimum in the external component
	if min_external_pct and ext_pct < min_external_pct:
		return {
			"letter": "F", "point": 0.0, "passed": False,
			"reason": f"External {ext_pct:.1f}% below minimum {min_external_pct}%",
		}
	if pct < pass_mark_pct:
		return {
			"letter": "F", "point": 0.0, "passed": False,
			"reason": f"Total {pct:.1f}% below pass mark {pass_mark_pct}%",
		}

	letter, point = grade_for(pct, scale)
	return {"letter": letter, "point": point, "passed": True, "reason": "", "pct": round(pct, 2)}


def sgpa(graded: list[tuple[CourseResult, dict]]) -> float:
	"""Credit-weighted grade-point average for one semester.

	Audit and Mandatory Non-Credit courses are excluded from both numerator and
	denominator — they appear on the transcript but never move the GPA.
	Failed courses count with 0 points but DO consume credits in the denominator
	(standard UGC practice), which is why a backlog depresses SGPA.
	"""
	num = den = 0.0
	for r, g in graded:
		if r.course_type in ("Audit", "Mandatory Non-Credit"):
			continue
		num += r.credits * g["point"]
		den += r.credits
	return round(num / den, 2) if den else 0.0


def cgpa(semester_sgpas: list[tuple[float, float]]) -> float:
	"""Cumulative GPA from [(sgpa, credits_that_semester), ...]."""
	num = sum(s * c for s, c in semester_sgpas)
	den = sum(c for _, c in semester_sgpas)
	return round(num / den, 2) if den else 0.0


def credits_earned(graded: list[tuple[CourseResult, dict]]) -> float:
	"""Credits that actually go to the Credit Ledger / ABC — passed courses only."""
	return sum(
		r.credits for r, g in graded
		if g["passed"] and r.course_type not in ("Audit", "Mandatory Non-Credit")
	)


def classification(final_cgpa: float) -> str:
	"""UGC-convention degree classification."""
	if final_cgpa >= 7.5:
		return "First Class with Distinction"
	if final_cgpa >= 6.5:
		return "First Class"
	if final_cgpa >= 5.5:
		return "Second Class"
	if final_cgpa >= 5.0:
		return "Pass Class"
	return "Fail"
