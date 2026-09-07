# Roadmap

Semver discipline: MINOR for additive capability, PATCH for fixes/wording, MAJOR only for breaking changes to how an existing skill is invoked or behaves. Release mechanics: bump VERSION (plugin.json auto-syncs via release.yml), notes from CHANGELOG, push to main.

## Shipped (through v1.6.0)

The structural work the earlier roadmap slotted for v1.4.0 and v1.5.0 has landed. Rather than restate it version by version — the `CHANGELOG.md` is the authoritative per-release record — the current state is:

- **Instance / playbook separation.** Every deployment value (Airtable base/table/field IDs, CRM custom-field IDs, list names, mailbox, field prefix) is a `{KEY}` token resolved once into a local, git-ignored `instance-config.json`. `instance-config.example.json`, `references/instance-config.md`, `scripts/validate_instance_config.py`, and `scripts/setup_status.py` support it. The repo never carries a resolved value.
- **Setup as a first-class module.** `SETUP.md` is the sequence; `references/environment-setup.md` and the `environment-setup` skill are the per-connector procedure and its invocable front door. One setup path, not one per skill.
- **The research spine.** The optional Research Vault base plus `company-deep-research`, `jd-intake`, `gap-closer`, `event-attribution`, `gtm-architecture-composer`, and the fan-out harness, all degrading to report-only when the Vault is absent.
- **Front door.** `CLAUDE.md` opens by routing a reader to USE (SETUP, skills) vs. CHANGE (repo conventions); the portable Airtable posts-base and per-connector guides are documented.
- **Motion selection is a choice, not a default.** The five presets (PLG, enterprise, founder-led, channel, regulated) live in `skills/gtm-blueprint/references/motion-templates.md`, and — new in v1.6.0 — a **custom-motion builder** for companies none of the five fit: the same four-part framework (where pipeline hides, shortest honest path to a conversation, trustworthy reporting, closer) under the same falsifiability standard. `gtm-blueprint` Step 3 presents the classification as a recommendation the human can override, choose a different preset, or send to the custom path.

## Next

- **Persona/motion presets as provisioning defaults.** The presets exist in `gtm-blueprint`; wiring them (and the custom path) into `provision-gtm-engine` as a first-run choice is the remaining half.
- **`commands/` surface:** `/gtm-scan`, `/gtm-audit`, `/gtm-blueprint`, `/gtm-status`, `/gtm-provision` as thin invocations over the skills.
- **`PLAYBOOK.md`:** the "why" layer (signal-based sourcing, tiered enrichment, show-don't-tell, human gates) for buyers and client teams.
- **Per-tool `engine/`-style docs** (Apollo, Apify + Airtable, CB Insights, Brand Kit OS, HubSpot) with a template for extending to a client's stack.
- **Multi-LLM pastable prompt layer; Brand Kit OS fast-signup card integration.**

## Parallel track (not repo-versioned)

Connector directory submission; GTM-layer schema roadmap (ICP+, positioning, objections, signals, attack angles, structured anti-slop).
