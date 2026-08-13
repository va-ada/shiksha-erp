# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Fee computation (Phase 3.1–3.2). Pure functions — money logic must be auditable
by the Accounts office, and Checkpoint 3 Pass 2 reconciles it to the rupee against
a real bank statement.

All amounts are handled in paise (int) internally to avoid float drift, and
converted at the boundary. Never do rupee arithmetic in float.
"""
from dataclasses import dataclass
from datetime import date

from shiksha.finance_ext.money import Money


@dataclass(frozen=True)
class FeeComponent:
	name: str
	amount: Money
	refundable: bool = False   # caution deposit etc.


@dataclass(frozen=True)
class StudentFeeProfile:
	"""The axes a fee structure varies on."""
	program: str
	batch: str
	category: str = "GEN"       # GEN/EWS/OBC/SC/ST
	quota: str = "STATE"        # STATE/MANAGEMENT/NRI
	hosteller: bool = False


@dataclass(frozen=True)
class Instalment:
	due_date: date
	amount: Money
	late_fee_per_slab: tuple = ()   # ((days_overdue, Money), ...) ascending


def applicable_components(
	profile: StudentFeeProfile,
	rules: list[dict],
) -> list[FeeComponent]:
	"""Select components whose rule matches the profile.

	A rule matches when every key it specifies equals the profile's value.
	Rules that omit a key match any value — so a rule is a partial specification,
	and the most specific matching rule for a component name wins.
	"""
	axes = ("program", "batch", "category", "quota", "hosteller")
	best: dict[str, tuple[int, dict]] = {}
	for rule in rules:
		specificity = 0
		for axis in axes:
			if axis in rule:
				if rule[axis] != getattr(profile, axis):
					break
				specificity += 1
		else:
			name = rule["component"]
			if name not in best or specificity > best[name][0]:
				best[name] = (specificity, rule)
	return [
		FeeComponent(
			name=name,
			amount=Money(rule["amount_paise"]),
			refundable=rule.get("refundable", False),
		)
		for name, (_, rule) in sorted(best.items())
	]


def total_payable(components: list[FeeComponent], concessions: list[Money] = ()) -> Money:
	gross = sum((c.amount for c in components), Money(0))
	relief = sum(concessions, Money(0))
	net = gross - relief
	return net if net.paise > 0 else Money(0)   # a concession never yields a negative bill


def late_fee(instalment: Instalment, paid_on: date) -> Money:
	"""Late fee from the highest slab the delay has crossed. Slabs are thresholds,
	not cumulative charges — crossing day 30 charges the day-30 amount, not
	day-7 plus day-30."""
	overdue_days = (paid_on - instalment.due_date).days
	if overdue_days <= 0:
		return Money(0)
	charge = Money(0)
	for threshold_days, amount in sorted(instalment.late_fee_per_slab, key=lambda s: s[0]):
		if overdue_days >= threshold_days:
			charge = amount
	return charge


def build_instalments(
	total: Money,
	due_dates: list[date],
	late_slabs: tuple = (),
) -> list[Instalment]:
	"""Split a total across instalments. Any indivisible remainder goes on the
	FIRST instalment, never the last — a student must never discover an extra
	rupee at the end of the year."""
	n = len(due_dates)
	if n == 0:
		raise ValueError("at least one due date required")
	base, remainder = divmod(total.paise, n)
	return [
		Instalment(
			due_date=d,
			amount=Money(base + (remainder if i == 0 else 0)),
			late_fee_per_slab=late_slabs,
		)
		for i, d in enumerate(due_dates)
	]


def outstanding(instalments: list[Instalment], payments: list[Money]) -> Money:
	billed = sum((i.amount for i in instalments), Money(0))
	paid = sum(payments, Money(0))
	return billed - paid
