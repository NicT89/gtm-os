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
- {ACCOUNT_LIST}: accounts list per motion (defaults: "Companies Hiring" / "Funding Signal - No GTM")
- {CONTACT_LISTS}: every new contact gets "LinkedIn Profile Enrichment" (when a LinkedIn URL exists) plus the motion contact list
- {SEQUENCE}: the motion's sequence; NEVER enroll anyone from this skill, enrollment is a human gate

## Credit rules (non-negotiable)

State total credit cost before any spend and get explicit approval. Costs, the estimate formula, and the reachability tiers live in the plugin root's references/apollo-credit-costs.md — read it rather than quoting numbers from memory. The short version: search is free, reveals are not, so rank the whole field for free before spending. Report actual burn by category at the end of the run.

## Step 1: Signal search (1 credit)

Signal selection and any additional gates come from references/signals-doctrine.md at the plugin root: the canonical taxonomy of buying signals (funding, postings, job changes, posting disappearance, website intent, commercial-maturity shifts, social buying language, review-site switch intent), each with source, cost, decay window, motion routing, and owner. The two searches below are gates 1-2 of that taxonomy; run additional gates only when the doctrine marks them active for this deployment.

Hiring motion, Apollo company search: US, 11-200 employees, q_organization_job_titles ["gtm engineer","go-to-market engineer","revenue operations","gtm operations","ai operations"], job posted within 60 days, keywords SaaS/software/AI.
Funding motion: latest_funding_date_range last 6 months, latest_funding_amount_range min 2000000, organization_department_or_subdepartment_counts master_sales 0-3, same size/geo/keywords.

Dedupe rule: the response's "accounts" array = already in the CRM (route to update, never create); "organizations" array = net new.

## Step 2: Score and tier

Score 0-100: archetype/motion fit 25, stage and funding 20, signal age 15, budget signal 15, stack overlap 10, geography 10, warm path 5. Exclude on sight: competitors (agencies selling GTM/AI services), job boards, staffing firms, offshore-only relevant roles, companies with an established sales/RevOps team of 4+ (funding motion) or dedicated GTM engineering team of 2+ (hiring motion).

Tiers: Excellent = full enrichment (org enrich + all selected people + posts digest + Opener/Blueprint composition). Good = partial (org enrich + 1-2 people). Fair = account record only, no people spend.

## Step 3: Account enrichment and creation

Org-enrich Excellent and Good tiers (1 credit each; funding, sales_department_size, growth, technologies land in Apollo system fields automatically). Bulk-create net-new accounts (name + domain; NOTE: account creation does NOT dedupe, always check step 1's accounts array first). Hiring motion: write GTM Jobs w/ URL (role | URL | posted date lines) and Role Archetypes fields. Add all accounts to {ACCOUNT_LIST}. Verify membership on the record's label_ids, never trust list cached_count.

## Step 4: People selection (search free)

Company boundary rule: search people ONLY by organization_ids resolved from enrichment or the search response. Domain, name, and website matching return people at similarly named companies; org id is the only reliable boundary. Search people at Excellent/Good accounts. Selection priority: CEO/founder/co-founder, then COO/chief of staff/head of operations, then growth/marketing/product/bizdev heads. Skip advisors, investors, board members, engineers, recruiters. Sizing rule: ~15 employees pick 3, ~50 pick 4-5, ~100 pick 6-7; Good tier picks 1-2 regardless.

## Step 4b: Rank on reachability BEFORE spending (free)

People search returns email_status and phone-availability flags without returning the address and without charging, so the whole candidate field can be ranked before a single credit is spent. Score each candidate as role-fit (step 4 priority order) x the reachability multiplier in the plugin root's references/apollo-credit-costs.md: verified+phone 1.0, verified 0.85, catch-all/guessed 0.6, unavailable/absent 0.3.

Then spend top-down against the step 4 sizing rule, and do NOT spend a match credit on T4 (unavailable) candidates at all: a match that returns no sendable address is a credit spent to learn the contact was never reachable. If a strong-fit person is T4, record them in the run report as a LinkedIn-only or referral path instead of enriching them. If ranking leaves an Excellent account with fewer reachable candidates than its size band calls for, take the shortfall rather than reaching down into T4 to fill the quota.

## Step 5: People enrichment and contact creation

Bulk-match the ranked candidates (1 credit per matched person, batches of 10, never set phone reveal or waterfall flags without separate approval). CRITICAL: enrichment results are NOT auto-saved; immediately create contacts (dedupes automatically) with organization_name for auto-linking, and label_names = {CONTACT_LISTS}. Only create contacts with a non-null email. Catch-all is a HARD EXCLUSION for sequence enrollment: a T3 (catch-all) contact may be created for the record, but is never enrolled in an email sequence (bounce postmortems show catch-alls plus stale mailboxes drive double-digit bounce rates that damage the sending domain for everyone else in the queue). Route T3 contacts to LinkedIn-only or referral paths and mark them send-excluded in the audit log. Email domains that mismatch the company domain are flagged send-risk and need human review before any enrollment.

## Step 6: Personalization prep

For each Excellent-tier contact compose the Opener and Blueprint fields per the composition spec in the outreach-audit skill, writing via contact custom fields (multi-line text, referenced in templates as `{{contact.<prefix> Opener}}` and `{{contact.<prefix> Blueprint}}`, where `<prefix>` is `{INSTANCE_FIELD_PREFIX}`). Run the `scrape-linkedin-posts` skill in batch mode against this run's Excellent-tier contacts and accounts; it writes to the posts base and pushes digests to the contact and account posts fields. Mark inactive posters "do not use post-based personalization" with an alternate angle.

## Step 7: Report and audit log

Deliver: tier table with scores, contact roster with email statuses, credit burn by category (planned vs actual), send-risk and send-excluded flags, and companies excluded with reasons.

CRM-sync health check: for records touched this run in a CRM instance with sync enabled to another system, read back each record's sync-job status (on Apollo, the record's `crm_job`) and surface any failed pushes with the error text. Silent sync failures poison downstream personalization; a domain-collision failure looks exactly like success until someone reads the record.

Append findings to the local audit log; any defect found becomes a permanent gate in the next run.

Also emit a machine-readable run artifact, run-shape-<date>.json, alongside the audit log entry: {motion, run_date, filters_used, counts: {searched, scored, excellent, good, fair, accounts_created, people_ranked, people_revealed, contacts_created, send_excluded}, credits: {planned, spent, by_category}, signals: [gate tags per account], defects: []}. Runs become diffable over time and the file doubles as client reporting data. Remind the user: enrollment is their gate, after preview review.
