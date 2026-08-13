# Shiksha

The India-2026 higher-education layer for ERPNext v16 — examination controller,
NEP credits / ABC / APAAR, NAAC-NIRF-AISHE reporting, campus services, statutory
committees, and DPDP consent.

Licence: GPL-3.0-only (derivative of ERPNext).

See `../../PLAN.md` for the 14-phase execution plan and `../../README.md` for setup.

## Modules

| Module | Phase | Status |
|---|---|---|
| `academics` | 1 | Regulation, Curriculum Version, CO/PO, attainment |
| `admission` | 2 | Seat allotment engine |
| `credits` | 6 | SGPA/CGPA, grading |
| `finance_ext` | 3 | Dues gate |
| `examination`, `campus`, `governance`, `careers`, `research`, `compliance`, `privacy`, `integrations` | 5–11 | scaffolded |

## Tests

```bash
# Tier 1 — pure logic, no frappe needed
PYTHONPATH=. python3 -m pytest shiksha -q

# Tier 2 — needs a live site
bench --site erp.localhost run-tests --app shiksha
```
