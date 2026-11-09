---
name: gtm-onboard
description: Onboard a company onto GTM OS from zero, in order, with the gates named. Use when the user says "onboard [company]", "set up GTM OS for [company]", "start a new client", "run gtm-onboard", "set up the workspace", "we just installed the plugin, what now", "set up the project for GTM OS", or when provision-gtm-engine finds no workspace. Audits connectors through environment-setup (every GTM OS connector is a strong recommendation; a declined one is recorded with its fallback), detects whether the session is Cowork with a folder, a Claude Project, or plain chat, renders the Project instructions to paste, lays down the workspace, audits its shape with a script, fills brand context from Brand Kit OS or from a site scrape plus interview into provenance-labeled files, hands off to provision-gtm-engine Phase 0, and creates the default scheduled tasks last, paused, after a live-fire run.
---

# GTM onboard

The front door for a new deployment. One sequence, run top to bottom, with each gate named
so nothing is automated past it. Everything it lays down is described in the plugin root's
`references/workspace-schema.md` and `references/brand-context.md`; this file is the order
and the gates.

## Version check (run first, never block)

Run the check in the plugin root's `references/version-check.md` (three sources in order, three outcomes, never blocks) and continue.

## Step 0: Connectors, through environment-setup

Run the `environment-setup` skill. It diagnoses what is already connected before suggesting
anything. The policy this skill adds on top: **every GTM OS connector is a strong
recommendation, not a requirement.** For each one that is absent, say what it adds and what
the engine does without it (the fallback column in `references/environment-setup.md`), and
ask the user to connect it now or decline it. A decline is recorded in `_index/instance.md`
with the fallback that deployment runs on, and the engine never nags about it again; a
later `environment-setup` run is how it changes. Brand Kit OS is recommended in the same
terms: with it, brand context is live and governed; without it, Step 4 builds files.

## Step 1: Where this session is

Detect, do not ask: folder tools present means Cowork with a connected folder; a Projects
tool that reports a project name means a Claude Project is attached; neither means plain
chat. Ask only when the signals conflict. Plain chat with no folder and no Project stops
here with two sentences: open this chat in Cowork with a folder connected, or attach a
Project, then say "onboard" again. The workspace root is the connected folder (Cowork) or
the working directory (Claude Code); a Project, when attached, receives copies of `_index/`.

## Step 2: Project instructions (paste gate)

When a Project is attached: collect the inputs `scripts/render_project_instructions.py`
names (company, instance name, field prefix, CRM provider, connector states from Step 0,
brand context source, the path to `instance-config.json`, and the organization's own rules
in their words), render, and show the block. **The user pastes it; the skill waits.** Confirm
through `project_info` that the instructions field is no longer empty before continuing,
and pass that result to the audit in Step 3. No Project: skip, and say the same rules live
in the workspace's `_index/overview.md` instead.

## Step 3: Workspace, then the audit gate

Create the folders and `_index/` files in `references/workspace-schema.md`, write
`_index/instance.md` (states, fallbacks, paths; never an identifier), and the ten brand
files with front matter and empty bodies. Then:

```bash
python3 <plugin root>/scripts/check_workspace.py --workspace . --brand-dir {BRAND_CONTEXT_DIR} --instructions-pasted yes|no --json
```

Exit 1 stops the sequence; fix what it names and run it again. Record the passing JSON in
`audit-log/`. Nothing is written into the brand files until this passes.

## Step 4: Brand context

With the Brand Kit OS connector: `get_agent_briefing`, record the kit in `_index/instance.md`,
and leave the brand folder empty with `source: brand-kit-os` in each file's front matter.
Without it: state the Firecrawl credit count, scrape the site as `provision-gtm-engine`
Phase 0 does, and write what the site states into `company-profile`, `products`,
`audiences` and `proof-and-quotes`, each fact KNOWN with its URL or INFERRED with the
clause. Then interview for what a site cannot say, one entity at a time: voice and
expression, personas, objections, governance (what is never said or claimed). Each answer
is KNOWN from the named person and date. Run the audit again; it now checks every fact's
label. Say once that the files are the fallback and the connector is the live version.

## Step 5: Stack audit, then Phase 0

The stack audit (Apollo context center, fields, labels, sequences; HubSpot scopes,
pipelines, properties, source tags) ships as its own skill in a later release. Until it
exists, write "stack audit: not built in this version, skipped" to the audit log and say
so. Then hand off to `provision-gtm-engine` Phase 0, which reads `company-profile.md` rather
than scraping twice. Gate 1 (ICP sign-off) is that skill's and is unchanged.

## Step 6: Scheduled tasks, last and paused

Three defaults, created paused: weekly `gtm-signal-scan`, monthly `scrape-linkedin-posts`
refresh of active-tracked contacts, monthly brand-context drift check (site against the
brand files; reports, writes nothing). Enrichment and enrollment are never scheduled. Before
any task is switched on, run it once against one target in a fresh headless session and
show the PASS/FAIL against real system state; a task is switched on only after its own run
passed. Every task carries the failure rule: on a connector-auth failure it stops, writes
the audit log entry, and reports a diagnosis with the fixes; it retries once in the same run
only when the diagnosis says a re-run can fix it, and otherwise stays paused for a person.

## When Brand Kit OS arrives later

If a deployment ran on files and the connector is connected afterwards, offer the import in
`references/brand-context.md`: one entity at a time, dry run shown, then confirmed, with
each label mapped to the kit's `basis`. Afterwards the files are marked `source:
brand-kit-os` and no longer read.

## What this skill never does

It never writes to a Project (the user pastes), never creates a scheduled task before its
live-fire run passed, never spends a credit without stating the total, never records an
identifier in `_index/`, and never claims a step it skipped.
