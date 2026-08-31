# Changelog

All notable changes to the GTM OS plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version recorded here must always match the `VERSION` file and the `version`
field in `.claude-plugin/plugin.json`. See [MAINTAINING.md](MAINTAINING.md) for the
release process. Release notes are sourced verbatim from the matching `## [x.y.z]`
section of this file — see MAINTAINING.md for how that extraction works.

## [Unreleased]

## [1.5.0] - 2026-08-31

The research spine and the setup module. Everything here is additive: no existing
skill changes how it is invoked, and an install that upgrades and changes nothing in
its config keeps working exactly as before.

Two capabilities land together. The **Research Vault** makes captured research
durable and diffable, so a second run on a company tells you what changed rather
than reading everything again. The **environment setup module** makes wiring the
engine a diagnosis rather than a questionnaire, on the premise that a user who has
not set a tool up has almost always still got the tool.

### Added

- `environment-setup` skill and `references/environment-setup.md` — the single
  canonical setup procedure, replacing per-skill setup prose. It places each
  connector on a five-state ladder (absent / owned but unreachable / reachable but
  unshaped / shaped but unrecorded / wired) and probes before it asks, because
  **not set up does not mean not owned**: the usual gap is a tool the user already
  pays for that has never been shaped for this engine. Only the first state needs a
  signup. Every skill now routes here when a connector it needs is missing.
- `references/research-vault.md` — the persistent research data spine (schema v1.1):
  Entities, Facts, Runs, Questions, plus a Field Keys reference table. Facts are
  append-only with mandatory provenance (source URL or inference tag, source type,
  method, capture date, agent, confidence) and are superseded rather than edited, so
  the set of facts a run superseded *is* its change report. Includes the
  supersede-versus-coexist rule, one-question-per-row and `partial` question status,
  and external-ID columns instead of IDs packed into notes.
- `references/run-manifest.md` — the resumability and cost-budgeting convention. One
  write-ahead JSON manifest per run, updated on every completed step, so a dropped
  connector is a resume rather than a restart. Costs are stated before spend across
  every meter, and a run projected to exceed its cap stops and asks.
- `references/fanout-harness.md` and `scripts/fanout_workflow.js` — parallel research
  across N companies with attribution intact. The orchestrator pre-creates Entity and
  Run rows (entity resolution is the one operation unsafe under concurrency);
  researchers only append; a separate writer stage validates provenance and runs the
  supersede protocol, so the write rules live in one place instead of N prompts.
  Human opt-in and a stated cost statement are required.
- `gtm-architecture-composer` skill — composes the five-layer GTM OS architecture
  (data spine, integration layer, agent workflows, micro apps, observability) and its
  60-day / 6-month / 12-month sequence from a completed intake. Refuses to compose
  from an empty one.
- `gap-closer` skill — works the open-question list: persona-routed batches, a hard
  three-question cap on outreach to a real person, drafts for human sending on
  LinkedIn and email (agents never hold credentials for a person's identity), and
  answers written back as sourced Facts.
- `event-attribution` skill — reconciles an event attendee list against the CRM and
  tags every match, additively, so an account sourced by outbound that later attends
  an event keeps both touches. Turns field spend into something queryable.
- `Tracking` field (`active` / `paused` / `archived`) on the posts base's Contacts and
  Company tables. Scheduled scrape runs touch only `active` rows; manual runs against
  a named target ignore it and report the override. Optional: an existing base with no
  such field behaves exactly as before.

### Changed

- `company-deep-research` now writes to the Research Vault as well as producing its
  report: Vault entity resolution and a Run row before harvesting (Step 1), full
  provenance and the supersede protocol after the verification pass (Step 10), and a
  run manifest opened before the first paid call (Step 0). With the Vault keys empty
  it degrades to report-only and says so.
- `scrape-linkedin-posts` gains two scrape-governance rules: recurring runs honor the
  `Tracking` field, and **every** run — scheduled or manual — ends by rebuilding the
  scrape roster from the live tables rather than patching it incrementally, so the
  roster cannot silently drift away from what a cadence will actually spend on.
- `scrape-linkedin-posts` now carries the version-check preamble every other skill
  already had.
- `SETUP.md` Step 1 is a diagnosis rather than a checklist, and routes through the
  setup module. New optional Step 2b builds the Research Vault base.
- `instance-config.example.json` gains six optional Research Vault keys, two optional
  `Tracking` field keys, and `SCRAPE_ROSTER_ARTIFACT`. All are optional: leaving them
  empty is a supported configuration with documented degradation, not a broken one.
- `scripts/validate_instance_config.py` checks any `AIRTABLE_*_BASE_ID` key for the
  `app` prefix rather than only the posts base by name, so a second base cannot
  silently accept a table ID where a base ID belongs.

## [1.4.0] - 2026-08-17

Initial public release of GTM OS: a configurable, vendor-neutral AI-native
go-to-market engine any team can install and point at their own CRM/Airtable/Apify
instances via `instance-config.json`.

**Why this starts at 1.4.0 rather than 0.1.0.** GTM OS is the generalized form of a
private engine that had already shipped four releases against a live pipeline. The
version line continues rather than restarting, so a version number means the same
thing in both places. The engine is not new; only its public, deployment-neutral
packaging is.

### Added

- Six skills: `gtm-signal-scan` (weekly buying-signal sourcing, scoring, tiered
  enrichment, list routing, audit logging), `outreach-audit` (quality gate for
  sequences — personalization depth, merge tokens, honesty rules, A/B discipline,
  configuration defects), `provision-gtm-engine` (provisions the full engine for a
  new deployment from a single company URL, with human gates at ICP sign-off,
  credit spend, and sequence activation), `gtm-blueprint` (composes a motion-classified
  30-day GTM plan behind a configurable CRM field, gated on field completeness),
  `scrape-linkedin-posts` (LinkedIn post/comment scraping into an Airtable
  posts base, with a digest pushed back into the CRM), and `jd-intake` (turns a job
  description into structured intake against the Known/Unknown status model).
- `SETUP.md` — the first-run walkthrough: connectors, instance config, dry run, and
  the local-vs-repo tokenization rule that keeps deployment values out of git.
- `scripts/render_report.py` — PDF renderer for run reports and onboarding output.
- References carried over from live operation: the onboarding template
  (Known/Unknown status model), the scraping playbook, an MCP coverage map, and a
  dated dependency-observations log recording which third-party behaviors have
  proven intermittent.
- Plugin-wide references: the canonical Apollo credit-cost table and
  score-before-you-reveal rule, the 12-signal buying-intent taxonomy, the portable
  Airtable posts-base schema, and the instance-config key reference.
- `examples/`: a synthetic scan report, audit-log entry, and composed blueprint —
  format anchors showing the shape of real run output without any real data.
- Instance-config system: every deployment-specific ID (CRM custom fields, list
  names, Airtable base/table/field IDs, field-name prefix) is resolved from
  `instance-config.json` at `{CONFIG_KEY}` placeholders in the skill bodies, so the
  same skill text works against any instance. `instance-config.example.json` is the
  template; the real file is gitignored.
- CI (`ci.yml`) validating both JSON manifests parse and every `skills/*/SKILL.md`
  has well-formed frontmatter with `name` matching its directory.
- Release automation (`release.yml`): a `VERSION` bump on `main` syncs
  `.claude-plugin/plugin.json`, tags, and publishes a GitHub Release sourced from
  this changelog.
- Tests for `field_gate.py` and `scripts/validate_skills.py`, run via
  `python3 -m unittest discover -s tests -v`.
