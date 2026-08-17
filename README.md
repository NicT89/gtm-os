# GTM OS

An open, configurable AI-native go-to-market playbook, packaged as a deployable plugin. Your team runs the machine; this plugin builds it.

The engine sources companies through buying signals (GTM hiring, fresh funding), enriches them in tiers, prepares research-grounded personalization, and audits every outreach asset before a single email sends. The pattern was built and operated against a live pipeline before being packaged as a template: every gate and defect check in this repo traces back to something that actually broke in production.

## Skills

| Skill | What it does |
|---|---|
| gtm-signal-scan | Weekly sourcing run: signal search, scoring, tiered enrichment, account/contact creation, list routing |
| outreach-audit | Quality gate for sequences: personalization depth, merge tokens, honesty checks, A/B discipline, config defects |
| provision-gtm-engine | Provisions the full engine for any company from a single URL: context brief, ICP, fields, lists, sequences |
| gtm-blueprint | Composes the customized 30-day GTM plan behind the `<prefix> Blueprint` field (prefix set by `{INSTANCE_FIELD_PREFIX}`): motion classification, field-completeness gate, motion-specific templates |
| scrape-linkedin-posts | Scrapes LinkedIn posts and comments for a person or company, writes them into the Airtable posts base, and pushes a summary back into Apollo. Runs standalone, in batch, or on a schedule; also called by gtm-signal-scan Step 6 |

## Credits

Every skill that spends Apollo credits states the total before spending and reports
actual burn afterward. Search is free; reveals are not. See
[references/apollo-credit-costs.md](references/apollo-credit-costs.md) for the full
cost table and the score-before-you-reveal rule that keeps burn down.

## What the output looks like

[`examples/`](examples/) holds a sample scan report, audit-log entry, and composed
blueprint, so you can see the shape of what a run produces before you run one. Every
company and figure in that folder is synthetic; real run artifacts live in your own
storage, never in this repo.

## Required connectors

- **Apollo** (required): signal source, CRM, enrichment, sequences, analytics. Sign in with a work email; model training must be off.
- **Apify** (required): LinkedIn posts and comments scraping (harvestapi/linkedin-profile-posts), used by the scrape-linkedin-posts skill.
- **Airtable** (required): posts archive base for scraped LinkedIn posts, comments, and their links back to contacts/accounts. Used by scrape-linkedin-posts and read by gtm-signal-scan Step 6.
- **Google Drive** (optional): canonical file home for briefs, JD library, and audit logs. Local folder storage works as the alternative; Box or OneDrive are supported substitutes.

## Versioning

Canonical source: https://github.com/NicT89/gtm-os

Every skill checks the repo's VERSION file against the local copy on invocation and notifies you when an update is available (it never blocks work). For belt-and-suspenders freshness, create a monthly scheduled task in your Claude instance: "Compare the VERSION file at https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION against the locally installed gtm-os plugin version and notify me if they differ."

## Operating principles (apply across all skills)

1. Show, don't tell: every outreach claim must be true for the specific recipient and grounded in captured research.
2. Human gates never automate away without measurement: ICP sign-off, credit spend approval, and pre-send quality review.
3. Credit-consuming actions are confirmed with the user before spending, with totals stated upfront.
4. Everything Claude creates in Apollo carries "[Claude]" in its name; human-managed assets are never edited.
5. Every run appends findings to a local audit log; fixes become permanent gates, never silent patches.

## File home

On first use, choose where run artifacts live: a local folder Claude structures for you, or Google Drive (same structure, accessible across devices). Audit logs and feedback loops are stored locally per user; they are the personalized layer of the playbook and are never shared with the repo.

Copyright [Your Organization]. Fill in your own copyright line and distribution terms before shipping this to your own clients or partners.
