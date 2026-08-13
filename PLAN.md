# Plan: Shiksha — NEP-Compliant Higher-Education ERP on ERPNext v16

> Status: **AWAITING APPROVAL** — no code written yet.
> Author: Claude · Date: 2026-08-13 · Target: real college deployment

---

## Problem Statement

An Indian higher-education institution (affiliated college / autonomous college / deemed
university) needs a single system of record covering the complete institutional lifecycle —
from prospect enquiry through admission, academic delivery, examination, credit accounting,
finance, HR, campus services, statutory compliance, and graduation — operated by real staff
on real student data.

**Who the users are:** students, parents/guardians, faculty, HoDs, deans, the Registrar, the
Controller of Examinations, the Accounts office, HR, hostel wardens, librarians, the Training &
Placement Officer, IQAC coordinators, and the Principal/VC. Each with distinct, scoped access.

**Expected output:** a deployed, running ERP — ERPNext v16 + Frappe Education + Frappe HRMS +
India Compliance, plus one custom Frappe app (`shiksha`) supplying the India-2026 higher-education
layer that no off-the-shelf app provides: examination-controller lifecycle, NEP credit accounting,
ABC/APAAR/NAD integration, NAAC/NIRF/AISHE reporting, campus services, statutory committees, and
DPDP-compliant consent handling. Done = a college can run an admission cycle, a semester, an
examination cycle, and a compliance submission on it without leaving the system.

**Why this approach:** the administrative half of a college ERP (accounting, payroll, procurement,
assets, workflow, permissions, reporting) is generic business software that ERPNext already solves
at production grade under GPLv3. Re-implementing it would consume the entire project budget and
produce something worse. We buy that half for free and spend all effort on the half that is
genuinely India-higher-education-specific.

---

## Assumptions

Every one of these is a real assumption. If any is wrong, tell me before Phase 0 — several of
them change the schema.

1. **Single institution**, not a multi-college group. Multi-tenancy is not a Phase-1 requirement.
   (Frappe supports multi-site; adding a second college later means a second site, not a rewrite.)
2. **GPLv3 is acceptable.** The resulting system is a derivative of ERPNext and must be
   distributed under GPLv3 if distributed at all. Running it in-house for your own college
   imposes no obligation whatsoever. Selling it as closed-source is not permitted.
3. **Indian regulatory context** — UGC/AICTE, NEP 2020, NCrF, ABC/APAAR, NAAC, NIRF, AISHE,
   DPDP Act 2023 + Rules 2025.
4. **Semester system with credits.** Annual-system-only institutions need Phase 1 adjusted.
5. **The affiliating university's exam data format** will be obtained during Phase 5. If the
   college is autonomous, we own the full exam lifecycle; if affiliated, we own internals and
   integrate for externals. **This is the single biggest open question — see Risks.**
6. **Deployment target is a Linux VPS or on-prem server** (not managed Frappe Cloud), self-hosted
   via Docker. Development happens locally on macOS via the same Docker images.
7. Legacy data exists in some combination of Excel, Tally, and an existing portal, and must be
   migrated. Volume and quality unknown until Phase 12 discovery.
8. Staff will need training; adoption is a change-management problem, not a software problem.
   Research consistently finds this is the dominant cause of higher-ed ERP failure.
9. **NEURAL-ERP is not being reused as code.** Its ML/at-risk-prediction idea is worth porting
   as a concept in a later phase; its schema and services are superseded.
10. The app name `shiksha` is baked into module paths and is painful to change after Phase 0.
    Confirm or replace it now.

---

## Dependencies & Prerequisites

### Verified on this machine (2026-08-13)

| Component | Required | Present | Status |
|---|---|---|---|
| Python | >=3.14,<3.15 (Frappe v16) | 3.14.2 | ✅ exact match |
| Node | 20/22 LTS (per Frappe v16) | 25.9.0 | ⚠️ newer than supported — Docker avoids this |
| Docker | any recent | 29.2.1 | ✅ installed |
| Docker Compose | v2+ | v5.0.2 | ✅ |
| Redis | 6+ | 8.4.0 | ✅ (Docker supplies its own) |
| **MariaDB** | **10.6+** | **absent (MySQL 9.6 only)** | ❌ **Docker supplies it** |
| bench CLI | latest | absent | ❌ not needed with Docker |
| wkhtmltopdf | 0.12.6 patched-qt | absent | ❌ Docker supplies it |
| yarn | 1.x | absent | ❌ Docker supplies it |
| git | 2.x | 2.50.1 | ✅ |
| Free disk | ~20 GB | 155 GB | ✅ |

**Conclusion:** a native `bench` install on this Mac would fight the missing MariaDB, the
absent wkhtmltopdf, and Node 25. Docker eliminates all four and makes local development
byte-identical to production. This is also the correct choice for a real deployment.

### ⛔ BLOCKER — action required from you

**Docker Desktop is installed but not running.** Start it before Phase 0. Nothing else is blocked.

### Upstream apps (all verified GPL-3.0-compatible, all with a `version-16` branch, all actively pushed 2026-08)

| App | Repo | Latest v16 release | Provides |
|---|---|---|---|
| Frappe Framework | `frappe/frappe` | v16.31.0 | ORM, DocTypes, **workflow engine**, permissions, report builder, print formats, audit trail, REST API, background jobs, file manager |
| ERPNext | `frappe/erpnext` | v16.32.0 | Accounting/GL, budgets, AP/AR, procurement, stock, **fixed assets**, projects, CRM (leads) |
| Education | `frappe/education` | v16.1.0 | 80 DocTypes — students, programs, courses, enrollment, attendance, assessment, fees |
| HRMS | `frappe/hrms` | v16.16.0 | Employee lifecycle, leave, **payroll with Indian PF/ESI/PT/Income-Tax**, recruitment, appraisal |
| India Compliance | `resilient-tech/india-compliance` | v16.8.3 | GSTIN, GST returns, e-invoice, TDS/TCS |
| `frappe_docker` | `frappe/frappe_docker` | MIT | Reproducible containerized deployment |

### External services to procure (not blocking Phase 0, needed by the phase noted)

- Payment gateway merchant account — Razorpay/PayU/CCAvenue (Phase 3)
- SMS provider with **DLT-registered templates** (Phase 3) — DLT registration takes ~2 weeks, start early
- WhatsApp Business API (optional, Phase 3)
- SMTP / transactional email (Phase 0)
- **ABC/NAD API credentials** from the institution's registrar login (Phase 6) — **request in Phase 0, procurement is slow**
- DigiLocker issuer onboarding (Phase 11) — slow, start in Phase 6
- Biometric/RFID device SDK details, if attendance hardware exists (Phase 4)
- Production server: 8 vCPU / 16 GB RAM / 200 GB SSD minimum for ~5,000 students

---

## Coverage Map — what we get free vs. what we build

This is the core of the strategy. **We do not build anything in the "free" column.**

| Flow (from requirements research) | Free from upstream | Built in `shiksha` |
|---|---|---|
| **A. Pre-admission** | ERPNext Lead/CRM; `Student Applicant`, `Student Admission` | Enquiry→lead funnel wiring, entrance-test scoring, **merit list**, **quota/category seat matrix**, admission rounds, waitlist |
| **B. Admission→Enrolment** | `Student`, `Program Enrollment`, `Guardian` | Document-verification workflow, **ABC/APAAR capture+validation**, ID card, **cancellation & refund-slab engine**, lateral entry, TC/migration |
| **C. Academic setup** | `Program`, `Course`, `Academic Year/Term`, `Course Schedule`, `Student Group` | **`Regulation` + `Curriculum Version`** (batch-scoped rules — the single most important missing entity), **L-T-P credits**, **CO/PO mapping**, prerequisites, **elective allocation engine**, faculty workload, **clash-free timetable generator** |
| **D. Teaching/learning** | `Course Topic`, `Article`, `Quiz`, `Course Activity` | Lesson plan + coverage tracking, **course file (NAAC evidence)**, internship/apprenticeship credit, MOOC/SWAYAM transfer, remedial |
| **E. Attendance** | `Student Attendance` + tool, `Student Leave Application` | **OD/duty leave**, medical certificates, **condonation workflow**, **detention/debar engine**, biometric/RFID ingest, threshold alerts to parents |
| **F. Examination** | `Assessment Plan/Criteria/Result`, `Grading Scale` | **The entire examination controller** — exam registration + eligibility, exam fee, **hall ticket**, **QP lifecycle (setter→moderation→encrypted release)**, seating plan, invigilation roster, **UFM/malpractice**, script coding/decoding, evaluation + double valuation, moderation, **revaluation**, **backlog/supplementary cycles**, transcripts |
| **G. Credits / NEP** | — | **Credit ledger**, **ABC/NAD push**, **MEME entry-exit awards**, NCrF levels, credit transfer/equivalence, promotion/detention, max-duration |
| **H. Fee & finance** | `Fee Structure`, `Fee Schedule`, `Fees`, `Payment Record`, full ERPNext GL | **Structure engine (programme×category×quota)**, instalments + late-fee slabs, concessions, **NSP/govt scholarship reconciliation**, **refund slabs**, gateway integration, **dues-blocking hooks** |
| **I. Campus services** | — | **Hostel** (block/room/bed, allotment, in-out, deposit), **mess** (menu, attendance-linked billing), **transport** (route/stop/vehicle/GPS), health, sports, clubs/NSS/NCC, events |
| **J. Discipline & grievance** | Frappe workflow engine | **Anti-ragging (UGC-mandatory)**, **ICC/POSH (confidential)**, grievance redressal with SLA, disciplinary enquiry, SC/ST cell |
| **K. Placement & alumni** | ERPNext CRM for company master | Drive lifecycle, eligibility filters, round tracking, offer capture, **NIRF placement metrics**, alumni module |
| **L. HR & payroll** | **HRMS — the whole flow**: recruitment, service book, leave, payroll, PF/ESI/TDS/Form-16, appraisal | **API/PBAS scoring**, **CAS promotion**, FDP tracking, UGC cadre-ratio reporting |
| **M. Research** | ERPNext Projects for grants | PhD lifecycle (DRC/RAC→thesis→viva), publications, patents, IIC reporting |
| **N. Procurement/assets** | **ERPNext — the whole flow**: indent→RFQ→PO→GRN→invoice, stores, fixed assets + depreciation, AMC | GeM reference fields, lab-chemical expiry, maintenance ticketing UI |
| **O. Accounts** | **ERPNext — the whole flow**: COA, budgets, GL, vouchers, bank rec, financial statements + India Compliance for GST/TDS | Grant-wise utilisation certificates, fund/corpus accounting |
| **P. Compliance** | Frappe report builder, `Version` audit trail | **AISHE export**, **NAAC SSR/AQAR + 7-criteria data**, **NIRF export**, **NBA CO-PO attainment**, IQAC, DigiLocker issuance, RTI log, statutory-body minutes |
| **Q. Exit** | — | No-dues clearance chain, degree generation, convocation, transcript service, verification portal, alumni handoff |
| **Cross-cutting** | **Workflow engine, RBAC, audit, DMS, print/PDF, email, REST API, report builder — all free** | **DPDP consent + retention engine**, parent portal, SMS/WhatsApp DLT adapter, payment gateway adapter, ABC/DigiLocker adapters |

**Estimated custom code: ~20,000 LOC** against ~400,000 LOC of free upstream.

---

## Architecture

```
Docker host
├── mariadb:10.6          (Frappe's database)
├── redis-cache / redis-queue
├── frappe/erpnext:v16    backend + websocket + scheduler + 2 workers
├── nginx                 static assets + reverse proxy
└── site: erp.<college>.ac.in
    └── apps (install order matters):
        frappe → erpnext → hrms → india_compliance → education → shiksha
```

`shiksha` app internal module layout (Frappe modules, each = a workspace in the UI):

```
shiksha/
├── academics/        Regulation, Curriculum Version, Credit, CO-PO, Elective Allocation, Timetable
├── admission/        Merit List, Seat Matrix, Admission Round, Doc Verification, Refund
├── examination/      the exam controller — largest module
├── credits/          Credit Ledger, ABC/NAD, MEME, Credit Transfer
├── finance_ext/      Fee engine extensions, scholarships, dues-blocking
├── campus/           Hostel, Mess, Transport, Health, Sports, Clubs, Events
├── governance/       Anti-ragging, ICC, Grievance, Discipline, Statutory Bodies, IQAC
├── careers/          Placement drives, Offers, Alumni
├── research/         PhD lifecycle, Publications, Patents
├── compliance/       AISHE, NAAC, NIRF, NBA, DigiLocker, RTI
├── privacy/          DPDP consent, retention, erasure, data-subject requests
└── integrations/     payment gateway, SMS/DLT, WhatsApp, ABC API, biometric
```

### Two architectural rules that must not be broken

1. **Never patch upstream apps.** All customization goes in `shiksha` via hooks, Custom Fields,
   and Server Scripts. The moment we fork `education`, we lose upgrades forever — this is the
   documented #1 cause of "misaligned, overly customized, and costly" higher-ed ERP outcomes.
2. **Every academic rule resolves through `Regulation`.** A 2023-batch student is graded by
   2023 rules in 2029. No grading, promotion, or credit logic may hardcode a rule.

---

## Execution Steps

Legend: `[PARALLEL]` = independent, may run concurrently. `[SERIES]` = strict order, full
checkpoint between each. Every checkpoint = error check → Pass 1 (synthetic) → Pass 2 (real
data) → no regressions.

---

### Phase 0 — Environment & Skeleton
**Goal:** a running ERPNext v16 site with all five upstream apps installed and an empty
`shiksha` app registered, reproducible from a clean machine in one command.

`[SERIES]`
- [ ] 0.1 — Confirm Docker Desktop is running (`docker info` exits 0)
- [ ] 0.2 — Clone `frappe/frappe_docker` into `shiksha-erp/infra/`
- [ ] 0.3 — Write `infra/compose.dev.yml` pinning `frappe/erpnext:v16`, mariadb 10.6, redis, nginx
- [ ] 0.4 — Write `infra/.env.example` (site name, DB root pw, admin pw, SMTP) + `.gitignore` for `.env`
- [ ] 0.5 — `docker compose up -d`; verify all containers healthy
- [ ] 0.6 — Create site `erp.localhost`; install `erpnext`
- [ ] 0.7 — Install `hrms`, `india_compliance`, `education` (in that order)
- [ ] 0.8 — Scaffold custom app: `bench new-app shiksha`; set GPLv3 licence header
- [ ] 0.9 — Create the 12 module directories listed in Architecture
- [ ] 0.10 — `git init`; commit; add `.github/workflows/ci.yml` (lint + `bench run-tests --app shiksha`)
- [ ] 0.11 — Write `Makefile`: `make up`, `make down`, `make shell`, `make test`, `make migrate`, `make backup`
- [ ] 0.12 — Write `README.md` with the from-clean-machine setup path
- [ ] 0.13 — **Request ABC/NAD API credentials and DigiLocker issuer onboarding now** (long lead time)
- [ ] 0.14 — **Start SMS DLT template registration now** (~2 week lead time)

**Checkpoint 0:**
- Pass 1: `docker compose ps` shows all healthy; `bench --site erp.localhost list-apps` returns all 6; CI green on an empty test
- Pass 2: log in to the Desk UI at `http://erp.localhost:8080` as Administrator; Education, HR, Accounting, and Shiksha workspaces all render; create one throwaway `Student` record through the UI and confirm it saves

---

### Phase 1 — Institution & Academic Spine
**Goal:** the versioned academic structure everything else depends on. **This phase is
load-bearing for all 13 that follow — no shortcuts.**

`[SERIES]`
- [ ] 1.1 — DocType `Institution Profile`: name, AISHE code, affiliating university, type (affiliated/autonomous/deemed), NAAC grade, establishment year, campuses
- [ ] 1.2 — DocType `Campus`, `Building`, `Room Extension` (capacity, type: classroom/lab/exam-hall)
- [ ] 1.3 — DocType **`Regulation`**: code (e.g. `R23`), effective-from academic year, min/max credits, grading scale link, promotion rules, max programme duration, attendance-shortage threshold, condonation limits
- [ ] 1.4 — DocType **`Curriculum Version`**: Program + Regulation + semester-wise course list with L-T-P-credits per course
- [ ] 1.5 — Custom Fields on `Course`: `lecture_hours`, `tutorial_hours`, `practical_hours`, `credits`, `course_type` (core/elective/open-elective/minor/audit/mandatory-non-credit), `ncrf_level`
- [ ] 1.6 — DocType `Course Prerequisite` (child table on Course)
- [ ] 1.7 — DocTypes `Program Outcome` (PO/PSO), `Course Outcome` (CO), `CO PO Mapping` with correlation strength 1–3
- [ ] 1.8 — Custom Field on `Program Enrollment`: link to `Regulation` — **stamped at admission, immutable thereafter**
- [ ] 1.9 — `shiksha/academics/regulation_resolver.py`: single API `get_rule(student, rule_name, as_of_date)` — the ONLY way any module reads an academic rule
- [ ] 1.10 — Validation hooks: credits must equal Curriculum Version total; prerequisites must be acyclic
- [ ] 1.11 — Fixtures: seed one complete real regulation (B.Tech CSE R23, 8 semesters, ~50 courses)

**Checkpoint 1:**
- Pass 1: pytest — two students on R21 and R23 resolve *different* pass marks and *different* max-duration from `get_rule()`; a cyclic prerequisite is rejected; a Curriculum Version whose credits don't sum is rejected
- Pass 2: enter one **real** B.Tech CSE curriculum from the college's actual syllabus PDF end-to-end through the UI; total credits must match the printed syllabus exactly; print the CO-PO matrix and compare against the department's existing NBA document

---

### Phase 2 — Admission
**Goal:** run a complete admission cycle from enquiry to enrolled student.

`[SERIES]`
- [ ] 2.1 — Wire ERPNext `Lead` → `Student Applicant` conversion; enquiry web form
- [ ] 2.2 — DocType `Seat Matrix`: Program × Academic Year × category (GEN/SC/ST/OBC/EWS/PwD) × quota (state/management/NRI) × sanctioned seats
- [ ] 2.3 — Custom Fields on `Student Applicant`: category, quota, entrance exam + rank/score, APAAR ID, physical-disability flag
- [ ] 2.4 — DocType `Entrance Score Import` — CSV/API ingest from CUET/state-CET
- [ ] 2.5 — DocType `Merit List` + generator: category-wise ranking with configurable tie-break chain
- [ ] 2.6 — DocType `Admission Round` + `Seat Allotment`: round-wise release, waitlist movement, seat return on cancellation
- [ ] 2.7 — DocType `Document Verification` with checklist child table, verifier sign-off, defect list, conditional-admission deadline
- [ ] 2.8 — DocType `APAAR Validation Log` — capture + format-validate APAAR ID (live API call deferred to Phase 6)
- [ ] 2.9 — DocType `Admission Cancellation` + **refund-slab engine** (date-banded % refund, reads from Regulation)
- [ ] 2.10 — DocType `Lateral Entry Credit Mapping` — external course → internal course equivalence with credit award
- [ ] 2.11 — Applicant portal pages: apply, upload documents, pay, track status, accept offer
- [ ] 2.12 — Workflow: `Applied → Verified → Merit-listed → Allotted → Fee-paid → Enrolled`, with `Rejected`/`Cancelled` terminal states

**Checkpoint 2:**
- Pass 1: pytest — 100 synthetic applicants against a 60-seat matrix produce category-wise allotments that exactly honour reservation percentages; a cancellation returns the seat to the correct category pool; refund on day 15 vs day 45 yields the two different slab amounts
- Pass 2: run **last year's real applicant list** (anonymised) through the merit-list generator and diff the output against the merit list the college actually published. Any discrepancy is a bug in our rules, not in theirs — investigate every one.

---

### Phase 3 — Fee Engine & Student Finance
**Goal:** correct money. Highest blast radius of any module — errors here are visible to
parents within hours.

`[SERIES]`
- [ ] 3.1 — DocType `Fee Structure Rule`: Program × Batch × Category × Quota × hosteller-flag → component amounts
- [ ] 3.2 — DocType `Fee Instalment Plan` + late-fee slab child table
- [ ] 3.3 — DocType `Fee Concession` (staff-ward, sibling, merit, management) with approval workflow
- [ ] 3.4 — DocType `Scholarship`: scheme master, NSP/state-portal application ID, sanctioned vs received, disbursement reconciliation
- [ ] 3.5 — `integrations/payment_gateway.py` — adapter interface + Razorpay implementation, webhook handler, idempotency keys
- [ ] 3.6 — DocType `Payment Reconciliation Queue` for unmapped bank credits
- [ ] 3.7 — DocType `Fee Refund` reusing the Phase-2 slab engine; caution-deposit release at exit
- [ ] 3.8 — `finance_ext/dues.py`: `has_blocking_dues(student)` — consumed by exam registration, result release, hostel allotment, no-dues
- [ ] 3.9 — Scheduled job: due-date reminders via SMS/email at T-7, T-1, T+1, T+7
- [ ] 3.10 — Reports: collection summary, defaulter list, ageing analysis, category-wise concession cost
- [ ] 3.11 — Verify every fee posting produces a correct ERPNext GL entry against the right cost centre

**Checkpoint 3:**
- Pass 1: pytest — SC-category hosteller under management quota gets the exact expected total; a ₹50,000 payment across a 3-instalment plan with one late instalment computes the exact late fee; a gateway webhook delivered twice creates exactly one payment
- Pass 2: reconcile one **real historical month** of the college's fee collection — our computed receivables vs. their actual bank statement. Must match to the rupee. Investigate every paisa of variance.

---

### Phase 4 — Attendance
`[SERIES]`
- [ ] 4.1 — Extend `Student Attendance` with period-wise marking; lab/tutorial distinct from lecture
- [ ] 4.2 — DocType `Duty Leave (OD)` — sports/NCC/conference, with approval workflow and auto-adjust
- [ ] 4.3 — Extend `Student Leave Application` with medical-certificate attachment + verification
- [ ] 4.4 — DocType `Attendance Condonation` — application → HoD → Principal → fee → approval
- [ ] 4.5 — `academics/detention.py` — shortage detection reading thresholds from `Regulation`; produces `Exam Debar List`
- [ ] 4.6 — `integrations/biometric.py` — adapter interface + CSV/push ingest (device-specific impl once hardware is identified)
- [ ] 4.7 — Scheduled alerts to student + parent + mentor at 75% and 65%
- [ ] 4.8 — Faculty bulk-marking UI; mobile-friendly; offline-tolerant

**Checkpoint 4:**
- Pass 1: pytest — student at 71% with 3 approved OD days crosses to 76%; a student at 60% appears on the debar list; condonation approval removes them
- Pass 2: import one **real semester** of attendance from the existing system; our computed shortage list must match the college's actual detention list. Every mismatch investigated.

---

### Phase 5 — Examination Controller ⚠️ LARGEST & HIGHEST-RISK PHASE
**Goal:** the complete exam lifecycle. Highest security sensitivity, zero error tolerance,
maximum institutional politics.

**⚠️ Before starting: resolve Assumption 5** — obtain the affiliating university's exam data
format, or confirm autonomous status. The phase cannot be correctly specified without this.

`[SERIES]`
- [ ] 5.1 — DocType `Exam Session` (Regular/Supplementary/Special) × academic term
- [ ] 5.2 — DocType `Exam Registration` — eligibility gate: attendance (Phase 4) + dues (Phase 3) + backlog count (Regulation)
- [ ] 5.3 — Exam-fee computation: regular + per-backlog-paper + late fee; posts to GL
- [ ] 5.4 — `Hall Ticket` print format with photo, QR verification, subject list
- [ ] 5.5 — DocType `Question Paper` — setter appointment, blueprint/Bloom's mapping, **encrypted attachment**, moderation workflow, **time-locked release**, full access audit
- [ ] 5.6 — DocType `Exam Seating Plan` — room allocation, no two same-subject candidates adjacent
- [ ] 5.7 — DocType `Invigilation Duty` roster with conflict avoidance
- [ ] 5.8 — DocType `Exam Attendance` — present/absent per candidate per paper
- [ ] 5.9 — DocType `UFM Case` — registration → committee → hearing → penalty → permanent record
- [ ] 5.10 — DocType `Answer Script` — dummy-number coding/decoding, packet tracking
- [ ] 5.11 — DocType `Evaluation` — examiner allotment, per-script marks, double valuation, third-valuation trigger on variance threshold
- [ ] 5.12 — DocType `Moderation` — committee adjustments with mandatory reason and full audit
- [ ] 5.13 — DocType `Revaluation Request` — photocopy / retotal / revaluation, fee, revised result, mark-change audit
- [ ] 5.14 — Backlog/arrear registration flowing into the supplementary `Exam Session`
- [ ] 5.15 — Security hardening: field-level permissions on QP and marks; **immutable audit log of every mark change (who, when, from, to)**; MFA enforced for Controller-of-Examinations role

**Checkpoint 5:**
- Pass 1: pytest — a debarred student cannot register; a student with dues cannot register; double valuation differing by >15% triggers third valuation; a mark edit after result publication is blocked and logged; a QP is unreadable before its release timestamp even by an Administrator-role user
- Pass 2: dry-run one **complete real past exam cycle** — registration through result — for a single department, and diff every computed mark and grade against the official published record. Zero discrepancies permitted before proceeding.

---

### Phase 6 — Results, Credit Ledger & NEP
`[SERIES]`
- [ ] 6.1 — `Result Processing` engine — internal + external weighting, grade from `Regulation`'s scale, SGPA/CGPA, class/division
- [ ] 6.2 — DocType `Credit Ledger Entry` — immutable, append-only, one row per credit earned/transferred/revoked
- [ ] 6.3 — `Grade Card` / `Marksheet` print formats with QR verification
- [ ] 6.4 — DocType `Credit Transfer` — MOOC/SWAYAM/NPTEL/other-institution with equivalence approval
- [ ] 6.5 — DocType `Programme Exit` — MEME: Certificate(1yr)/Diploma(2yr)/Degree(3yr)/Hons(4yr) with credit-threshold validation
- [ ] 6.6 — DocType `Re-entry` — restore credits from ABC on return
- [ ] 6.7 — `integrations/abc_nad.py` — APAAR verification + credit push to NAD-ABC; retry queue; per-student push audit
- [ ] 6.8 — NCrF level assignment per credit
- [ ] 6.9 — Promotion/detention engine + max-duration enforcement, all rules from `Regulation`
- [ ] 6.10 — `Transcript` generation — consolidated, term-wise, and WES-compatible formats

**Checkpoint 6:**
- Pass 1: pytest — SGPA/CGPA computed for 50 synthetic students match hand-calculated values exactly; a student exiting at 2 years with 88 credits gets a Diploma, at 76 credits gets nothing; credit ledger rejects any UPDATE
- Pass 2: process one **real semester's** results for one department; diff SGPA/CGPA against officially published grade cards — zero tolerance. Then push a **test batch** to the ABC sandbox and confirm acceptance.

---

### Phase 7 — Campus Services
`[PARALLEL]` — three independent module groups, no shared state
- [ ] 7.A **Hostel** (agent 1) — Block/Room/Bed masters, allotment (merit/preference/lottery), room change, in-out register, curfew/late-entry, visitor log, warden roster, inspection, maintenance complaints, vacating + deposit refund
- [ ] 7.B **Mess** (agent 2) — menu planning, attendance-linked or fixed billing, vendor management, feedback; bills flow to Phase-3 fee engine
- [ ] 7.C **Transport** (agent 3) — routes, stops, vehicle + driver masters, seat allotment, route-wise fee, document-expiry alerts (fitness/insurance/permit), GPS webhook ingest, parent notifications
- [ ] 7.D — *(serial, after A/B/C)* Health centre, sports facility booking, clubs/NSS/NCC, event management. **Health records get restricted permissions from the outset** (DPDP)

**Checkpoint 7:**
- Pass 1: pytest per module — hostel double-allotment of one bed is rejected; mess bill for 22 attended days at ₹120/day is exact; transport fee varies correctly by stop distance
- Pass 2: load the college's **real hostel occupancy** and **real bus routes**; warden and transport-in-charge each perform one real day's operations in the system and sign off

---

### Phase 8 — Governance, Discipline & Statutory Committees
`[SERIES]` — legally mandated; correctness over speed
- [ ] 8.1 — DocType `Grievance` — UGC-mandated redressal with SLA timers, escalation ladder, ombudsperson referral
- [ ] 8.2 — DocType `Anti-Ragging Affidavit` (student + parent, annual) + `Ragging Complaint` with committee workflow + UGC compliance report
- [ ] 8.3 — DocType `ICC Case` (POSH) — **confidential by design**: restricted role, no list-view exposure, encrypted attachments, annual statutory report
- [ ] 8.4 — DocType `Disciplinary Case` — enquiry → committee → hearing → penalty → appeal
- [ ] 8.5 — DocTypes for SC/ST cell, minority cell, equal-opportunity cell, PwD support
- [ ] 8.6 — DocType `Statutory Body Meeting` — Governing Body / Academic Council / BoS / Finance Committee: agenda, minutes, resolutions, action-taken tracking
- [ ] 8.7 — DocType `IQAC Activity` feeding the Phase-10 AQAR

**Checkpoint 8:**
- Pass 1: pytest — a non-ICC-member (including a System Manager) cannot read an ICC case by any route: list view, report view, REST API, or `frappe.get_doc`. This test is mandatory and must be adversarial.
- Pass 2: the actual ICC presiding officer and grievance officer each walk one real (redacted) historical case through the system and confirm the confidentiality model is acceptable to them

---

### Phase 9 — Placements & Alumni
`[PARALLEL]`
- [ ] 9.A — Company master (ERPNext Customer), JD posting, eligibility filters, drive scheduling, round tracking, offer capture, policy enforcement (1-offer/dream-offer rules), **NIRF metrics: median salary, placement %, higher-studies count**
- [ ] 9.B — Alumni auto-conversion at graduation, directory, verification-request service (paid), donations, mentorship, employer-feedback capture for NAAC

**Checkpoint 9:**
- Pass 1: pytest — a student with 2 backlogs is filtered out of a drive requiring zero; median-salary calculation matches hand-computed value on a synthetic offer set
- Pass 2: load the **real last-3-years placement data**; our NIRF metric outputs must match the college's actual NIRF submission

---

### Phase 10 — Compliance & Accreditation Reporting
**Goal:** one-click generation of every statutory submission from live data.
`[PARALLEL]` — each export is independent
- [ ] 10.A — **AISHE** export in the portal's exact required format
- [ ] 10.B — **NAAC** — 7-criteria data pack, SSR inputs, AQAR, QIF metrics
- [ ] 10.C — **NIRF** — TLR / RP / GO / OI / Perception parameter export
- [ ] 10.D — **NBA** — CO/PO attainment computation from Phase-1 mapping + Phase-6 results, gap analysis, course files
- [ ] 10.E — UGC/AICTE returns, mandatory web disclosure page, RTI request log
- [ ] 10.F — *(serial, after all)* **Cross-framework consistency validator** — NAAC's DVV cross-checks SSR claims against AISHE and NIRF; this report flags any figure that differs across the three exports **before** submission
- [ ] 10.G — DigiLocker issuance of degrees/marksheets/TCs

**Checkpoint 10:**
- Pass 1: pytest — CO/PO attainment on a synthetic cohort with known marks matches hand-computed attainment; the consistency validator catches a deliberately injected mismatch between the AISHE and NIRF student count
- Pass 2: generate the **current year's real AISHE submission** from live data and diff against what the college submitted manually. Every difference is either our bug or an error in their manual submission — both are valuable findings.

---

### Phase 11 — DPDP Compliance & Security Hardening
**Goal:** legally defensible handling of personal data. **Not optional — statutory.**
`[SERIES]`
- [ ] 11.1 — DocType `Consent Record` — purpose-specific, granular, timestamped, withdrawable. **Not a bundled checkbox** (explicitly insufficient under the Rules)
- [ ] 11.2 — **Verifiable parental consent** for students under 18 — DigiLocker or govt-ID or payment-signal verification
- [ ] 11.3 — DocType `Data Retention Policy` per document class + scheduled erasure job triggered at graduation/transfer
- [ ] 11.4 — Data-subject request handling: access, correction, erasure, withdrawal
- [ ] 11.5 — Sensitive-category access control: health, counselling, ICC, caste, disability — restricted roles, encrypted at rest, **read access itself logged**
- [ ] 11.6 — Breach detection + notification workflow; named Grievance Officer
- [ ] 11.7 — Privacy notice pages; confirm **no tracking/profiling/targeted advertising** anywhere in the codebase
- [ ] 11.8 — Security: MFA for all privileged roles, TLS, secrets in env not code, rate limiting, `bench` security audit, dependency CVE scan
- [ ] 11.9 — Backup: automated encrypted nightly + offsite, with a **documented and rehearsed restore drill**

**Checkpoint 11:**
- Pass 1: pytest — erasure job removes exactly the right records after retention expiry and nothing else; consent withdrawal immediately blocks the dependent processing path; a role without health permission is denied via UI, report, and REST API
- Pass 2: **restore the full backup onto a clean host and verify integrity.** A backup that has never been restored is not a backup. Then run a live data-subject erasure request end to end.

---

### Phase 12 — Data Migration
**Goal:** real historical data in, without corrupting it. Research identifies poor migration
as a primary cause of ERP project failure, and a college cannot go offline to do it.
`[SERIES]`
- [ ] 12.1 — Discovery: inventory every legacy source (Excel, Tally, existing portal DB, paper), volume, date range, owner
- [ ] 12.2 — Profile data quality: nulls, duplicates, encoding, date formats, orphaned references. **Publish the defect report before writing any importer**
- [ ] 12.3 — Write reversible ETL scripts per entity, in dependency order: departments → programs → regulations → curricula → employees → students → enrollments → attendance → results → credit ledger → fees → GL opening balances
- [ ] 12.4 — Dry-run into a scratch site; reconcile counts and control totals per entity
- [ ] 12.5 — Remediation pass with the data owners on every defect
- [ ] 12.6 — Rehearse the full migration twice, timed, with rollback
- [ ] 12.7 — Cutover runbook with a go/no-go checklist and rollback trigger

**Checkpoint 12:**
- Pass 1: reconciliation report — row counts and financial control totals match source exactly for every entity
- Pass 2: 20 randomly sampled **real** students verified field-by-field against their physical/legacy records by registry staff, signed off

---

### Phase 13 — UAT, Training & Go-Live
`[SERIES]`
- [ ] 13.1 — UAT scripts per role (12 roles), executed by the actual staff who will use them
- [ ] 13.2 — Role-based training sessions + printed quick-reference cards per role
- [ ] 13.3 — Identify and train one power-user champion per department
- [ ] 13.4 — Production deployment: compose.prod, TLS, nginx hardening, monitoring, log aggregation
- [ ] 13.5 — Load test at realistic peak — **result-day is the worst case: the entire student body in 10 minutes**. Also test fee-deadline day and counselling day
- [ ] 13.6 — Parallel run: one full month operating both old and new systems, reconciled daily
- [ ] 13.7 — Go-live; hypercare support window; defect triage process
- [ ] 13.8 — Handover documentation: admin runbook, backup/restore procedure, escalation contacts

**Checkpoint 13:**
- Pass 1: load test sustains peak concurrent users at acceptable p95 latency without errors
- Pass 2: **one full month of parallel running with zero unexplained reconciliation differences.** This is the real acceptance criterion.

---

## Final Verification

- [ ] Every phase checkpoint passed, both passes
- [ ] Full regression suite green; CI green on main
- [ ] Every flow A–Q from the requirements research either implemented or explicitly documented as deferred with a reason
- [ ] Zero upstream app files modified (`git diff` against pristine `education`/`erpnext`/`hrms` is empty)
- [ ] Statutory: DPDP consent + retention live; anti-ragging, ICC, grievance operational
- [ ] Compliance exports reconcile across AISHE/NAAC/NIRF
- [ ] Backup restore drill completed and documented
- [ ] All 12 roles trained and signed off
- [ ] One month parallel run reconciled

---

## Risks & Open Questions

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | **Affiliated vs autonomous exam model unresolved** (Assumption 5) | Phase 5 — the largest phase — cannot be correctly specified | **Resolve before Phase 5 starts.** Obtain the university's exam data format in Phase 0 |
| R2 | `frappe/education` v16 is at release **v16.1.0** — young on this branch | Possible upstream bugs/API churn in a core dependency | Pin exact version; wrap education APIs behind our own thin layer; contribute fixes upstream rather than forking |
| R3 | **Change management** — research finds this outranks technical causes in higher-ed ERP failure | Project rejected by staff regardless of code quality | Phase 13 champions + parallel run; involve registry/exam staff from Phase 1, not Phase 13 |
| R4 | Legacy data quality unknown until Phase 12 | Schedule slip; corrupted history | Pull Phase 12.1–12.2 discovery forward to run in parallel with Phase 1 |
| R5 | ABC/NAD and DigiLocker credential procurement is institutionally slow | Blocks Phase 6 and 10.G | Requested in Phase 0.13; build against sandbox/mocks meanwhile |
| R6 | GPLv3 obligation | Blocks closed-source resale | Confirmed acceptable (Assumption 2). In-house use carries no obligation |
| R7 | Over-customization — the documented failure mode of higher-ed ERPs | Loss of upgrade path, spiralling cost | Architectural Rule 1 enforced by a CI check that fails if upstream app files are modified |
| R8 | Scope is genuinely large (14 phases) | Fatigue, half-finished modules | Each phase is independently shippable. Phases 0–6 alone constitute a usable academic ERP; 7–13 extend it |
| R9 | Timetable generation is NP-hard under NEP flexible credits | Phase 1.x may overrun | Ship constraint-solver-assisted manual generation first; full automation is an enhancement, not a blocker |
| R10 | Node 25 on host vs Frappe's supported LTS | Local build inconsistency | Docker isolates it entirely; never build assets on the host |

### Questions I need answered

1. **Affiliated or autonomous?** (R1 — blocks Phase 5)
2. **Which institution, which affiliating university?** Determines exam formats, regulation codes, and AISHE/NAAC identifiers
3. **Approximate scale?** Student count, staff count, number of programs — drives infrastructure sizing
4. **Is `shiksha` an acceptable app name?** Painful to change after Phase 0
5. **What legacy systems hold the existing data?** Feeds R4 discovery

None of these block Phase 0. Questions 1–3 must be answered before Phase 5.
