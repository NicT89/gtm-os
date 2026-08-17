---
name: provision-gtm-engine
description: Provision the full GTM OS engine for a company from a single URL. Use when the user says "provision the GTM engine for [URL]", "set up the engine for a new client", "run provision-gtm-engine", "onboard [company] to the playbook", or starts a new client deployment. Produces the company context brief, ICP hypothesis, signal design, Apollo configuration (Context Center, fields, lists, sequences), and the operating cadence, with human gates at ICP sign-off, credit spend, and sequence activation.
---

# Provision GTM Engine

Input: one company URL. Output: a working, documented GTM engine that company's team operates. This playbook was built and operated against a live pipeline before being packaged as a template; every client instance inherits the latest version and its learnings feed back as version increments.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Phase 0: Company context brief (agent, ~1 hour)

Scrape the site (home, pricing, careers, docs, blog). Extract: what they sell, their 2-3 distribution models and the buyer persona per model (most companies have multiple: a primary product for one persona and secondary channels like widgets, APIs, or partnerships for others), competitive frame, pricing model, GTM motion type (PLG free trial vs sales-led book-a-call, classify from the primary website CTA), public support channels, and review-site presence. Pull firmographics and hiring signals from Apollo. Draft ICP hypothesis v0.
**GATE 1: human signs off the ICP hypothesis before anything is built.**

## Phase 1: Signal design

Define what a buying signal is for THIS company: hiring in a function, funding events, tech stack changes, product launches, regulatory shifts. Rank 3-5 signal types by intent strength, map each to a collection method, and build the 0-100 scoring rubric with routing thresholds (Excellent / Good / Fair tiers per the gtm-signal-scan skill).

## Phase 2: Apollo build

1. Context Center: company profile (overview, pain points, value proposition, competitors, differentiators, soft CTAs) and one product entry per offering using the persona template (Department, Titles, Pain Points, Value Props, Use Cases, Killer Questions, Why Now). Never state pricing in cold-outreach context.
2. Fields: contact multi-line text fields `<prefix> Opener` and `<prefix> Blueprint` (created in the UI, the API cannot create field definitions; `<prefix>` comes from `{INSTANCE_FIELD_PREFIX}`); account fields for the signal data the motion needs.
3. Lists: motion account list, motion contact list, "LinkedIn Profile Enrichment" (workflow trigger), Warm Leads, Negative Response, Watched Video (tags-as-lists for engagement routing).
4. Sequences: one per signal segment, created INACTIVE with "[Claude]" naming, 5-step default (email with A/B variants → LinkedIn view → manual blueprint email with canned video → LinkedIn connect → breakup reply), merge tokens with object prefixes, then audited via the outreach-audit skill.
5. Engagement plumbing spec (UI-side): deals created selectively for meetings and strong-intent replies only, owner set to the operating user; negative replies tagged, neutral replies generate a human follow-up task; notifications on for replies, meetings, and video views; all responses sent manually, only sequence sends automate.
**GATE 2: credit-consuming enrichment batches approved by the human, with the total stated upfront per the plugin root's references/apollo-credit-costs.md. Confirm that file's per-call numbers against the client's own Apollo account during provisioning — the free-vs-paid boundary holds across plans, the per-call costs do not. GATE 3: human reviews merged previews against a fully-enriched contact, then activates sequences.**

## Phase 3: Operate

Weekly cadence: signal scan (gtm-signal-scan skill), enrichment approval, cohort enrollment sized to what the human can service same-day on manual steps, reply triage (human sends every response), Friday analytics readout.

## Phase 4: Learn

Weekly iteration memo: sequence and variant analytics plus reply-content review, proposing at most 2 single-variable changes with hypotheses; human approves; changelog records outcomes. Monthly: scoring rubric recalibration against reply data, Context Center drift check against the live website. Every audit finding becomes a permanent gate or pipeline step. Learnings that generalize flow back to the plugin repo as version increments; client data never does.

## File home (set once per instance)

Offer the user: a local folder Claude structures (briefs, audit log, changelog, run reports, JD library), or Google Drive with the identical structure for cross-device access. Box and OneDrive are supported substitutes. Audit logs and feedback loops always stay in the user's own storage; they are the personalized layer of the playbook.
