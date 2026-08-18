---
name: company-deep-research
description: Deep-research any company end to end and produce a sourced report: site sweep, funding and M&A history, GTM org map, named customers, partner taxonomy, competitors, and public code footprint. Use when the user says "deep research [company]", "run company-deep-research", "research this company", "do a full workup on [company]", "who are their customers", "who do they partner with", "who are their competitors", "what is their tech stack", "map their GTM org", "how big is their sales team", shares a company URL and asks what the company actually does, or when jd-intake or gtm-signal-scan leaves Unknown template fields that extended search can close. Sitemap-first extraction, primary-source funding and M&A verification, department and seniority counts, proof points with hard numbers, partner classification (API integration vs embedded/OEM vs channel), and GitHub / package-registry footprint.
---

# Company Deep Research

Input: a company name, domain, or URL, optionally with a partially completed onboarding template from `jd-intake`. Output: a sourced research report, the template's Extended Search column filled with attribution, and an Ask list of what only the company can answer. Nothing is guessed. Every hard fact carries a source URL, every vendor estimate is labeled directional, and every unverifiable claim becomes an Ask instead of a sentence in the report.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Connectors and degradation

Firecrawl is the default extractor for everything on the web; see the plugin root's `references/scraping-playbook.md` for the extraction rules and why markdown is the storage format. Without it, fall back to search and plain fetch and state the degradation in the report: JS-rendered pages (ATS, app-shell marketing sites, docs portals) return page metadata and zero content on a plain fetch, so an empty extraction means "not extracted", never "not present". Without a CRM connector, the org map comes from the site and public profiles only and every count is reported Unknown rather than estimated. A missing connector narrows the report; it never licenses a guess.

## Step 0: Scope and cost gate (human, before any paid call)

Name the target, the sections in scope, and the TOTAL spend before spending it, costed from the plugin root's `references/apollo-credit-costs.md`: org enrichment and job postings (1 credit per company each), people match (1 credit per matched person, and only after the free people search has ranked reachability), Firecrawl scrape/search credits, and actor spend if Step 8 runs. Search is free and reveals are not, so rank the whole org for free and spend only on the people the run actually needs. Report actual burn by category at the end, not just a total.

## Step 1: Entity resolution and merge-artifact check

Resolve to ONE legal entity before harvesting anything, and record the rebrand and acquisition chain as aliases on that single entity rather than as separate companies. When two entities are plausibly in scope (a parent and an acquired brand still trading under its own name), put both in front of the human and let them pick; researching the wrong one is a whole run wasted.

Treat any enrichment-vendor org record for a company that merged, was acquired, or rebranded in the last ~24 months as a merge artifact until each field is verified against a primary source. This rule is from a live run: a vendor record for a B2B software company that had just acquired a smaller startup interleaved the acquired company's seed rounds into the acquirer's funding history and still pointed the LinkedIn URL at the acquired company's page. Cited as-is, outreach would have credited the wrong investors to the wrong company to the one reader who knows better. Duplicated stack categories after a merger (two warehouses, two CRMs, two ticketing systems) are evidence of unmerged heritage, not a contradiction to resolve: they become Asks.

## Step 2: Site sweep, sitemap first

Enumerate URLs from the sitemap before scraping anything, so the sweep is driven by what exists rather than by guessed paths. Scrape in priority order, storing each page's markdown as the audit copy: pricing (classifies the motion), product/platform and services or plans (the services page is often the real contract-level catalog and the upsell map's raw material), customers and case studies, partners and integrations, about and team, careers index, docs and developer portal, newsroom and blog for the last 6 months, and legal/terms (which names the legal entity). Motion classification from the pricing page: quote calculator or contact form means sales-led, card checkout means PLG, both means a hybrid with a self-serve wedge, and a fast-install path alongside enterprise contact forms is a wedge worth stating explicitly. Full evidence table in `references/harvest-rubrics.md`.

## Step 3: Funding and M&A from primary sources

The company's own newsroom and the investor's press release outrank every aggregator. Capture rounds with date, amount, named lead investors and any board seats taken; acquisitions in BOTH directions with close date and stated rationale; and the current legal entity with its rebrand date. Every funding fact carries the primary-source URL, not the aggregator's. Absolute dates only ("in March 2026", never "recently"). A fact that exists only on an aggregator is reported as such, with its capture date, and is a candidate Ask.

## Step 4: Org map: departments, seniority, and the chain

Run free people search by department and seniority band (C-suite, VP, Director, Manager, IC) and report counts as "N people indexed by <source>", never as headcount: index coverage is partial, and a gap against the company's own stated headcount is coverage, not shrinkage. State the headcount trend separately when the enrichment record carries one, labeled directional.

Then read the org for shape, which is what the report is actually for: which functions are one person deep, which are hiring, which have no owner at all, and who the GTM leadership chain runs through. Identify the likely sponsor or hiring manager for any open req in play; the interpretation rules for department shape are in `references/harvest-rubrics.md`. A title that appears in a JD or on the site but that no public source confirms is an Ask, never a fact.

## Step 5: Named-customer proof-point harvest

Rank sources by strength per the tier table in `references/harvest-rubrics.md`: a case study with a named customer AND a hard metric is a proof point; a press release naming customers is a proof point without a metric; a logo wall is neither and is recorded only as claimed adoption. For each proof point capture customer name, source URL, capture date, and the metric verbatim with its unit and period. A metric with no named customer, or a named customer with no metric, is half a proof point: record what you have and mark the other half Unknown. These land in outreach copy, where a wrong number is more expensive than a missing one.

## Step 6: Partner taxonomy

Classify every named partner or integration as API integration, embedded/OEM/white-label, or channel/referral, using the disambiguation tests in `references/harvest-rubrics.md`. The rule that makes this step non-obvious: **scrape the partner's own site, not just the target's.** Embedded relationships are routinely presented on the partner's marketing page as the partner's own technology and disclosed only in an FAQ, a legal page, or a co-published report. A live run found exactly that: the target's scoring engine ran inside a larger platform's own workflow and was credited only in that platform's FAQ, which changed the classification from "competing option" to "distribution surface" and with it the whole account strategy.

## Step 7: Competitor set and code footprint

Competitors: build the set from the company's own comparison and alternatives pages, analyst/database comparison pages, and review-site category placement, then split it three ways per `references/harvest-rubrics.md`. Head-on competitors sell the same job to the same buyer. Adjacent vendors overlap on one feature but sell a different job, and a partner that ships a native version of one feature is not automatically a competitor. Record the company's own stated differentiation claim verbatim; it is their positioning, not your assessment.

Code footprint: search for the org under current AND former names, plus package registries (npm, PyPI, Packagist, platform marketplaces) and the developer docs subdomain. Public repos leak which platforms get first-party integration modules, which infrastructure is in use (a payments vendor's public org exposed its Terraform and Helm configs, naming its cloud provider and deployment shape before a single call), and which employee accounts follow a company naming pattern. Product code is usually private; the public shell still maps the engineering surface. Full method in the scraping playbook's code-footprint section.

## Step 8: People and events pass (optional, human gate)

For the 2-3 most GTM-relevant people, run `scrape-linkedin-posts` and respect its caps, its authored-post filter, and its breadcrumb human gate. This pass earns its cost when it surfaces channels the website does not: recurring field events with host cities and named venues, internal tool launches, and the ecosystem the team actually operates in. Event channels carry attribution questions that become Asks. Never auto-expand to second-degree targets.

## Step 9: Assemble, verify, deliver

Compose the report against `references/output-contract.md`, which fixes the section order, the per-section content, and the standing rules (source URL plus capture date on every fact, absolute dates, directional labels on vendor estimates). Then run the verification pass BEFORE delivery, as a distinct step: every number traced to its source URL, every date absolute, every vendor estimate labeled directional, every unverifiable claim moved into the Ask list, and every section that came back empty marked "not extracted" with the method that failed rather than reported as "none". Render the human-facing version through the plugin root's `scripts/render_report.py`.

Unknown template fields that research closed move into the Extended Search column with source and capture date; the status stays as the source document left it. Remaining Unknowns become Asks phrased ready to use in a call.

Writeback is gated and optional. With a CRM connected (`{CRM_PROVIDER}`) and the human's approval, write the condensed digest to the Research Company Profile field `{APOLLO_CF_CONTACT_RESEARCH_COMPANY_PROFILE}` for contacts on that account, resolving the key from `instance-config.json` per the plugin root's `references/instance-config.md`. If a CRM-side AI field already populates it, do NOT overwrite: reconcile, and flag any disagreement between this research and the AI field output for the human. If the key is missing, report the mapping and skip the write rather than guessing a field.

Log the run, the credit burn, and any tool behaving differently than documented (dated) to the plugin root's `references/dependency-observations.md`.
