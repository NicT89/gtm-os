---
name: jd-intake
description: Extract a job description from any URL and map it onto the GTM onboarding template. Use when the user says "run jd-intake", "extract this JD", "map this job description", "intake this role", shares a job posting URL for analysis, or when provision-gtm-engine or the hiring signal motion needs a structured JD. Produces the verbatim extraction, the field-by-field template mapping with Known / Unknown status plus Extended Search and Ask columns, the extended-search task list, and the interview-question list.
---

# JD Intake

Input: one job posting URL. Output: the verbatim JD, a structured mapping onto the onboarding template, and two work queues (researchable gaps, must-ask questions). Nothing is guessed; every field is sourced or flagged.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Step 1: Extract (Firecrawl first, always)

Scrape the URL with Firecrawl, markdown format, onlyMainContent true, waitFor 5000, maxAge 0. ATS pages (Gem, Ashby, Lever, Greenhouse embeds) are client-side rendered JavaScript apps: a plain fetch returns page metadata with zero JD content, so Firecrawl with the JS wait is the DEFAULT, not the fallback. See the plugin root's references/scraping-playbook.md for the full extraction rules, including why markdown is the storage format.

Capture verbatim, preserving section structure: title, location, work arrangement, compensation, about-company, about-role, responsibilities, requirements, stack, success milestones, values, EEO entity name (it reveals the legal entity), and the req ID.

Present the extraction to the human for approval before mapping. A mapping built on a bad extraction is worthless.

## Step 2: Sibling postings (org intel for free)

Scrape the same careers index page and list every open role with team and location. Sibling reqs are org structure leaking: two AE segments hiring means pipeline pressure, an offshore analyst req reveals a delivery pod, an engineering req names the product stack. Cross-check job boards (Built In, Ladders) for the same req; they often publish structured tool tags the ATS hides, but verify per-listing attribution, since category pages put adjacent listings' tags next to the wrong logo.

## Step 3: Map onto the onboarding template

Read the plugin root's references/onboarding-template.md and walk EVERY field in order, applying its two-status rubric:

- **Known**: the JD itself answers the field (quote or tight paraphrase, with the JD section named)
- **Unknown**: the JD does not answer it

Then populate the two columns independently of status:

- **Extended Search**: for Unknown fields, emit an ES-# task naming the method (site scrape, Apollo search, press release, review sites, GitHub footprint); for Known fields, record any enrichment research added, with source and date
- **Ask**: one or more ready-to-use questions per field that only the company can answer; a Known field can still carry Asks when the JD's answer is ambiguous (scope, location, reporting lines)

Two standing rules: mark inferences "(inferred)", and treat titles or claims in the JD that cannot be verified publicly as Ask entries, not facts (a JD can name a "Director of X" who does not exist yet).

## Step 4: Deliver

Produce the mapping document (the onboarding template with statuses, values, and sources), the ES task list grouped by research method, and the ASK list.

When the CRM is connected, write the structured JD summary to the account's JD Summary field `{APOLLO_CF_ACCOUNT_JD_SUMMARY}` and the role list to GTM Jobs w/ URL `{APOLLO_CF_ACCOUNT_GTM_JOBS_WITH_URL}` IF those fields are not populated by the account's own CRM-side AI field runs; when the AI fields already populate them (they are triggered by adding the account/contact to the configured list), do not overwrite, reconcile: flag any disagreement between this extraction and the AI field output for the human. Resolve both keys from `instance-config.json` per the plugin root's references/instance-config.md; if a key is missing, report the mapping to the human and skip the write rather than guessing a field.

For the human-facing deliverable, render the mapping through the plugin root's scripts/render_report.py with the onboarding template (consistent format, status colors, PDF output). See SETUP.md for the render environment.

## Downstream

The ES task list is the research plan for company research (or provision-gtm-engine Phase 0). The ASK list feeds the first call or interview. The mapping document is the spine an architecture proposal composes from.
