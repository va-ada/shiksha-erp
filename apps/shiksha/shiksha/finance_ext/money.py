# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Integer-paise money type.

Float rupees lose money: 0.1 + 0.2 != 0.3. Checkpoint 3 Pass 2 requires
reconciliation to the rupee against a real bank statement, so every intermediate
value stays an int.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Money:
	paise: int

	def __post_init__(self):
		if not isinstance(self.paise, int):
			raise TypeError(f"Money takes int paise, got {type(self.paise).__name__}")

	@classmethod
	def from_rupees(cls, rupees: str | int) -> Money:
		"""Accepts '1234.50' or 1234. Never accepts a float — that is the bug
		this class exists to prevent."""
		if isinstance(rupees, float):
			raise TypeError("refusing float rupees; pass a str like '1234.50'")
		if isinstance(rupees, int):
			return cls(rupees * 100)
		whole, _, frac = str(rupees).partition(".")
		frac = (frac + "00")[:2]
		sign = -1 if whole.startswith("-") else 1
		return cls(int(whole) * 100 + sign * int(frac or 0))

	@property
	def rupees(self) -> str:
		sign = "-" if self.paise < 0 else ""
		whole, frac = divmod(abs(self.paise), 100)
		return f"{sign}{whole}.{frac:02d}"

	def __add__(self, other):
		if other == 0:
			return self                      # lets sum() start at 0
		return Money(self.paise + other.paise)

	__radd__ = __add__

	def __sub__(self, other) -> Money:
		return Money(self.paise - other.paise)

	def __mul__(self, n: int) -> Money:
		if not isinstance(n, int):
			raise TypeError("multiply Money by int only; use apply_pct for percentages")
		return Money(self.paise * n)

	def apply_pct(self, pct: float) -> Money:
		"""Percentage of an amount, rounded half-up to the paise — the convention
		Indian accounting expects."""
		from decimal import ROUND_HALF_UP, Decimal
		result = (Decimal(self.paise) * Decimal(str(pct)) / Decimal(100)).quantize(
			Decimal(1), rounding=ROUND_HALF_UP
		)
		return Money(int(result))

	def __str__(self) -> str:
		return f"₹{self.rupees}"
