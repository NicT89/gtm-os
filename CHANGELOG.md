# Changelog

All notable changes to the GTM OS plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version recorded here must always match the `VERSION` file and the `version`
field in `.claude-plugin/plugin.json`. See [MAINTAINING.md](MAINTAINING.md) for the
release process. Release notes are sourced verbatim from the matching `## [x.y.z]`
section of this file — see MAINTAINING.md for how that extraction works.

## [Unreleased]

## [0.1.0] - 2026-08-17

### Added

Initial public release of the GTM OS template: a configurable, vendor-neutral
AI-native go-to-market engine any team can install and point at their own
CRM/Airtable/Apify instances via `instance-config.json`.

- Five skills: `gtm-signal-scan` (weekly buying-signal sourcing, scoring, tiered
  enrichment, list routing, audit logging), `outreach-audit` (quality gate for
  sequences — personalization depth, merge tokens, honesty rules, A/B discipline,
  configuration defects), `provision-gtm-engine` (provisions the full engine for a
  new deployment from a single company URL, with human gates at ICP sign-off,
  credit spend, and sequence activation), `gtm-blueprint` (composes a motion-classified
  30-day GTM plan behind a configurable CRM field, gated on field completeness),
  and `scrape-linkedin-posts` (LinkedIn post/comment scraping into an Airtable
  posts base, with a digest pushed back into the CRM).
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
