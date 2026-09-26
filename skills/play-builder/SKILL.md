---
name: play-builder
description: Define, edit and build a deployment's plays, the routes that decide which accounts go to which list, sequence and persona. Use when the user says "create a play", "build my plays", "run play-builder", "define my outbound motions", "set up routing", "add a new play", "change my entry criteria", "which fields do I need in Apollo", or when gtm-signal-scan stops because no plays file exists, or provision-gtm-engine reaches signal design. Interviews for each play in the organization's own words against written guidance, writes and shape-checks the plays file, links each play to scoring, and, only with approval, creates the standard Apollo fields, lists and inactive sequences each play needs.
---

# Play builder

A play is one outbound route: the situation that qualifies an account, the persona written
to, and the Apollo objects it owns. What a play is, how the scan assigns one, and the naming
rule are in the plugin root's `references/plays.md`; this skill builds them.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION and compare it to the
VERSION file at the plugin root. If they differ, say an updated version is available, then
continue.

## What it needs

Nothing to write the plays file. The Apollo connector for Step 5; without it, Step 5 produces a
UI checklist instead of creating anything, and says so. For setup of any connector, route to
the `environment-setup` skill.

## Step 1: Start from what exists

Read the deployment's plays file (`{PLAYS_FILE}`) if there is one. If Apollo is connected, list
the existing sequences and lists, read-only. **Not set up does not mean not owned**: most teams
already run routes they have never written down. Turn those into plays before inventing new
ones, keeping the team's own names for the situations they describe.

## Step 2: Write each play in the organization's words

One play at a time. For every free-text field (entry criteria, evidence to check, exit
criteria, persona, angle), draft from the operator's description against the guidance in
`references/play-fields.md`, and show the draft beside that field's bar. **Never offer a list of
criteria to pick from**: plays differ between organizations, and an enumerated menu forces one
company's axes onto another. The guidance is what keeps free text precise.

Then run the field's test: apply the drafted criteria to two or three real or example accounts
and confirm the play decision is unambiguous. Where two plays fit the same account, settle it
with `priority` and say so in the higher play's criteria.

## Step 3: Write and check the file

Write the plays file, then run `scripts/check_plays.py <file>` in this skill's folder. It checks
shape only (codes, priority, naming rule, known standard fields, criteria written as a
sentence), never content. Fix every problem. Set `"provenance": "deployment"` only when the
operator confirms these are decisions, not drafts.

## Step 4: Link each play to scoring

Every play needs its `play_fit` points in the scoring config (`{SCORING_CONFIG_FILE}`). Run
`gtm-signal-scan`'s `scripts/score.py --check-config <scoring file> --plays <plays file>`; a play
with no entry would score 0 without anyone deciding it should.

## Step 5: Build the Apollo objects (each one approved first)

- **Fields:** the standard set once, then each play's custom fields, per
  `references/standard-fields.md`, which carries the creation procedure and its read-back. The
  first live creation is one field, read back, before any more.
- **Lists:** the play's account and contact lists (`apollo_labels_create`), named exactly as in
  the plays file. Check for an existing list of that name first.
- **Sequences:** `apollo_sequences_create`, always **inactive**, named as in the plays file,
  after `apollo_emailer_campaigns_search` finds no duplicate. Step content follows
  `provision-gtm-engine` Phase 2 and is audited by `outreach-audit`. **Activation is a human
  gate and this skill never performs it.** Existing sequences are renamed in the UI only
  (`references/plays.md` says why).
- **Workflows:** a UI checklist per entry in the play's `workflows`, then verify by reading the
  fields it fills on one record.

Read back every write and report the IDs. Never edit a human-managed asset; everything created
here carries "[Claude]" in its name.

## Step 6: Prove it before a live scan

Run the offline demo in preview mode (`gtm-os-demo`, `python3 <plugin root>/scripts/demo.py
--config instance-config.json`). Clear its blocking findings. Report what was built, what is
still a UI step, and which plays remain drafts.
