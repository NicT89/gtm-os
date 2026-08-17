# Roadmap

Semver discipline: MINOR for additive capability, PATCH for fixes/wording, MAJOR only for breaking changes to how an existing skill is invoked or behaves. Release mechanics: bump VERSION (plugin.json auto-syncs via release.yml), notes from CHANGELOG, push to main.

## v1.3.0 (this release)
Signals doctrine (12-signal taxonomy), org_ids boundary rule, catch-all hard exclusion, run-shape JSON artifacts, credit-frugality as standing principle, plus the comparison-branch quality work (credit reference, CI, examples, repo conventions).

Also landed early, ahead of their v1.4.0 slot:
- Release-notes unification: `release.yml` now extracts the matching `## [x.y.z]` CHANGELOG section. `CHANGES-<version>.md` is deprecated (still read as a fallback); fold the two remaining files into CHANGELOG.md and delete them.
- `references/airtable-posts-base.md`: the portable posts-base schema (tables, field types, link wiring, build order, fields not to create) — the client-facing half of the Airtable instance separation. The ID block in `scrape-linkedin-posts` is now explicitly labelled instance-specific and points here.

## v1.4.0: instance/playbook separation + operator UX
- THE structural change: extract all instance-specific values (Airtable base/table/field ids, Apollo custom-field ids, list names, mailbox, closers/voice lines) out of skill bodies into one generated instance config; skills reference config keys; provision-gtm-engine writes the config per deployment. Unlocks clean client installs. Start with `scrape-linkedin-posts` (45 IDs, the largest single concentration) now that its schema is documented separately.
- Per-connector setup guides matching `references/airtable-posts-base.md`, for Apollo custom fields and lists, and CB Insights.
- Persona/motion mode presets (founder-led, PLG, enterprise/ABM, channel, regulated) as provisioning defaults.
- commands/ surface: /gtm-scan, /gtm-audit, /gtm-blueprint, /gtm-status, /gtm-provision.

## v1.5.0: front door + enablement
- Top-level CLAUDE.md interactive onboarding (persona assessment -> mode -> workspace scaffold -> connector walk-through), reframing provisioning as first-run experience.
- PLAYBOOK.md: the "why" layer (signal-based sourcing, tiered enrichment, show-don't-tell, human gates) for buyers and client teams.
- engine/-style per-tool docs (Apollo, Apify+Airtable, CB Insights, Brand Kit OS, HubSpot) with a tool template for extending to a client's stack.
- Multi-LLM pastable prompt layer; Brand Kit OS fast-signup card integration.

## Parallel track (not repo-versioned)
Connector directory submission; GTM-layer schema roadmap (ICP+, positioning, objections, signals, attack angles, structured anti-slop).
