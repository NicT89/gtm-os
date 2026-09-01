# GTM OS

**An AI-native go-to-market engine you run yourself, as an installable Claude Code plugin.**

GTM OS sources companies through buying signals, enriches them in tiers, prepares
research-grounded personalization, and audits every outreach asset before a single
email sends. You point it at your own CRM, Airtable, and scraping accounts; it never
ships with anyone else's.

The pattern was built and operated against a live pipeline before it was packaged.
Every gate and defect check in this repo traces back to something that actually broke
in production — the deprecated field that silently wrote a false "no posts" verdict,
the catch-all addresses that damaged a sending domain, the workflow that reported
success while matching nobody.

## Install

```
/plugin marketplace add NicT89/gtm-os
/plugin install gtm-os@gtm-os
```

Then run through [`SETUP.md`](SETUP.md) — connectors, the Airtable posts base, and
`instance-config.json`. Nothing works until that config is filled in, and that is
deliberate: a skill that guessed at an ID would write your data into someone else's
workspace.

Or just say **"set up my environment"** and let the `environment-setup` skill drive it.
It diagnoses what you already have before it suggests anything, which matters because
**not set up almost never means not owned** — the usual situation is that you have the
tool and have simply never shaped it for this engine. The per-connector procedure is
[`references/environment-setup.md`](references/environment-setup.md), and every skill
routes there when a connector it needs is missing.

## What it does

| Skill | What it does |
|---|---|
| `gtm-signal-scan` | Weekly sourcing run: signal search, scoring, tiered enrichment, account/contact creation, list routing |
| `gtm-blueprint` | Composes a motion-classified 30-day GTM plan per target company, behind a hard field-completeness gate |
| `outreach-audit` | Quality gate before enrollment: personalization depth, merge tokens, honesty rules, A/B discipline, config defects |
| `provision-gtm-engine` | Provisions the whole engine for a company from a single URL: context brief, ICP, fields, lists, sequences |
| `scrape-linkedin-posts` | Scrapes posts and comments into an Airtable base and pushes a digest back to the CRM. Standalone, batch, or scheduled |
| `jd-intake` | Turns a job posting into structured intake: Known/Unknown per field, an extended-search list, and interview questions |
| `company-deep-research` | Full sourced workup on a company: site sweep, funding and M&A, org map, customers, partners, competitors, code footprint |
| `gtm-architecture-composer` | Composes the five-layer GTM OS architecture and its 60-day / 6-month / 12-month sequence from a completed intake |
| `gap-closer` | Works the open-question list: persona-routed batches, drafts for human sending, answers written back as sourced facts |
| `event-attribution` | Reconciles an event attendee list against the CRM and tags every match, so field spend stops being unattributable |
| `environment-setup` | Diagnoses and wires the connectors, from whatever state you are already in |

## Who this is for

**A good fit** if you run outbound yourself, want the machine to be inspectable, and
would rather own a system than rent a dashboard. You will be comfortable in a terminal
and willing to create custom fields in your CRM.

**A poor fit** if you want a no-code product, a managed service, or something that
works without configuring your own connectors. The setup is real work — an afternoon,
not a click.

## Operating principles

These hold across every skill, and they are the reason the engine is trustworthy
rather than merely fast:

1. **Show, don't tell.** Every outreach claim must be true for the specific recipient
   and grounded in captured research. If an email could be sent to a different company
   unchanged, it has failed.
2. **Human gates never automate away.** ICP sign-off, credit spend approval, and
   pre-send review are gates, not steps.
3. **Credit-consuming actions state their cost first** and report actual burn after.
   Search is free; reveals are not. Ranking happens before spending.
4. **Everything the agent creates is labeled**, and human-managed assets are never
   edited by it.
5. **Every run appends to an audit log**, and every defect found becomes a permanent
   gate rather than a silent patch.
6. **Conversation memory is never the system of record.** Facts land in the Research
   Vault with source, method, capture date, and confidence, and they are appended and
   superseded rather than edited or deleted. Re-running research is then a mechanical
   diff: the set of facts a run superseded *is* the change report.

## Connectors

- **CRM** (required) — Apollo is the reference implementation: signal source, CRM,
  enrichment, sequences, analytics.
- **Apify** (required *for post scraping*) — LinkedIn post and comment scraping.
  Skills that do not scrape run without it.
- **Airtable** (required *for the posts base*) — the posts archive. Build it from
  [`references/airtable-posts-base.md`](references/airtable-posts-base.md). A second,
  optional base is the **Research Vault**
  ([`references/research-vault.md`](references/research-vault.md)): the persistent
  research spine where every captured fact lands with its source, method, and
  confidence. Without it the research skills still produce their reports; they just
  cannot tell you what changed since last time.
- **CB Insights** (optional) — funding stage, named investors, commercial maturity.
- **Brand Kit OS** (optional) — supplies structured brand voice, positioning, and
  audience data as the seller-side context that `gtm-blueprint` composes against.
  Without it, the engine falls back to your CRM's context center or a document you
  name.
- **Google Drive / Box / OneDrive** (optional) — file home for briefs and audit logs.
  A local folder works too.

## What output looks like

[`examples/`](examples/) holds a sample scan report, audit-log entry, and composed
blueprint. Every company and figure there is synthetic; real run artifacts live in
your own storage, never in this repo.

Cost discipline is documented in
[`references/apollo-credit-costs.md`](references/apollo-credit-costs.md), including
the score-before-you-reveal rule that keeps burn down.

## Versioning

Canonical source: <https://github.com/NicT89/gtm-os>

Every skill compares this repo's `VERSION` against your installed copy on invocation
and tells you when an update exists. **It notifies; it never blocks, and it never
auto-updates** — re-run the install flow to pull a new version.

## License

GTM OS is released under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**.

- **Noncommercial use is free** — personal use, learning, research, and use by
  nonprofit, educational, or government organizations. Keep the notices intact and
  credit the source (see [`NOTICE`](NOTICE) for the exact line).
- **Commercial use requires a separate license.** Running it on client pipelines,
  bundling it into a paid offering, or operating it inside a for-profit company are
  commercial purposes. Requests are welcome — the terms exist to prevent silent
  commercial copying, not to prevent commercial use.

Contact **Nicolas Thatcher — nthatcher@realblockai.com** to arrange one, or with any
question about which side of the line you are on.

Copyright © 2026 Nicolas Thatcher, Launch99 Agency.
