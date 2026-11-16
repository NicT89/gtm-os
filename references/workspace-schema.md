# The deployment workspace

What `gtm-onboard` lays down for a deployment, and what `scripts/check_workspace.py`
checks before any brand context is written. One workspace per deployment. In Cowork it is
the connected folder; in Claude Code it is the working directory; when a Claude Project is
attached, the `_index/` files are also uploaded to the Project so a plain-chat session can
read them. The two never hold different truths: the filesystem is the source and the
Project carries copies.

## Folders

```
instance-config.json   the resolved config; filesystem only, never in the Project
{BRAND_CONTEXT_DIR}/   brand context as files (references/brand-context.md); always present.
                       With the Brand Kit OS connector on, the ten files carry
                       `source: brand-kit-os` and empty bodies, and are not read
_index/                the small set of files every session reads first
  instance.md          instance name, prefix, CRM provider, connector states and fallbacks,
                       brand context source, the PATH to instance-config.json. No IDs.
  overview.md          one page: what this deployment is, who operates it, current stage
  pending-tasks.md     open items by owner; the only live task list
runs/                  one file per engine run (signal scans, scrapes, blueprints)
audit-log/             append-only; every finding becomes a gate or a step
sequences/             sequence drafts and their analytics
research/              company research, JD intake, evidence, reports
```

`plays.json` and `scoring-config.json` sit next to `instance-config.json` when
`play-builder` has written them (`references/plays.md`).

## `_index/instance.md`

```markdown
# Instance: {INSTANCE_NAME}

- Company: <name>
- Field prefix: {INSTANCE_FIELD_PREFIX}
- CRM: {CRM_PROVIDER}
- Connectors: apollo on; hubspot declined (fallback: ...); airtable on; apify on; firecrawl on; brand-kit-os absent
- Brand context: files in {BRAND_CONTEXT_DIR}/ (connector absent) | Brand Kit OS kit
- instance-config.json: <absolute path on the filesystem>
- Onboarded: <date>, gtm-os <version>
- Scheduled tasks: <name: state> ...
```

The check script fails this file on any Airtable id, 24-hex id or nine-plus-digit run. A
path is fine; a resolved identifier is not. The reason: Project files are shared with every
member and pasted into prompts.

## The brand folder

Defined in `references/brand-context.md`: ten files, one per Brand Kit OS entity, each with
front matter (`entity`, `source`, `verified`, `provenance_default`) and a label on every
fact. `gtm-onboard` writes them in two passes (site scrape, then interview); the check
script verifies the shape of each before the first pass and again after the second.

## What the check does not do

It does not read content for quality, does not call any connector, does not confirm the
Project instructions by itself (the agent confirms through `project_info` and passes
`--instructions-pasted yes|no`, or `not-applicable` when no Project is attached and the
rules live in `_index/overview.md`), and does not touch `instance-config.json` beyond noting
its path. It is a shape gate, like `check_plays.py`.
