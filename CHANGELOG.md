# Changelog

All notable changes to the GTM OS plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version recorded here must always match the `VERSION` file and the `version`
field in `.claude-plugin/plugin.json`. See [MAINTAINING.md](MAINTAINING.md) for the
release process. Release notes are sourced verbatim from the matching `## [x.y.z]`
section of this file — see MAINTAINING.md for how that extraction works.

## [Unreleased]

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
