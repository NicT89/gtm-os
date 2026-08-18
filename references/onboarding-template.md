# GTM Onboarding Template (Company Context Intake)

The structured intake a GTM engineer runs against any company before designing a GTM OS. Every field is a question a GTM engineer would ask the business. `jd-intake` maps a job description onto it; company research closes the gaps; `provision-gtm-engine` Phase 0 uses the same spine so client provisioning and role research share one format.

## Status model (rubric, revised 2026-08-17)

Exactly TWO statuses, judged against the source document alone:

- **Known**: the source document (JD, brief, site) itself answers the field. Later enrichment does not change this; a rebrand discovered in research does not make the company name "partial."
- **Unknown**: the source document does not answer the field.

Enrichment and questions live in their own COLUMNS, never in the status:

- **Extended Search (ES)** column: what research added to the field, with attribution (source URL, method, capture date). A Known field can carry ES enrichment; an Unknown field is usually closed by it.
- **Ask** column: open questions, one or more per field, phrased ready to use. Consumed by humans in interviews or by agents as a task list. A field can be Known and still carry Asks (scope stated but ambiguous).

The older four-way FILLED / PARTIAL / GAP / ASK legend is retired: it mixed source-coverage, enrichment, and questions into one overloaded label, which made classification arguable. Status answers exactly one question (did the source document answer this?); the columns carry everything else. `scripts/render_report.py` still accepts the legacy keys so previously rendered inputs keep working, but new work uses Known/Unknown.

Rules: mark inferences "(inferred)"; every hard fact carries a source URL; unverifiable claims become Ask entries, never facts.

## Section A: Company and Product

| # | Field |
|---|-------|
| A1 | Company name, legal entity, brand history (rebrands, M&A) |
| A2 | What the company does (one-liner) |
| A3 | ICP: who buys (size, vertical, platform signals) |
| A4 | Customer vs end-user distinction (whose lifecycle does the product instrument) |
| A5 | Product lines / modules (the upsell map's raw material) |
| A6 | Integration ecosystem (integrations double as buyer signals) |
| A7 | Pricing model and sales motion (PLG vs sales-led; read the pricing page CTA) |
| A8 | Competitors |
| A9 | Partners and partnership types (tech-embed vs channel vs co-sell) |
| A10 | Funding, size, HQ, locations, headcount trend |

## Section B: GTM Organization

| # | Field |
|---|-------|
| B1 | Teams the role/engagement supports |
| B2 | GTM team size and names by function |
| B3 | Seniority breakdown per function (leadership wants drill-down analytics; ICs want more closed deals with less wasted motion) |
| B4 | RevOps/GTM Ops team and likely manager or sponsor |
| B5 | Named collaborators (identify, enrich, read their posts) |
| B6 | Where Support sits (own org vs inside CS) |
| B7 | Other open GTM roles (JDs leak tools, KPIs, and team gaps) |

## Section C: Revenue Lifecycle

| # | Field |
|---|-------|
| C1 | Lead sources: inbound, outbound, events, partnerships |
| C2 | Attribution state: campaign to UTM to CRM to closed-won, and where it breaks |
| C3 | Sales journey: stages, deal size, cycle length (deal size dictates the human vs AI split) |
| C4 | Onboarding process and technical implementation path |
| C5 | Health score definition and product usage metrics |
| C6 | Contract terms and renewal workflow |
| C7 | Cross-sell and upsell paths (from the product catalog) |
| C8 | Commission structure and payout process (quietly puts Finance in scope) |
| C9 | Escalation routing |

## Section D: Systems and Data

| # | Field |
|---|-------|
| D1 | CRM division of labor (two CRMs usually means sales vs marketing split) |
| D2 | Full tool stack |
| D3 | MCP/API coverage per stack tool (see references/mcp-coverage-map.md) |
| D4 | Current AI/agent setup: connectors, skills, workflows in daily use |
| D5 | Data silos, manual workflows, real-time gaps |
| D6 | Work intake process (tickets, requests, projects) |

## Section E: Role Scope and Expectations

| # | Field |
|---|-------|
| E1 | Success milestones (30/60/90, 6-month, 1-year) |
| E2 | KPIs owned |
| E3 | Scope boundaries and priority arbitration (flag scope creep explicitly) |
| E4 | Remote vs in-person expectations |
| E5 | Compensation / budget |
| E6 | Ownership model (build-and-own vs build-and-hand-off) |
| E7 | System observability expectations (efficacy tracking, error notification, root cause) |

## Output contract

The completed template is delivered as: (1) the mapping table with status, value, source per field; (2) the ES task list grouped by research method; (3) the ASK list phrased ready to use. Render the human-facing version with `scripts/render_report.py` for consistent formatting and PDF output.
