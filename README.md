# Shiksha ERP

NEP-compliant Indian higher-education ERP: **ERPNext v16 + Frappe Education + HRMS +
India Compliance**, plus the custom `shiksha` app supplying the India-2026 layer
(examination controller, NEP credits/ABC/APAAR, NAAC/NIRF/AISHE, campus services,
statutory committees, DPDP). Licence: **GPL-3.0** (derivative of ERPNext).

See `PLAN.md` for the full 14-phase execution contract.

## From a clean machine

```bash
# 0. Prereqs: Docker Desktop running. That's it.
cp infra/.env.example infra/.env   # then edit passwords

# 1. Bring up the stack (MariaDB 10.6, Redis ×2, ERPNext v16 backend/workers/nginx)
make up

# 2. One-time: create site + install all six apps (frappe→erpnext→hrms→india_compliance→education→shiksha)
make create-site
make install-apps

# 3. Open http://erp.localhost:8080  (login: Administrator / your ADMIN_PASSWORD)

# 4. Run the shiksha test suite (Checkpoint Pass 1)
make test
```

## Repository layout

```
PLAN.md              the approved execution plan — the contract
Makefile             up / create-site / install-apps / migrate / test / backup
infra/               compose.dev.yml + .env (never commit .env)
apps/shiksha/        the custom Frappe app — ALL our code lives here
  shiksha/academics/     Regulation, Curriculum Version, resolver  ← Phase 1
  shiksha/admission/     merit list, seat matrix, rounds           ← Phase 2
  shiksha/examination/   exam controller                           ← Phase 5
  ... (12 modules, one per PLAN.md flow group)
```

## Architectural rules (enforced)

1. **Never patch upstream apps** — `make upstream-pristine` must always pass.
2. **Every academic rule resolves through `Regulation`** via
   `shiksha.academics.regulation_resolver.get_rule(student, rule)` — stamped at
   admission, immutable forever.
