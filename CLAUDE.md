# Working on this repo

This repo *is* the GTM OS plugin. It ships prose playbooks (skills)
plus a small amount of deterministic tooling. Editing it is editing what every
installed copy executes, so the conventions below are load-bearing.

For the release process, see [MAINTAINING.md](MAINTAINING.md). For what the plugin
does, see [README.md](README.md). This file is the part an agent needs before
changing anything.

## Layout

```
.claude-plugin/    plugin.json + marketplace.json  (version lives in plugin.json)
skills/<name>/     SKILL.md, plus optional references/ and scripts/
references/        plugin-wide references shared across skills
examples/          redacted sample outputs — the format anchors for the skills
.github/workflows/ ci (every push/PR) + release (VERSION change on main)
VERSION            the single source of truth users' version checks read
```

Skill-local `references/` are for one skill. Root `references/` are for material
more than one skill cites — the credit table is the current example. When citing a
root reference from inside a SKILL.md, say "the plugin root's references/..." so it
is not confused with the skill's own folder.

## The rules that CI enforces

- **Both JSON manifests must parse.**
- **Every `skills/*/SKILL.md` needs YAML frontmatter with `name` and `description`,
  and `name` must equal the directory name.** The description is what triggers the
  skill, so it carries the trigger phrases, not just a summary of behavior.

## The rules CI cannot enforce

- **Bump `VERSION` alone; never hand-edit `.claude-plugin/plugin.json`'s version.**
  `release.yml` rewrites the manifest to match `VERSION` and commits it back to
  `main` before tagging. Editing both by hand still works but is redundant, and
  editing only the manifest silently does nothing. There is deliberately no CI
  check that the two match — it would false-fail every release PR. See
  [MAINTAINING.md](MAINTAINING.md).
- **Never commit client data, run artifacts, or audit logs.** Those live in each
  user's own storage and are the personalized layer of the playbook. `.gitignore`
  blocks the common names; that is a safety net, not permission to try.
- **Never commit a credential.** `.env` and `.env.*` are ignored. The audit is
  `git log --all -p | grep -iE 'APOLLO|APIFY|API_KEY'` and it must come back empty.
- **Do not invent numbers.** The skills demand "one hard number, verifiable, true
  for this specific recipient" and forbid fabrication. That standard applies to the
  repo's own documentation too: if a figure for the adopter's own pipeline is not in
  hand, leave the placeholder rather than inventing a plausible one.
- **Keep `README.md` shippable as-is.** It is the README installed copies carry.
  Maintainer-only material goes in MAINTAINING.md or here.

## Editing skills

A `SKILL.md` loads on *every* invocation of that skill; `references/` load only when
the skill reaches for them. That is the whole basis for what goes where:

- SKILL.md holds the decision flow, the gates, and anything needed on every run.
- references/ hold lookup material — field dictionaries, templates, cost tables,
  rubrics — that is consulted at one specific step.

When a SKILL.md grows past roughly 80 lines, that is usually a sign a reference
should be split out rather than that the skill got more complex.

Four structural conventions every skill in this repo follows:

1. **Version check first, never blocking.** Fetch the repo VERSION, compare, notify
   on mismatch, continue.
2. **Human gates are named and explicit.** ICP sign-off, credit spend, and pre-send
   review are gates. Do not add a step that automates past one.
3. **Credit-consuming actions state the total before spending** and report actual
   burn after, costed from `references/apollo-credit-costs.md`.
4. **Everything Claude creates in Apollo carries "[Claude]" in its name.**
   Human-managed assets are never edited.

## Scripts

`skills/gtm-blueprint/scripts/field_gate.py` is the model: standard library only, a
docstring with usage, meaningful exit codes (0 pass / 1 fail / 2 usage error), and
JSON on stdout so results are loggable to the audit trail. New scripts should match
that shape and ship with tests under `tests/`.

Run the tests with `python3 -m unittest discover -s tests -v`.

## Connectors

Apollo is required; Apify, Airtable, Google Drive, and CB Insights are optional and
each skill degrades explicitly when one is missing rather than guessing. Note that
interactively-authenticated MCP connectors may be unavailable in headless or
scheduled runs — a skill that hard-stops on a missing connector will hard-stop
there, which is correct behavior but worth knowing when scheduling a run.
