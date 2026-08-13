# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Merit-list and seat-allotment engine (Phase 2.5–2.6).

Pure functions — no frappe imports — so Pass-1 tests run anywhere and the logic
is auditable by the admission committee. DocType layers call into this.

Reservation model (vertical categories + PwD horizontal reservation is Phase 2
scope; inter-se conversion rules follow the state's standard order).
"""
from dataclasses import dataclass, field

VERTICAL_CATEGORIES = ("GEN", "EWS", "OBC", "SC", "ST")


@dataclass(frozen=True)
class Applicant:
	applicant_id: str
	category: str            # GEN / EWS / OBC / SC / ST
	score: float             # entrance/qualifying score, higher = better
	tie_break: tuple = ()    # e.g. (subject_score, -age_days, application_no)


@dataclass
class SeatPool:
	category: str
	sanctioned: int
	allotted: list = field(default_factory=list)

	@property
	def vacant(self) -> int:
		return self.sanctioned - len(self.allotted)


def rank(applicants: list[Applicant]) -> list[Applicant]:
	"""Merit order: score desc, then the tie-break chain, then applicant_id for
	total determinism (two runs on the same data must produce the same list)."""
	return sorted(applicants, key=lambda a: (-a.score, a.tie_break, a.applicant_id))


def allot(applicants: list[Applicant], matrix: dict[str, int]) -> dict:
	"""Single-round allotment against a seat matrix {category: seats}.

	Rules implemented:
	- Reserved-category candidates who make the open (GEN) cutoff take GEN seats
	  first and do NOT consume their category quota (migration principle,
	  Indra Sawhney compliant).
	- Remaining reserved seats fill from that category's merit order.
	- Unfilled reserved seats are NOT auto-converted in round 1 (conversion is a
	  final-round policy decision — explicit, never silent).

	Returns {"allotments": {applicant_id: category_of_seat}, "pools": pools,
	         "waitlist": {category: [applicant_id, ...]}}
	"""
	pools = {c: SeatPool(c, matrix.get(c, 0)) for c in VERTICAL_CATEGORIES}
	merit = rank(applicants)
	allotments: dict[str, str] = {}

	# Pass 1 — open competition: strict merit order into GEN seats, any category
	for a in merit:
		if pools["GEN"].vacant <= 0:
			break
		if a.applicant_id in allotments:
			continue
		pools["GEN"].allotted.append(a.applicant_id)
		allotments[a.applicant_id] = "GEN"

	# Pass 2 — reserved seats: category merit order among the not-yet-allotted
	for cat in ("EWS", "OBC", "SC", "ST"):
		for a in merit:
			if pools[cat].vacant <= 0:
				break
			if a.applicant_id in allotments or a.category != cat:
				continue
			pools[cat].allotted.append(a.applicant_id)
			allotments[a.applicant_id] = cat

	waitlist: dict[str, list[str]] = {c: [] for c in VERTICAL_CATEGORIES}
	for a in merit:
		if a.applicant_id not in allotments:
			waitlist["GEN"].append(a.applicant_id)
			if a.category != "GEN":
				waitlist[a.category].append(a.applicant_id)

	return {"allotments": allotments, "pools": pools, "waitlist": waitlist}


def cancel(result: dict, applicant_id: str, applicants_by_id: dict[str, Applicant]) -> str:
	"""Return a cancelled applicant's seat to the correct pool; give back the
	category of the SEAT (not of the person). Waitlist movement is the caller's
	next `allot` round."""
	seat_cat = result["allotments"].pop(applicant_id, None)
	if seat_cat is None:
		raise ValueError(f"{applicant_id} holds no seat")
	result["pools"][seat_cat].allotted.remove(applicant_id)
	return seat_cat
