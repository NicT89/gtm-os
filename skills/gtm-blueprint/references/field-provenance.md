# Field provenance map (per-deployment template)

**This file is a template. Rebuild it for each deployment** from that CRM's field
inventory, via the connector's field-listing tool, before running the gate.

Field IDs are not written here literally — they live in `instance-config.json` at the
plugin root and are referenced below as `{KEY}`. See `references/instance-config.md`
for how to populate them.

The general principle transfers to any CRM: workflows and enrichment jobs are usually
invisible to the API, so completeness is verified by checking whether the OUTPUT field
on the record is populated, never by asking whether the job ran.

## Contact-modality fields (blueprint inputs)

| Field | Config key | Populated by | Trigger | Gate role |
|---|---|---|---|---|
| System enrichment (funding stage/amount/date, dept sizes, technologies, description) | system | CRM org enrichment, 1 credit | On demand during runs | REQUIRED all motions |
| LinkedIn Profile Summary | `{APOLLO_CF_CONTACT_LINKEDIN_PROFILE_SUMMARY}` | Enrichment workflow | List membership | REQUIRED |
| Research Company Profile | `{APOLLO_CF_CONTACT_RESEARCH_COMPANY_PROFILE}` | AI research play (cited web research) | Workflow | REQUIRED (or posts digest) |
| LinkedIn Posts | `{APOLLO_CF_CONTACT_LINKEDIN_POSTS}` | `scrape-linkedin-posts` skill | Manual / batch / scheduled | Required if Research Company Profile blank; otherwise optional |
| Persona Intelligence | `{APOLLO_CF_CONTACT_PERSONA_INTELLIGENCE}` | AI play | Workflow | Optional |
| Has LinkedIn | `{APOLLO_CF_CONTACT_HAS_LINKEDIN}` | AI qualification play | Workflow | Optional |
| Startup/SMB Fit | `{APOLLO_CF_CONTACT_STARTUP_SMB_FIT}` | AI qualification play | Workflow | Optional |
| Opener | `{APOLLO_CF_CONTACT_OPENER}` | Composed by this engine | AFTER gate passes | Output |
| Blueprint | `{APOLLO_CF_CONTACT_BLUEPRINT}` | Composed by this engine | AFTER gate passes | Output |

## Account-modality fields

| Field | Config key | Populated by | Gate role |
|---|---|---|---|
| GTM Jobs w/ URL | `{APOLLO_CF_ACCOUNT_GTM_JOBS_WITH_URL}` | AI field prompt | REQUIRED for hiring motion |
| JD Summary | `{APOLLO_CF_ACCOUNT_JD_SUMMARY}` | AI field prompt | REQUIRED for hiring motion |
| Role Archetypes | `{APOLLO_CF_ACCOUNT_ROLE_ARCHETYPES}` | Set during signal-scan runs | REQUIRED for hiring motion |
| Available GTM Roles list | `{APOLLO_CF_ACCOUNT_AVAILABLE_GTM_ROLES}` | Set during signal-scan runs | Optional |
| LinkedIn Company Summary | `{APOLLO_CF_ACCOUNT_LINKEDIN_COMPANY_SUMMARY}` | Enrichment workflow | Optional |
| Company LinkedIn Posts | `{APOLLO_CF_ACCOUNT_COMPANY_LINKEDIN_POSTS}` | `scrape-linkedin-posts` skill | Optional |
| CBI Mosaic Score | `{APOLLO_CF_ACCOUNT_CBI_MOSAIC_SCORE}` | CB Insights, when connected | Optional (scoring input) |
| CBI Commercial Maturity | `{APOLLO_CF_ACCOUNT_CBI_COMMERCIAL_MATURITY}` | CB Insights, when connected | Optional (scoring + routing hint) |
| Named Investors | `{APOLLO_CF_ACCOUNT_NAMED_INVESTORS}` | Manual or CBI | Optional (opener context only) |

When rebuilding for a deployment, also record any auto-numbered duplicate fields the
CRM has accumulated (e.g. `Research Company Profile 2453`) as **deprecated, never
consume** — they are a common source of silently reading a stale value.

## Posts pipeline (CURRENT RULE, single source of truth)

The posts input field is `{APOLLO_CF_CONTACT_LINKEDIN_POSTS}` (textarea, contact),
filled EXCLUSIVELY by the `scrape-linkedin-posts` skill BEFORE the contact joins the
enrichment trigger list; the summarize-posts workflow step keys on it.

Any field named "View professional posts" is permanently deprecated: never write to
it, never key a workflow on it. Zero-post scrape results are never trusted on first
pass — retry once, then write `Scrape returned empty - verify manually (checked
<date>)`; never assert a person does not post from one empty scrape.

CBI number-field rule: CBI Mosaic Score and CBI Commercial Maturity default to 0 when
retrieval was attempted and returned nothing (0 = attempted-but-empty, blank = never
attempted). Text fields use "N/A" for the same distinction.

Digest format per post: `date | post URL | text excerpt (<= 200 chars) | reactions |
comments`; last 10 posts / 90 days. (Decision history is in the History appendix at
the end of this file.)

## Field dictionary: CB Insights account fields

Most CRMs cannot store field descriptions, so this file is the canonical dictionary.

- **CBI Mosaic Score** (number, account): CB Insights composite health score, range
  1-1000. Higher = stronger operational momentum, financial stability, favorable
  market, strong management. Scoring rubric input (>700 full points). Source: CBI
  `get_company_profile`.
- **CBI Commercial Maturity** (number, account): CB Insights stage rating, 1-5
  (1 Emerging/R&D, 2 Validating, 3 Deploying, 4 Scaling, 5 Established). Routing
  hint: 2 typically means founder-led sales with no GTM team; 3 typically means an
  early GTM team exists. Hint only — the people-search gate still decides. Source:
  CBI `commercialMaturityLevel`.
- **Named Investors** (text, account): investor firm names with round and lead status,
  for OPENER CONTEXT ONLY (e.g. "Benchmark, led Series B 2026"). Firms are never saved
  as contacts and never targeted; the outreach-relevant humans are advisors and
  growth-adjacent decision makers.

## CBI-to-CRM data mapping (persist vs runtime)

| CBI data point | Destination | Rationale |
|---|---|---|
| Funding stage, amount, date | CRM SYSTEM fields (via org enrichment); CBI as pre-filter and cross-check | Already stored; no custom field |
| Total funding | CRM system | Already stored |
| Description, founded year, HQ, taxonomy | CRM system | Already stored |
| Mosaic score | CBI Mosaic Score (custom, number) | Scoring rubric input, persists |
| Commercial maturity | CBI Commercial Maturity (custom, number) | Scoring + routing hint, persists |
| Investors (firm, round, lead) | Named Investors (custom, text, opener context only) | Persists |
| Revenue (est/reported) | RUNTIME ONLY: search filter and scoring at run time | Avoid duplicate storage drift |
| Competitors | RUNTIME ONLY: feeds blueprint positioning lines at compose time | Ephemeral, changes often |
| News, hiring insights, headcount growth | RUNTIME ONLY: recency hooks and scoring | Ephemeral |

## Operating conventions

- **The N/A rule:** when an enrichment RUNS but returns no data for a TEXT field,
  write "N/A" instead of leaving it blank, so blank always means "never run" and "N/A"
  means "ran, nothing found". NUMBER fields use 0 for the same purpose.
- **Contact-account linkage bug (observed in Apollo):** contacts created via API can
  appear in search yet NOT under their company page's People tab (account rows show
  `num_contacts` 0). Workaround: always operate on contact IDs and contact LISTS,
  never on "contacts at this company" from the account side; company-workflow steps
  that act on a company's contacts may silently match nobody. Re-verify whether this
  reproduces in your instance before designing around it.
- **CBI Mosaic availability:** Mosaic values may be plan-gated and come back empty for
  every company on some CB Insights plans. Check the CBI UI; where unavailable, score
  Mosaic at half-weight-neutral in the rubric rather than penalizing the account.

## Enrichment workflow order

Reference build for the enrichment workflow, trigger = list membership only (no score
condition): (1) LinkedIn Profile Summary → (2) Persona Intelligence → (3) Summarize
Professional Posts (requires the LinkedIn Posts field populated; fill it via
`scrape-linkedin-posts` before list-add) → (4) Research Company Profile (only if
empty; never overwrites).

## Remediation paths by populator

- Workflow field blank: re-add the contact to the workflow's trigger list (remove then
  re-add if already a member; workflow triggers have failed silently on API-created
  contacts), wait, re-check the field value.
- Posts field blank: run `scrape-linkedin-posts` for that contact.
- System enrichment missing: run org enrichment (1 credit) on the account.
- AI field prompt blank (account JD fields): confirm the account is in the prompt's
  scope in the CRM UI; these often run UI-side only.

## Sample gate result (shape reference)

> PASS. Populated: system enrichment, LinkedIn Profile Summary, Research Company
> Profile, Persona Intelligence, Has LinkedIn, Startup/SMB Fit. Blank: posts digest
> (optional here because Research Company Profile is present), and several
> other-motion fields that are not blueprint inputs. Account-side custom fields not
> applicable for the funding motion.

Record your own verified gate results in your deployment's copy — a real PASS and a
real FAIL are the fastest way to confirm the gate is reading the right fields.

## History appendix (dated decisions, superseded content)

- 2026-08-04: a "View professional posts" field was briefly un-deprecated as the
  workflow input for the summarize step.
- 2026-08-07: it failed its live test — a silent-empty scrape wrote "N/A - no posts"
  for a founder who does post.
- 2026-08-11: permanently deprecated; a dedicated LinkedIn Posts field created as the
  replacement; zero-post verification rule adopted; the CBI 0-vs-blank rule finalized,
  superseding an earlier leave-blank decision.
