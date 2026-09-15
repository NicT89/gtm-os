---
name: gtm-signal-scan
description: Run the GTM OS sourcing scan. Use when the user says "run the signal scan", "run gtm-signal-scan", "source new leads", "find companies hiring GTM roles", "find recently funded companies", "run the weekly sourcing run", or asks to refresh the prospect pipeline. Sources companies via Apollo buying signals (GTM hiring or fresh funding), scores and tiers them, enriches accounts and people, creates records with correct list routing, and appends to the run audit log.
---

# GTM Signal Scan

Weekly sourcing run: signal search, scoring, tiered enrichment, record creation, list routing, audit logging.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION and compare to the VERSION file at the plugin root. If they differ, tell the user an updated playbook version is available from the repo, then continue with the run.

## Instance variables (confirm on first run, then reuse)

- {MOTION}: "hiring" (companies hiring GTM Engineer / RevOps / AI Ops roles) or "funding" (recently raised, no established sales function)
- {ACCOUNT_LIST}: accounts list per SIGNAL TYPE, not per GTM motion (defaults: "Companies Hiring" / "Funding Signal - No GTM"). The two axes are defined in references/signals-doctrine.md.
- {CONTACT_LISTS}: every new contact gets "LinkedIn Profile Enrichment" (when a LinkedIn URL exists) plus the contact list for this signal type
- {SEQUENCE}: the sequence for this signal type; NEVER enroll anyone from this skill, enrollment is a human gate

## Credit rules (non-negotiable)

State total credit cost before any spend and get explicit approval. Costs, the estimate formula, and the reachability tiers live in the plugin root's references/apollo-credit-costs.md — read it rather than quoting numbers from memory. The short version: search is free, reveals are not, so rank the whole field for free before spending. Report actual burn by category at the end of the run.

## Step 1: Signal search (1 credit)

Signal selection and any additional gates come from references/signals-doctrine.md at the plugin root, which is the canonical taxonomy: every signal with its source, cost, decay window, routing and owner, and a line saying which are active for this deployment. **Read the taxonomy there; it is not summarized here.** This paragraph used to list the signals by name, and the list drifted to eight of the twelve rows — dropping, among others, signal 6, GTM persona presence/absence, which the doctrine marks a structural gate that is ALWAYS ON. A partial copy of a taxonomy is worse than a pointer to it, because it reads complete. The two searches below are gates 1-2; run additional gates only when the doctrine marks them active.

Hiring signal, Apollo company search: US, 11-200 employees, q_organization_job_titles ["gtm engineer","go-to-market engineer","revenue operations","gtm operations","ai operations"], job posted within 60 days, keywords SaaS/software/AI.
Funding signal: latest_funding_date_range last 6 months, latest_funding_amount_range min 2000000, organization_department_or_subdepartment_counts master_sales 0-3, same size/geo/keywords.

Dedupe rule: the response's "accounts" array = already in the CRM (route to update, never create); "organizations" array = net new.

## Step 1.5: Motion assignment (free)

**Assign the motion before scoring, because scoring depends on it and it costs nothing.**
The motion is `M1`-`M5` per the plugin root's [references/motion-codes.md](../../references/motion-codes.md),
and M1-M4 are the four quadrants of one 2x2:

|                    | NOT hiring GTM | Hiring GTM |
|---|---|---|
| **Has GTM team**   | M1 | M4 |
| **No GTM team**    | M2 | M3 |

Both axes are FREE to resolve, which is the whole reason this is its own step:

1. **Hiring GTM?** Already answered by Step 1's search filters. No extra call.
2. **Has a GTM team?** One people search per account by `organization_ids` against the GTM and
   RevOps titles. `apollo_mixed_people_api_search` costs nothing, and this is doctrine signal
   6, the structural gate marked ALWAYS ON.
   **Set `include_similar_titles: false` on this call.** It defaults to TRUE, and a fuzzy
   title search decides this gate: asked for `Founding GTM` / `Founding Account Executive` /
   `Founding Sales`, a live run returned Founding Engineer, Founding SWE and Founding
   Software Engineer — none of them commercial, all of them counted. **A qualification field
   set from a fuzzy match marks a company as having GTM staff on a title nobody holds.**
   Strict for a search that decides a field; fuzzy only when prospecting, where a near-miss
   costs a glance and a false qualification costs the whole routing.
   **And run the falsification query before reading anything into a zero.** See below.

**"Hiring GTM" means hiring GTM ENGINEERING or REVOPS specifically.** A company hiring sellers
— AE, SDR, AM — is not hiring the function this engine replaces, and those reqs are **moot for
qualification**: they neither disqualify an account nor count toward the hiring axis. Only reqs
for the systems function do. Read literally, "any GTM req" would disqualify most companies
worth talking to, since almost everyone is always hiring a seller.

Then apply **M5, which overrides M3 and M4**: if a GTM leader has been in seat 9 months or
less, the motion is M5 regardless of hiring state, because a new leader's first ninety days is
a different conversation from a team's expansion.

**The same free call also enforces the exclusion.** A company with a dedicated GTM engineering
or RevOps team of 2+ is excluded, and running this BEFORE enrichment is what makes the
exclusion free. Observed on a live run 2026-09-10: this step disqualified two accounts that
had 4 and 3 GTM staff respectively, saving both their enrichment credits and the people-match
credits that would have followed. Run in the old order, those credits were already spent by
the time anyone looked.

Record the assigned motion with its date and the quadrant evidence. **Re-derive it every run
rather than trusting the stored value** -- reqs get filled and leaders land, so motion is a
property of current state, not a label.

Route the account into that motion's list, and remember the naming rule: every Apollo object a
motion touches carries the code at the front of its own name.

### The falsification query (run it before believing any zero)

**An ignored filter and a real absence return the identical empty response.** Nothing in the
payload distinguishes them, so a zero is not evidence until the filter has been shown to
constrain.

**The step:** re-run the same query, changing only the filter value to something nothing could
match — a title no company posts, a technology nobody uses. If that also returns zero, the
filter works and the real zero is trustworthy. If it returns results, the filter is being
ignored and the original zero meant nothing.

It costs one free call. Run it:

- whenever a zero decides a qualification field,
- the first time a filter is used in a run,
- and any time a zero is surprising — a company you expect to be hiring that appears not to be.

**A zero that has not been falsified is not a finding.** Write it into the run report as
"unverified zero" rather than as an absence.

This is the repo's own rule about checks that cannot fail, applied to a query rather than to a
test. And it generalises: `references/known-failure-modes.md` row 7 is the entry for this, and
**every other row in that register is a defect that returned a well-formed answer that happened
to be false.** Read it before trusting any single field that decides a route — the
compensations listed there are all free.

### Trusting a field you did not watch change

**A provider's freshness timestamp records when it wrote the row, not when it verified it.**
Observed: an index returned a contact as "SVP Strategy & Commercial" stamped the same day,
six months after he had publicly announced becoming Chief Commercial Officer — and the saved
CRM record held the newer title than the index it had been sourced from. The field that looks
like a guarantee is the one that misled.

So: **a title from search is a hypothesis; the person's own announcement is the evidence.**
This matters most where a title decides something — seniority routing, the leader-versus-IC
persona switch, and any tenure filter, which is the gate the new-leader motion rests on
entirely. Where the two disagree and it changes the motion, resolve it before enrolling.

**But a disagreement in spelling is not a disagreement in fact.** The same seat arrives as
"VP, Go-to-Market" and "VP, Go to Market", as "Co-Founder" and "Cofounder", as "Chief Revenue
Officer" and "Chief Revenue Officer (CRO)", as "SVP Strategy & Commercial" and "SVP Strategy
and Commercial". **None of those are conflicts, and nothing in this run may fail, branch or
re-source because of one.** Normalize before comparing: fold case, whitespace, punctuation,
parentheticals and the common seniority abbreviations, then compare.

`scripts/field_match.py` does exactly that and nothing more —
`python3 field_match.py "<a>" "<b>"` exits 0 when they agree, 1 when they genuinely differ.
It deliberately does **not** stem or guess synonyms, because the opposite failure is worse:
a normalizer eager enough to fold "Head of Sales" into "Head of Marketing" qualifies a company
on a seat nobody holds. Its tests pin both directions.

The rule this leaves: **compare on the normalized value, report on the raw one.** Store what
each source actually said, so a later reader can see which was stale, and never let the
difference between them stop a run.

## Step 2: Score and tier

**Scoring runs in two passes, because half its inputs do not exist yet at this point in the run.**
Observed 2026-09-10: the Step 1 company-search response carries no employee count, no funding
stage, no technologies and no location for a net-new organization, so a single-pass score was
being computed against absent data and reading as a real number.

**Pass 1, the FREE pre-score, decides who is worth enriching** (55 points available):

| Dimension | Points | Source at this stage |
|---|---|---|
| Motion fit | 15 | Step 1.5's quadrant. Free. |
| Signal age | 15 | Posting dates from Step 1's filters. Free. |
| Budget signal | 15 | Headcount growth, revenue when present. Free, on the search response. |
| Geography | 10 | Free when present; absent on net-new orgs, so score 0 and let Pass 2 fill it. |

**Pass 2, after Step 3 enrichment, completes the score** (45 points):

| Dimension | Points | Why it cannot be Pass 1 |
|---|---|---|
| Stage and funding | 20 | `latest_funding_stage` arrives from org enrichment only. |
| Archetype fit | 10 | Depends on the JD, which needs the postings call. |
| Stack overlap | 10 | Technologies are not on the search response. |
| Warm path | 5 | Needs the contact set. |

**`archetype/motion fit 25` was one dimension until 1.9.5 and is now two**, split 15/10, because
the two halves resolve at different stages and for different reasons: the motion is a free
structural fact about the company, and the archetype is a reading of a specific job description.
Bundling them forced the free half to wait on the paid half.

Tier on the Pass 1 score to choose who gets enriched; re-tier on the full score before any
people spend. A Pass 1 score is never reported as a final score -- label it `pre-score`. Exclude on sight: competitors (agencies selling GTM/AI services), job boards, staffing firms, offshore-only relevant roles, companies with an established sales/RevOps team of 4+ (funding signal) or dedicated GTM engineering team of 2+ (hiring signal).

Tiers: Excellent = full enrichment (org enrich + all selected people + posts digest + Opener/Blueprint composition). Good = partial (org enrich + 1-2 people). Fair = account record only, no people spend.

## Step 3: Account enrichment and creation

Org-enrich Excellent and Good tiers (1 credit each; funding, sales_department_size, growth, technologies land in Apollo system fields automatically). Bulk-create net-new accounts (name + domain; NOTE: account creation does NOT dedupe, always check step 1's accounts array first). Hiring signal: write GTM Jobs w/ URL (role | URL | posted date lines) and Role Archetypes fields. Add all accounts to {ACCOUNT_LIST}. Verify membership on the record's label_ids, never trust list cached_count.

## Step 4: People selection (search free)

Company boundary rule: search people ONLY by organization_ids resolved from enrichment or the search response. Domain, name, and website matching return people at similarly named companies; org id is the only reliable boundary. Search people at Excellent/Good accounts. Selection priority: CEO/founder/co-founder, then COO/chief of staff/head of operations, then growth/marketing/product/bizdev heads. Skip advisors, investors, board members, engineers, recruiters. Sizing rule: ~15 employees pick 3, ~50 pick 4-5, ~100 pick 6-7; Good tier picks 1-2 regardless.

## Step 4b: Rank on reachability BEFORE spending (free)

**Run the people search TWICE and read both together: once by title, once by seniority.** Neither is safe alone, and they fail in opposite directions. A title search MISSES `Founding <function>` staff entirely — on a live run it returned zero people at two companies that both have go-to-market staff, whose titles were "Founding Technical Account Executive", "Founding Growth" and "Founding Account Executive". A seniority search OVER-REPORTS the same people: querying one of those companies for c_suite/founder/owner returned five results and every one was an individual contributor, because the provider reads "Founding" as founder-level seniority. So treat `Founding <anything commercial>` as a GTM individual contributor, never as a founder, and never conclude a company has no GTM staff from a title search alone. This matters most at exactly the companies worth reaching: early-stage, no GTM leader yet, first commercial hires titled "Founding X". More broadly, **not found is not the same as absent** — vary the query shape before concluding a value does not exist, and only then escalate to another source.

People search returns email_status and phone-availability flags without returning the address and without charging, so the whole candidate field can be ranked before a single credit is spent. Score each candidate as role-fit (step 4 priority order) x the reachability multiplier in the plugin root's references/apollo-credit-costs.md. **Read the tier table there rather than a summary of it.** This sentence used to restate the four tiers and the restatement had lost two flags: `likely` (T3) and `unverified` (T4). Dropping `unverified` from T4 is the expensive one — it reads as spendable, so every `unverified` candidate bought a match credit to learn the address was never sendable, which is the exact spend this step exists to prevent.

Then spend top-down against the step 4 sizing rule, and do NOT spend a match credit on T4 candidates at all — T4 is `unavailable`, `unverified`, or the flag absent entirely, per the table: a match that returns no sendable address is a credit spent to learn the contact was never reachable. If a strong-fit person is T4, record them in the run report as a LinkedIn-only or referral path instead of enriching them. If ranking leaves an Excellent account with fewer reachable candidates than its size band calls for, take the shortfall rather than reaching down into T4 to fill the quota.

## Step 5: People enrichment and contact creation

Bulk-match the ranked candidates (1 credit per matched person, batches of 10, never set phone reveal or waterfall flags without separate approval). CRITICAL: enrichment results are NOT auto-saved; immediately create contacts (dedupes automatically) with organization_name for auto-linking.

**Contact creation is four steps, not one, they are ORDERED, and the endpoint reports success after the first.** On a live run the bulk-create call returned success while doing none of the others, and every omission is silent:

1. **Create.** The record is saved. That is all this step does.
2. **Scrape posts BEFORE the list-add.** Run the `scrape-linkedin-posts` skill in batch mode against this run's Excellent-tier contacts and accounts; it writes to the posts base and pushes digests to the contact and account posts fields. This has to happen here rather than at composition time, because the summarize-posts step of the Apollo-side cascade **keys on the posts field and fires on list membership**: add the contact first and that step runs against an empty field, writes an empty summary, and reports success. Nothing downstream can tell that from a person who does not post. The rule is stated in `gtm-blueprint`'s `references/field-provenance.md` ("filled EXCLUSIVELY by the `scrape-linkedin-posts` skill BEFORE the contact joins the enrichment trigger list"); until 1.9.3 this skill scraped in Step 6, one step too late, and was the reason that rule needed stating twice. Mark inactive posters "do not use post-based personalization" with an alternate angle. A zero-post result is retried once before it is believed.
3. **Add to lists SEPARATELY.** `label_names` passed to bulk-create is ignored — every created contact came back with an empty label set. Use the list-add endpoint and **confirm the list count moved**; a queue that looks filled and is empty reports nothing downstream.
4. **Trigger enrichment SEPARATELY.** Creating a contact does not enrich it. The AI cascade is an **Apollo-side workflow** fired by membership of the cascade list, so a contact created and never added to it has no Profile Summary, no Persona Intelligence and no Research Company Profile — and will fail the field gate at composition time, several stages later, with no indication of why. Four of six contacts in one live cohort failed exactly this way.

Treat a created contact as **incomplete until its output fields are populated**, and see Step 6 for why that is a wait-and-verify rather than a synchronous call. Only create contacts with a non-null email. **Catch-all handling is an operator policy, not a fixed rule, and it must be decided before the first send rather than per contact.** The two defensible positions: EXCLUDE catch-all (T3) contacts from email sequences and route them to LinkedIn or referral, or ENROLL them like any other verified address. Exclusion is the conservative default, and the argument for it is that a catch-all domain accepts every address, so a wrong one never bounces and never announces itself, and bounce postmortems show catch-alls plus stale mailboxes driving rates that damage a sending domain shared by every other motion. The argument against it is volume: catch-all is common on small-company domains, so on a small-business ICP the exclusion can remove most of a sourced cohort, and providers publish per-address accuracy guarantees that already price this risk. **Whichever is chosen, record it as a decision with a date and a reason, and pair it with a monitored bounce threshold** -- most sequence tools support an auto-pause on bounce rate, and enrolling catch-alls without that guardrail armed is the combination that actually burns a domain. Note the two flags are independent: `email_status: verified` describes the address, `email_domain_catchall` describes whether the domain would accept any address at all, and reading only the first is how a catch-all reaches a send unnoticed. Email domains that mismatch the company domain are flagged send-risk and need human review before any enrollment.

## Step 6: Personalization prep

For each Excellent-tier contact compose the Opener and Blueprint fields per the composition spec in the outreach-audit skill, writing via contact custom fields (multi-line text, referenced in templates as `{{contact.<prefix> Opener}}` and `{{contact.<prefix> Blueprint}}`, where `<prefix>` is `{INSTANCE_FIELD_PREFIX}`). The posts digests were already scraped in Step 5, before the list-add, so what this step does with them is **verify** rather than fetch: an empty posts summary on a contact whose digest is non-empty means the cascade fired too early, and the fix is to re-run the scrape and re-add the contact to the trigger list, not to compose around the gap.

## Step 7: Report and audit log

Deliver: tier table with scores, contact roster with email statuses, credit burn by category (planned vs actual), send-risk and send-excluded flags, and companies excluded with reasons.

CRM-sync health check: for records touched this run in a CRM instance with sync enabled to another system, read back each record's sync-job status (on Apollo, the record's `crm_job`) and surface any failed pushes with the error text. Silent sync failures poison downstream personalization; a domain-collision failure looks exactly like success until someone reads the record.

Append findings to the local audit log; any defect found becomes a permanent gate in the next run.

Also emit a machine-readable run artifact, run-shape-<date>.json, alongside the audit log entry: {signal_type, run_date, filters_used, counts: {searched, scored, excellent, good, fair, accounts_created, people_ranked, people_revealed, contacts_created, send_excluded}, credits: {planned, spent, by_category}, signals: [gate tags per account], defects: []}. Runs become diffable over time and the file doubles as client reporting data. Remind the user: enrollment is their gate, after preview review.
