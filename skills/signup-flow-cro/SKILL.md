---
name: signup-flow-cro
description: Audit and optimize a signup, registration, account-creation, waitlist, or free-trial flow. Use when the user says "run signup-flow-cro", "audit our signup flow", "signup conversions", "registration friction", "reduce signup dropoff", "signup abandonment", "people aren't signing up", "nobody completes registration", "too many steps to sign up", "simplify our signup", "trial conversion rate", or shares a signup page URL and asks why it underperforms. Produces sourced audit findings, quick wins, higher-effort changes, test hypotheses, and an optional redesigned field set with copy. Not for post-signup onboarding or for lead-capture forms that do not create an account.
---

# Signup Flow CRO

Adapted from the `signup` skill (formerly `signup-flow-cro`) in
[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), MIT
licensed, at commit `1efedbc`. The upstream license is kept in this folder's `LICENSE`.

Input: a signup flow (URL, screenshots, or a description) plus whatever funnel data exists.
Output: an audit that reduces friction to account creation without losing the data the
business genuinely needs at that moment.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin
root VERSION file, notify on mismatch, continue.

## Step 1: Context

If the Brand Kit OS connector is available, pull the product, ICP and persona context from
it before asking anything. Without it the skill degrades to asking the user; to wire it, use
the `environment-setup` skill and the plugin root's references/environment-setup.md. Do not
ask for anything the context already answers.

Establish:

1. **Flow type**: free trial, freemium, paid, waitlist, or guest-checkout account; B2B or B2C.
2. **Current state**: steps or screens, required fields, completion rate, where users drop.
3. **Constraints**: what data is genuinely required before first use, compliance or
   verification requirements, and what happens immediately after submit.

If the flow is a URL, scrape it with Firecrawl (JS wait on, since signup pages are usually
client-rendered) and capture every field, label, error state and CTA verbatim before judging.
A scrape is a credit spend: before running it, tell the user it consumes Firecrawl credits and
that a single scrape is not always one credit (the plugin root's
references/scraping-playbook.md records one that cost 5), then report the actual burn from
the response after. Screenshots or a description cost nothing and are a fine substitute.

## Step 2: Audit against the four principles

1. **Minimize required fields.** For each field: needed before first use? Deferrable to
   progressive profiling? Inferable (company from email domain)?
2. **Value before commitment.** What can the visitor see or do before creating an account?
3. **Reduce perceived effort.** Progress indicators, grouping, smart defaults, pre-fill.
4. **Remove uncertainty.** Say what happens after signup; no hidden steps.

Walk the field-by-field rules, single- vs multi-step criteria, trust and error handling,
mobile, and post-submit checks in `references/field-guide.md`.

## Step 3: Deliver

**Audit findings**, one block per issue: **Issue**, **Impact**, **Fix**, **Priority**
(High/Medium/Low).

**Impact is qualitative unless the number is sourced.** This repo's no-invented-numbers rule
applies in full: a conversion lift, a drop-off rate or a benchmark appears only if it comes
from the user's own analytics or a specific, linkable study you can name. "Removes a
required field before first use" is a true impact statement; "+20% completion" with no
source is a fabricated one. The same goes for reassurance copy: write "Takes 30 seconds"
only if someone has timed it.

**Recommended changes**, grouped as quick wins (same-day), high-impact changes (week-level),
and test hypotheses. Draw hypotheses from `references/experiments.md`; each one names the
metric it moves from the measurement list in `references/field-guide.md`.

**Form redesign** (only if asked): field set with rationale, field order, copy for labels,
placeholders, buttons and errors, and layout notes.

If funnel data is missing, close with the questions that would unlock a sharper audit:
completion rate, field-level drop-off, data required before first use, compliance
requirements, and the immediate post-submit experience.

## Out of scope here

Post-signup onboarding, lead-capture forms, landing-page CRO and A/B test design are covered
by sibling skills in the upstream marketingskills repo (`onboarding`, `cro`, `ab-testing`),
which this plugin does not ship. Name them to the user rather than improvising those audits.
