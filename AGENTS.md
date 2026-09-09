# AGENTS.md

GTM OS is an AI-native go-to-market engine, packaged as an installable Claude Code
plugin. It sources companies through buying signals, enriches them in tiers, prepares
research-grounded personalization, and audits every outreach asset before anything sends.
You point it at your own accounts; it ships with nobody else's.

This file exists so that an agent landing here first — rather than on `README.md` or
`CLAUDE.md` — can start correctly without being routed somewhere else. The four steps
below are repeated verbatim in all three files on purpose.

<!-- BEGIN GET STARTED -->
## Get started

GTM OS is a **Claude Code plugin**, not a prompt and not a hosted service. Opening this
repo's URL in a chat window installs nothing and runs nothing — the skills only exist
once the plugin is installed.

**1. Install it.** In Claude Code:

```
/plugin marketplace add NicT89/gtm-os
/plugin install gtm-os@gtm-os
```

**2. Set it up.** In a working directory of your own — not a clone of this repo — say:

```
set up my environment
```

The `environment-setup` skill drives it, and it diagnoses what you already have before it
suggests anything, because **not set up almost never means not owned**. The usual
situation is that you own the tool and have simply never shaped it for this engine.
Diagnosis costs almost nothing: every probe is a read-only call except the Firecrawl one,
which performs a scrape, spends a single credit, and states that before it runs.

**3. Know how well it speaks your stack.** Bring the CRM and data tools you already use.
`references/platform-support.md` puts each one in a tier: **native** (built against that
platform's own semantics), **generic** (the motion runs under the same gates, but you map
the fields and its failure modes are undocumented), or **not built** (no path here yet,
whatever the vendor's own server can do). Generic is a real option, not a warning label.
Not built is genuinely not supported. The engine tells you which tier you are on rather
than letting you infer it.

**4. Run something.** Ask in your own words — `run a signal scan`,
`create a GTM blueprint for <company>`, `audit my sequence`. Every skill states what it
needs and stops when a connector is missing rather than guessing around it.

Full walkthrough: `SETUP.md`. Nothing from your instance — IDs, prospects, reports, logs —
ever comes back to this repo.
<!-- END GET STARTED -->

## If you are changing this repo rather than using it

Read [CLAUDE.md](CLAUDE.md). It carries the conventions that are load-bearing for every
installed copy: instance tokenization, the human gates that never automate away, the
version and changelog rules, and the pull-request loop. [MAINTAINING.md](MAINTAINING.md)
covers the release process.

Two things to know before editing:

- **Every deployment value is a `{KEY}` token** resolved from a git-ignored
  `instance-config.json`. A resolved ID committed to this repo is a defect, and this is a
  public repository.
- **The three copies of the block above are pinned by a test.** Edit
  `references/get-started.md` and re-sync, or `tests/test_get_started_consistent.py`
  fails. Do not hand-edit one copy.

## How well this engine speaks your stack

You choose your platforms. `references/platform-support.md` states which are built in
natively, which run generically, and which are not built yet — and what specifically you
give up in each case. A platform outside the native tier still runs the motion; say which
tier the user is on rather than implying the tiers are equivalent.
