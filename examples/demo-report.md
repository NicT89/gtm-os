# GTM OS demo run

> **Run mode: SIMULATED.** Synthetic accounts, real decision logic. No connector was called, no credit was spent, nothing was written to a CRM or a base, and nothing was sent. Companies and people are invented, on `.example` domains. Scoring used: **ILLUSTRATIVE demo parameters**. As of 2026-09-01.

Every table row carries a label. The four labels are defined in the plugin root's `references/run-manifest.md`:

| What the row is | Label |
|---|---|
| Synthetic input, real engine logic | SIMULATED |
| A hand-written stand-in for an API or model response | FIXTURE |
| Your real config over synthetic input, no spend | PREVIEW |
| Real calls against your own tools | LIVE |

## Headline

12 source records became 10 accounts; 5 earned enrichment, 8 people earned a match credit, and **5 contact(s) reached the pre-send review queue**. **0 sent. 0 credits spent.** The same run live would state a cap of **32 Apollo credits** before spending and, at this ranking, spend **18**.

| Stage | Count | Label |
|---|---|---|
| Source records | 12 | SIMULATED |
| Rejected at intake | 1 | SIMULATED |
| Unique accounts | 10 | SIMULATED |
| Excluded before any spend | 3 | SIMULATED |
| Held: motion could not be assigned | 1 | SIMULATED |
| Pre-scored | 6 | SIMULATED |
| Enriched (pre-score Excellent + Good) | 5 | SIMULATED |
| People ranked | 12 | SIMULATED |
| People matched | 8 | SIMULATED |
| Passed the field gate | 5 | SIMULATED |
| Ready for pre-send review | 5 | SIMULATED |
| Sent | 0 | SIMULATED |

## 1. Intake and dedupe

| Account | Domain | Signals | Route | Label |
|---|---|---|---|---|
| Northwind Analytics | northwind.example | hiring (2026-08-25) | in CRM: update, never create | SIMULATED |
| Cobalt Systems | cobalt.example | hiring (2026-08-28) + funding (2026-06-30) | net new: create | SIMULATED |
| Harbor Labs | harbor.example | funding (2026-07-10) | net new: create | SIMULATED |
| Tidewater AI | tidewater.example | hiring (2026-08-20) | net new: create | SIMULATED |
| Meridian Retail | meridian.example | hiring (2026-07-12) | net new: create | SIMULATED |
| Foundry GTM Partners | foundry.example | hiring (2026-08-22) | net new: create | SIMULATED |
| Kestrel Staffing | kestrel.example | hiring (2026-08-18) | net new: create | SIMULATED |
| Vantage Global | vantage.example | hiring (2026-08-26) | net new: create | SIMULATED |
| Lumen Freight | lumen.example | hiring (date unknown) | net new: create | SIMULATED |
| Quarry Works | quarry.example | funding (2026-01-15) | net new: create | SIMULATED |
| Unnamed listing | (none) |  | rejected: no domain: identity cannot be resolved | SIMULATED |

*Live:* the company search costs one credit; its `accounts` array is what is already in the CRM and its `organizations` array is net new. Account creation does not dedupe, so this split is the only thing standing between a run and duplicate records.

## 2. Exclusions and motion (free)

| Account | GTM team | Hiring GTM | Motion | Decision | Label |
|---|---|---|---|---|---|
| Foundry GTM Partners | 0 | yes | (not routed) | excluded: category: competitor | SIMULATED |
| Kestrel Staffing | 0 | yes | (not routed) | excluded: category: staffing_firm | SIMULATED |
| Vantage Global | 3 | yes | (not routed) | excluded: established GTM team of 3 (this signal type excludes above 1) | SIMULATED |
| Lumen Freight | unknown | yes | none | held: unknown input: gtm_leader_tenure_months_max, has_gtm_team; run the free people search by organization id before routing (not found is not absent) | SIMULATED |
| Northwind Analytics | 0 | yes | first-gtm-hire | criteria met: has_gtm_team=False, hiring_gtm=True | SIMULATED |
| Cobalt Systems | 0 | yes | first-gtm-hire | criteria met: has_gtm_team=False, hiring_gtm=True | SIMULATED |
| Harbor Labs | 0 | no | founder-direct | criteria met: has_gtm_team=False, hiring_gtm=False | SIMULATED |
| Tidewater AI | 1 | yes | new-leader | criteria met: gtm_leader_tenure_months_max=9, has_gtm_team=True | SIMULATED |
| Meridian Retail | 1 | yes | team-expansion | criteria met: has_gtm_team=True, hiring_gtm=True | SIMULATED |
| Quarry Works | 0 | no | founder-direct | criteria met: has_gtm_team=False, hiring_gtm=False | SIMULATED |

*Live:* one free people search per account answers both questions at once, which is why exclusion runs before enrichment and costs nothing.

## 3. Pre-score, pass 1 (free, out of 55)

| Account | Motion | Pre-score | Pre-tier | Unknown inputs | Next | Label |
|---|---|---|---|---|---|---|
| Northwind Analytics | first-gtm-hire | 55 | Excellent | none | enrich | SIMULATED |
| Cobalt Systems | first-gtm-hire | 40 | Excellent | geography | enrich | SIMULATED |
| Harbor Labs | founder-direct | 45 | Excellent | none | enrich | SIMULATED |
| Tidewater AI | new-leader | 45 | Excellent | none | enrich | SIMULATED |
| Meridian Retail | team-expansion | 31 | Good | none | enrich | SIMULATED |
| Quarry Works | founder-direct | 22 | Fair | none | account record only, no spend | SIMULATED |

A pre-score is never reported as a final score. An unknown input scores 0 and is named, so a gap is visible instead of reading as a weak account.

## 4. Credit statement, made before any spend

| Line item | Units | Credits each | Subtotal | Label |
|---|---|---|---|---|
| Company search | 1 | 1 | 1 | SIMULATED |
| Organization enrichment (pre-score Excellent + Good) | 5 | 1 | 5 | SIMULATED |
| Job postings (hiring accounts being enriched) | 4 | 1 | 4 | SIMULATED |
| People match (quota cap at pre-score tier) | 22 | 1 | 22 | SIMULATED |
| **Cap stated to the operator** |  |  | **32** | SIMULATED |
| Would spend at this ranking |  |  | 18 | SIMULATED |
| Actually spent |  |  | 0 | SIMULATED |

Per-unit costs are read from the plugin root's `references/apollo-credit-costs.md` at run time. The people line is capped at each account's quota; ranking then spends less. Run-cost tally: `Apollo credits: 0 | Actor USD: 0 | Firecrawl credits: 0 | Status: final`.

*Live:* the run stops here and asks. Credit spend is a named human gate.

## 5. Enrichment and the full score (out of 100)

Enrichment values are FIXTURES standing in for org enrichment and the job postings call; the scoring over them is real.

| Account | motion_fit | signal_age | budget_signal | geography | stage_and_funding | archetype_fit | stack_overlap | warm_path | Score | Tier | Label |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Northwind Analytics | 15 | 15 | 15 | 10 | 20 | 10 | 10 | 0 | 95 | Excellent | SIMULATED |
| Cobalt Systems | 15 | 15 | 10 | 10 | 14 | 10 | 10 | 5 | 89 | Excellent | SIMULATED |
| Harbor Labs | 12 | 13 | 10 | 10 | 20 | 0 (unknown) | 5 | 0 | 70 | Good | SIMULATED |
| Tidewater AI | 15 | 15 | 5 | 10 | 16 | 6 | 0 | 0 | 67 | Good | SIMULATED |
| Meridian Retail | 8 | 3 | 10 | 10 | 8 | 3 | 0 | 0 | 42 | Below Fair | SIMULATED |

## 6. People: rank on reachability before spending

| Account | Person | Title | Email flag | Reach | Role | Decision | Label |
|---|---|---|---|---|---|---|---|
| Northwind Analytics | A. Reyes | CEO & Co-founder | verified | T2 | priority 1 ('ceo') | match: ranked 1 of quota 5 | SIMULATED |
| Northwind Analytics | J. Okafor | Head of Growth | verified | T1 | priority 3 ('growth') | match: ranked 3 of quota 5 | SIMULATED |
| Northwind Analytics | S. Lindqvist | Co-founder & COO | catch_all | T3 | priority 1 ('founder') | match: ranked 2 of quota 5; then held: catch-all enrollment gate (no policy recorded) | SIMULATED |
| Northwind Analytics | R. Singh | Founding Account Executive | verified | T2 | Founding <role>: GTM individual contributor, not a founder | match: ranked 4 of quota 5 | SIMULATED |
| Northwind Analytics | D. Park | Board Member | verified | T2 | skipped: 'board' is not a selection target | skip | SIMULATED |
| Cobalt Systems | M. Duarte | CEO | verified | T1 | priority 1 ('ceo') | match: ranked 1 of quota 3 | SIMULATED |
| Cobalt Systems | P. Anand | VP Marketing | verified | T2 | priority 3 ('marketing') | match: ranked 2 of quota 3 | SIMULATED |
| Cobalt Systems | L. Chen | Chief of Staff | unavailable | T4 | priority 2 ('chief of staff') | hold: T4: no match credit; LinkedIn-only or referral path | SIMULATED |
| Cobalt Systems | D. Moreau | CTO | verified | T2 | skipped: not in the selection priority | skip | SIMULATED |
| Harbor Labs | K. Whitfield | Founder | verified | T2 | priority 1 ('founder') | match: ranked 1 of quota 2 | SIMULATED |
| Tidewater AI | T. Nakamura | CEO | verified | T2 | priority 1 ('ceo') | match: ranked 1 of quota 2 | SIMULATED |
| Tidewater AI | E. Walsh | Head of Marketing | guessed | T3 | priority 3 ('marketing') | hold: T3: role fit below the T3 spend threshold | SIMULATED |

Reachability tiers are parsed from `references/apollo-credit-costs.md`, not copied. A T4 contact never gets a match credit; a shortfall is taken rather than filled from T4. Catch-all enrollment policy on record: **unset**.

Northwind Analytics could draw 5 and yielded 4 reachable; the shortfall was taken.

Cobalt Systems could draw 3 and yielded 2 reachable; the shortfall was taken.

Harbor Labs could draw 2 and yielded 1 reachable; the shortfall was taken.

Tidewater AI could draw 2 and yielded 1 reachable; the shortfall was taken.

## 7. Field gate (Excellent contacts)

| Contact | Gate | Fact-bearing sources | Missing | Label |
|---|---|---|---|---|
| A. Reyes | PASS | 8 | none | SIMULATED |
| J. Okafor | PASS | 8 | none | SIMULATED |
| S. Lindqvist | PASS | 8 | none | SIMULATED |
| R. Singh | PASS | 8 | none | SIMULATED |
| M. Duarte | PASS | 8 | none | SIMULATED |
| P. Anand | FAIL | 7 | LinkedIn Profile Summary | SIMULATED |

The contact and account records are FIXTURES; the gate is `field_gate.py`, unchanged. A FAIL names its remediation instead of composing around the gap.

## 8. Composition checks

The opener text below is a FIXTURE. The demo does not call a model; it runs the deterministic checks a live opener must also pass: no bare merge tokens, and every number traceable to a named source.

**A. Reyes** (Northwind Analytics), FIXTURE:

> You co-founded Northwind in 2023 after running analytics consulting, and now own the call on who builds revenue operations. Reading the RevOps Lead posting your team opened on 2026-08-25, the scope covers CRM hygiene and pipeline reporting in one seat. That reads as a build seat rather than a support seat. Who owns pipeline reporting until that hire lands?

**J. Okafor** (Northwind Analytics), FIXTURE:

> You joined Northwind in 2025 to build the growth function, and attribution has been yours since. Reading the RevOps Lead posting from 2026-08-25, reporting moves to a new seat. That splits attribution across two owners. How will the handoff work?

**R. Singh** (Northwind Analytics), FIXTURE:

> You were the first sales hire at Northwind and carry a team of 40 accounts alone. Reading the RevOps Lead posting from 2026-08-25, reporting is about to get an owner. That changes what you are measured on. What does your pipeline review look like today?

**M. Duarte** (Cobalt Systems), FIXTURE:

> You founded Cobalt in 2024 and have written about replacing manual list building. Reading the GTM Engineer posting from 2026-08-28, the role builds that automation in Clay and n8n. That is the build you described, handed to one person. Who runs list building until they start?

| Contact | Checks | Label |
|---|---|---|
| A. Reyes | pass | SIMULATED |
| J. Okafor | pass | SIMULATED |
| R. Singh | the number '40' appears in no named source | SIMULATED |
| M. Duarte | pass | SIMULATED |

## 9. Pre-send review queue

| Contact | Account | Status | Label |
|---|---|---|---|
| A. Reyes | Northwind Analytics | ready for pre-send review | SIMULATED |
| J. Okafor | Northwind Analytics | ready for pre-send review | SIMULATED |
| M. Duarte | Cobalt Systems | ready for pre-send review | SIMULATED |
| K. Whitfield | Harbor Labs | ready for pre-send review; Good tier composes no personalization fields | SIMULATED |
| T. Nakamura | Tidewater AI | ready for pre-send review; Good tier composes no personalization fields | SIMULATED |
| S. Lindqvist | Northwind Analytics | held: catch-all enrollment gate (no policy recorded) | SIMULATED |
| R. Singh | Northwind Analytics | held: composition check, the number '40' appears in no named source | SIMULATED |
| P. Anand | Cobalt Systems | held: field gate FAIL, LinkedIn Profile Summary | SIMULATED |

Nothing is enrolled. Pre-send review and enrollment are human gates, in the demo and in a live run.

## Next step

Run the same accounts through your own setup. Nothing is spent:

```
python3 scripts/demo.py --config instance-config.json
```

Every gap it finds (an unset key, a missing scoring config, a motion with no list, an unrecorded catch-all policy) comes back as a finding.

