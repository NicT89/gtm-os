# Field provenance map (per-deployment template)

Every field this engine reads or writes is listed here with its purpose, because a CRM
field's label is not its contract. "LinkedIn Posts" does not say that an empty value means
"verified not a poster" rather than "not researched yet", and that difference decides
whether a run should re-scrape. Most CRMs, Apollo included, expose no place to store this
next to the field itself, so this file is the field documentation and it is the copy that
must stay correct.

**This file is a template. Rebuild it for each deployment** from that CRM's field
inventory, via the connector's field-listing tool, before running the gate.

Field IDs are not written here literally — they live in `instance-config.json` at the
plugin root and are referenced below as `{KEY}`. See `references/instance-config.md`
for how to populate them.

The general principle transfers to any CRM: workflows and enrichment jobs are usually
invisible to the API, so completeness is verified by checking whether the OUTPUT field
on the record is populated, never by asking whether the job ran.

## Contact-modality fields (blueprint inputs)

| Field | Purpose (what it holds, what consumes it) | Config key | Populated by | Trigger | Gate role |
|---|---|---|---|---|---|
| System enrichment (funding stage/amount/date, dept sizes, technologies, description) | The company's hard facts. Drives motion routing (dept sizes decide GTM-present vs not), ICP gates, and every funding number quoted in an opener. | system | CRM org enrichment, 1 credit | On demand during runs | REQUIRED all motions |
| LinkedIn Profile Summary | Career history and role context for THIS person. Establishes persona (founder vs operator vs IC), which decides motion fit and opener framing. Verify the employer it names matches the account before trusting it. | `{APOLLO_CF_CONTACT_LINKEDIN_PROFILE_SUMMARY}` | Enrichment workflow | List membership | REQUIRED |
| Research Company Profile | Cited web research: recent developments, pain points, common ground, conversation starters. The richest single source for blueprint content, and the fallback voice source when the contact's own posts are thin. | `{APOLLO_CF_CONTACT_RESEARCH_COMPANY_PROFILE}` | AI research play (cited web research) | Workflow | REQUIRED (or posts digest) |
| LinkedIn Posts | Digest of authored posts in the lookback window, with dates and engagement. The mirror-line source: the recipient's own words, and the only field that proves a claimed post reference is real. Empty means not a poster, not "not researched". | `{APOLLO_CF_CONTACT_LINKEDIN_POSTS}` | `scrape-linkedin-posts` skill | Manual / batch / scheduled | Required if Research Company Profile blank; otherwise optional |
| Persona Intelligence | One-line role read plus identity-confidence notes. Read the identity flags before composing: a name-match warning here means the research may describe a different person. | `{APOLLO_CF_CONTACT_PERSONA_INTELLIGENCE}` | AI play | Workflow | Optional |
| Has LinkedIn | Whether a usable profile URL exists. Gates scraping entirely; a contact without one cannot be post-personalized or tenure-checked. | `{APOLLO_CF_CONTACT_HAS_LINKEDIN}` | AI qualification play | Workflow | Optional |
| Startup/SMB Fit | Qualification verdict for the size/stage band this engine serves. A "Not Qualified" here should stop composition, not just flag it. | `{APOLLO_CF_CONTACT_STARTUP_SMB_FIT}` | AI qualification play | Workflow | Optional |
| Opener | ENGINE OUTPUT. The opening of email 1, merged as `{{contact.<prefix> Opener}}`. **`skills/outreach-audit/SKILL.md` is the authoritative composition spec** and owns length, structure and the falsifiability tests; this row deliberately states neither, because when it did the two drifted. Never hand-edited in the CRM without recording it. | `{APOLLO_CF_CONTACT_OPENER}` | Composed by this engine | AFTER gate passes | Output |
| Blueprint | ENGINE OUTPUT. The 30-day Week 1 / Week 2 / Weeks 3-4 plan, merged as `{{contact.<prefix> Blueprint}}`. Its closer must match the motion the contact is enrolled in. | `{APOLLO_CF_CONTACT_BLUEPRINT}` | Composed by this engine | AFTER gate passes | Output |

## Account-modality fields

| Field | Purpose (what it holds, what consumes it) | Config key | Populated by | Gate role |
|---|---|---|---|---|
| GTM Jobs w/ URL | Role title, posting URL, and posted date, pipe-separated. The posted date is the opener's "open N days" number and the URL is what a JD audit re-scrapes. Without the date the hiring opener has no hard number. | `{APOLLO_CF_ACCOUNT_GTM_JOBS_WITH_URL}` | AI field prompt | REQUIRED for hiring motion |
| JD Summary | Condensed first-90-days scope of the open role: the named tools and the work the hire inherits. Source of the blueprint's real-tool requirement. Lossy by nature — audit the stored full JD for reporting line and seniority. | `{APOLLO_CF_ACCOUNT_JD_SUMMARY}` | AI field prompt | REQUIRED for hiring motion |
| Role Archetypes | Normalized role classification, so different titles for the same job route the same way. Drives motion selection and which persona owns the req. | `{APOLLO_CF_ACCOUNT_ROLE_ARCHETYPES}` | Set during signal-scan runs | REQUIRED for hiring motion |
| Available GTM Roles list | Every open GTM req at the account, not just the one being anchored on. Reveals multi-role patterns worth naming in copy. | `{APOLLO_CF_ACCOUNT_AVAILABLE_GTM_ROLES}` | Set during signal-scan runs | Optional |
| LinkedIn Company Summary | The company's own positioning in its own words. The rung-2 voice source when a contact's posts are too thin to mirror. | `{APOLLO_CF_ACCOUNT_LINKEDIN_COMPANY_SUMMARY}` | Enrichment workflow | Optional |
| Company LinkedIn Posts | Company-page post digest. Corporate voice and announcement timing; distinct from any individual's posts. | `{APOLLO_CF_ACCOUNT_COMPANY_LINKEDIN_POSTS}` | `scrape-linkedin-posts` skill | Optional |
| CBI Mosaic Score | Third-party composite health score, 0-1000. Scoring input only; never quoted to a recipient. | `{APOLLO_CF_ACCOUNT_CBI_MOSAIC_SCORE}` | CB Insights, when connected | Optional (scoring input) |
| CBI Commercial Maturity | 1-5 rating of how built-out the commercial function is. Calibrates blueprint ambition and hints at motion (2 suggests founder-led, 3 suggests a team in place). A hint, never the routing decision. | `{APOLLO_CF_ACCOUNT_CBI_COMMERCIAL_MATURITY}` | CB Insights, when connected | Optional (scoring + routing hint) |
| Named Investors | Lead and participating investors on the latest round. Opener credibility context ONLY; never a claim of relationship. | `{APOLLO_CF_ACCOUNT_NAMED_INVESTORS}` | Manual or CBI | Optional (opener context only) |
| Tech Stack Details (A11) | What THEY run to sell and operate, not what their product integrates with. Composition requires citing one real stack tool, so this is where a verified stack lives, and it is the canonical gap-ledger write target. NEVER write inferred technographics here: those are for filtering and are not quotable. | `{APOLLO_CF_ACCOUNT_TECH_STACK_DETAILS}` | The engine, from a primary source. Job descriptions first; source order in the plugin root's `references/scraping-playbook.md` | Optional |

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

- **Apollo's own `organization_revenue` returns `0.0` when revenue is UNKNOWN, not zero.**
  Private companies routinely come back this way. Write `N/A`, never `$0`, and never cite
  the figure. Observed 2026-09-07: one enrichment call returned real estimates for two
  companies and `0.0` for a third that is privately held — the absent value sits in the
  same column as the good ones, which is what makes it dangerous. A blueprint citing "$0
  revenue" to a real prospect is a fabricated hard number, and the falsifiability test
  will not catch it because the number came from a tool. When revenue matters and Apollo
  has none, the gap is filled by CB Insights or a primary source, or it stays N/A.
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
