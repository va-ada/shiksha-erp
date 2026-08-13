# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""CO/PO attainment computation — NBA accreditation evidence (Phase 10.D).

Pure functions so the accreditation committee can audit the arithmetic and
Pass-1 tests run without a bench. The NBA-standard direct-attainment method:

  1. Per CO, attainment level 0-3 from the % of students crossing a target mark.
  2. Per PO, weighted average of contributing CO levels, weights = correlation
     strength (1/2/3) from the CO-PO matrix.
  3. Attainment is expressed on the same 0-3 scale as the correlation matrix.
"""
from dataclasses import dataclass

# Standard NBA thresholds: % of students at-or-above the target mark → level
DEFAULT_LEVEL_THRESHOLDS = ((70.0, 3), (60.0, 2), (50.0, 1))


@dataclass(frozen=True)
class COResult:
	"""Marks scored by each student against one CO's assessment items."""
	co_code: str
	max_marks: float
	scores: tuple[float, ...]


def co_attainment_level(
	result: COResult,
	target_pct: float = 60.0,
	thresholds=DEFAULT_LEVEL_THRESHOLDS,
) -> int:
	"""Level 0-3 for one CO.

	target_pct: the mark a student must reach to 'attain' the CO.
	thresholds: (% of cohort attaining, level) descending.
	"""
	if not result.scores:
		return 0
	target_mark = result.max_marks * target_pct / 100.0
	attained = sum(1 for s in result.scores if s >= target_mark)
	pct_attaining = attained * 100.0 / len(result.scores)
	for cutoff, level in thresholds:
		if pct_attaining >= cutoff:
			return level
	return 0


def po_attainment(
	co_levels: dict[str, int],
	co_po_matrix: dict[str, dict[str, int]],
) -> dict[str, float]:
	"""Weighted PO attainment from CO levels.

	co_levels:    {"CO1": 3, "CO2": 2, ...}
	co_po_matrix: {"CO1": {"PO1": 3, "PO2": 1}, ...}  correlation strengths
	Returns {"PO1": 2.75, ...} on the 0-3 scale.
	"""
	numerator: dict[str, float] = {}
	denominator: dict[str, float] = {}
	for co, po_weights in co_po_matrix.items():
		level = co_levels.get(co)
		if level is None:
			continue  # CO not assessed this cycle — excluded, not treated as zero
		for po, weight in po_weights.items():
			numerator[po] = numerator.get(po, 0.0) + level * weight
			denominator[po] = denominator.get(po, 0.0) + weight
	return {
		po: round(numerator[po] / denominator[po], 2)
		for po in numerator
		if denominator.get(po)
	}


def attainment_gap(
	attained: dict[str, float], target: float = 2.0
) -> dict[str, float]:
	"""Gap analysis for the NBA report: POs below target and by how much."""
	return {po: round(target - v, 2) for po, v in attained.items() if v < target}
