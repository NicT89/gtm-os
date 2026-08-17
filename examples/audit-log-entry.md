# Audit log entry — 2026-08-14

SYNTHETIC EXAMPLE. Format anchor for the audit-log append every skill ends with.
Real audit logs live in the operator's own storage, never in this repo.

---

## Run: gtm-signal-scan — hiring motion — 2026-08-14

**Operator:** [name] · **Duration:** 38m · **Credits:** 15 (est. 15)

### Findings

**F-2026-08-14-01 — DEFECT — list membership silently failed**
Two accounts (Harbor Labs, Tidewater AI) reported success on the add-to-list call
but did not appear in `label_ids` on re-read. `cached_count` on the list had
incremented, which is what made it look successful.
→ **Gate added:** verify membership on the record's `label_ids` after every list
add; never trust `cached_count`. Now step 3 of the skill.
→ Status: **permanent gate, shipped in v1.0.0**

**F-2026-08-14-02 — DEFECT — credit spent on unreachable contact**
D. Moreau (Cobalt Systems, CTO) matched at 1 credit and returned no sendable
address. Role fit was strong, reachability flag was `unavailable` before the spend
and was visible for free at search time.
→ **Gate added:** rank on reachability flags before spending; never match a T4
candidate. Now step 4b.
→ Status: **permanent gate, shipped in [Unreleased]**

**F-2026-08-14-03 — OBSERVATION — size band edge**
Tidewater AI at 140 employees sits at the top of the 11-200 band but behaves like a
larger company (established marketing function, 2 layers above the signal role).
Not a defect. Worth watching whether 11-120 is the better band.
→ Status: **open — revisit at monthly rubric recalibration**

### Send-risk carried forward

- S. Lindqvist (Northwind) — catch-all
- P. Anand (Cobalt) — email/company domain mismatch

### Gate results

| Gate | Result |
|---|---|
| Credit spend approved before enrichment | PASS |
| No enrollment performed by the skill | PASS |
| "[Claude]" naming on created assets | PASS |
| Human assets unedited | PASS |

---

## Run: outreach-audit — [Claude] Hiring Signal Q3 — 2026-08-14

**Verdict: SHIP AFTER FIXES**

| # | Severity | Finding | Violates | Fix |
|---|---|---|---|---|
| 1 | BLOCKING | Email 3 uses `{{<prefix> Blueprint}}` without the object prefix — renders as literal text | Merge token rules | `{{contact.<prefix> Blueprint}}` |
| 2 | BLOCKING | Excluded contact stages empty (API-created sequence) — replied and do-not-contact stages can re-enroll | Config check 2 | Set exclusions in UI before activation |
| 3 | HIGH | Email 2 opener would read identically for any Series A company | Five-point checklist, falsifiability | Anchor to the JD's named tooling |
| 4 | MEDIUM | Two variables changed between A/B variants (subject *and* opener angle) | A/B discipline | Split into two sequential tests, angle first |
| 5 | LOW | Wrong Context Center product auto-attached on creation | Config check 1 | Reattach correct product |

Findings 1 and 2 block activation. 3 must be fixed before the cohort sends; 4 and 5
can follow.
