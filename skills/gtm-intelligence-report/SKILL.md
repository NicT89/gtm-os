---
name: gtm-intelligence-report
description: Produce the standard multi-page GTM intelligence report PDF for a prospect or customer: findings with KNOWN/INFERRED/UNVERIFIED labels, segments and reverse ICP, competitive landscape, five-gate product-fit plan, recommendations, 30/60/90 plan, and evidence appendices with highlighted screenshots. Use when the user says "GTM intelligence report", "build the intelligence report", "research report for [company]", "proposal report with evidence", or asks to update a report to a new version.
---

# GTM intelligence report

A branded, versioned PDF in which every claim is label-first and traceable, and every appendix is generated from the engagement database so the text cannot drift from the evidence.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Before building

1. Run the `evidence-register` skill: probe, capture, database. No report without a database that passes `evidence_db.py summary`.
2. Read the engagement's own rules if it has them (project ID, naming, versioning, who sends what). The report carries the project ID, version, status and date on the cover and in every inner-page footer.
3. Gather: calls and transcripts, the customer's site and pricing history (archive snapshots), the competitor reports, the customer list (CRM per `references/hubspot-reverse-icp.md`, else site logos), the open questions.
4. Decide the version: `0.x` unsent drafts, `1.0` first version sent. Never overwrite a version that was shared; write a new file and mark the old one superseded.

## Structure

The default section list, and what each must contain, is in `references/report-structure.md`. Appendices A to F are fixed: web evidence with highlighted screenshots, internal breadcrumbs, claim ledger, one entry per competitor report, open questions with answers, version history with corrections. The plan section always carries the 30/60/90 day plan with a named deliverable per line.

## Build

```bash
cp scripts/config.example.json my-report/config.json     # fill client, project ID, version, palette, fonts, logo
cp scripts/content_template.py my-report/content.py      # write the content; keep it OUT of the plugin repo
# then set "content_module": "content.py" in my-report/config.json (the example names content_template.py)
python3 scripts/build_report.py my-report/config.json
python3 scripts/check_report.py <pdf> --db <db> --project-id <ID> --version <v> --forbid "<individual names>"
```

`check_report.py` must exit 0 before delivery. It blocks em dashes, trailing labels, forbidden names, placeholders, unsourced claims, near-empty pages and a missing project ID or version in any footer. Then rasterize pages (`pdftoppm -r 45`) and look at them: tables that spill, orphan headings and wrapped chart text are visual defects no text check finds.

Branding, fonts and chart rules: `references/branding.md`. Charts: `scripts/charts.py`.

## Writing rules

- Label first: `KNOWN: ... [EV-03]`. Never a trailing label.
- Person-neutral: the company, not the individual. Set `scrub` in the config for known names and titles.
- Conservative on value: a time-saved or revenue figure is an estimate with its basis, shown as an estimate, and never the sole reason for a recommendation.
- Unknowns are `TBD`, not invented. No pricing, tier, term or statistic without a source.
- Gated features (for example a feature sold in one tier only) appear in assets and outreach only for the segment that can buy them.
- Client-facing means no internal strategy, margin or negotiating notes.
- No em dashes.

## Deliver

Name the file `YYYY-MM-DD_client_gtm-intelligence-report_vX.Y_status.pdf`. Store the markdown source and the database dump where the engagement keeps its record, record the version in the manifest, and rebuild the open-questions appendix from the database for every version.
