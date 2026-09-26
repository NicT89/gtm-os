---
name: gtm-os-demo
description: Run the GTM OS offline demo, with no connectors and no credits spent. Use when the user says "run the demo", "run gtm-os-demo", "show me how it works", "try GTM OS", "what would a scan do", "test my setup", "check my instance before a live run", or has just installed the plugin and has nothing connected yet. Runs the engine's real decision logic (dedupe, exclusions, play assignment as a labeled stand-in for the model's judgment, two-pass scoring, reachability ranking, the credit statement, the field gate, composition checks) over synthetic accounts and writes a labeled report. With the user's instance-config.json it runs the same accounts through their own config and reports every setup gap as a finding.
---

# GTM OS offline demo

The first thing to run: before connecting anything, to see the engine think, and again
after setup, to check the instance before the first live scan spends a credit.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION and compare it to the
VERSION file at the plugin root. If they differ, say an updated version is available, then
continue.

## What it needs

Python 3 and nothing else. No connector, no key, no network beyond the version check. The
plugin root is two directories above this skill's base directory; every path below is
relative to it.

## Step 1: Choose the mode

- **Synthetic** (default): the user has nothing set up, or wants to see how it works.
- **Preview**: the user has an `instance-config.json` in their working directory, or asks
  to test their setup. Use their file; never create one for them here. If they have none,
  run the synthetic mode and point them at the `environment-setup` skill.

## Step 2: Run it

```bash
python3 <plugin root>/scripts/demo.py --out gtm-os-demo                       # synthetic
python3 <plugin root>/scripts/demo.py --config instance-config.json --out gtm-os-demo  # preview
```

It writes `gtm-os-demo/report.md` and `gtm-os-demo/run-shape.json` in the user's working
directory. Exit 1 in preview mode means blocking findings, not a crash; exit 2 means it
could not run, and its message says why.

## Step 3: Walk the user through the report

Lead with the headline counts, then the holds, because the holds are the engine's
judgment: each one has a reason, and the reasons are what a live run protects them from
(a duplicate record, a credit spent on an unreachable contact, an opener carrying a number
nobody can source). In preview mode, lead with the findings table instead, blocking first,
and route each fix to where it is made: instance keys to `environment-setup`, the plays file to
`play-builder`, the scoring config to `provision-gtm-engine`, the catch-all policy to the operator as a named human
gate.

## The rules for talking about it

- **Say the label.** Every row is SIMULATED, FIXTURE or PREVIEW, per the plugin root's
  `references/run-manifest.md`. Never describe a demo result as a result about a real
  company, and never present a FIXTURE opener as something the engine wrote.
- **The scoring numbers are illustrative** unless the report says it used the user's own
  scoring config. Do not recommend the demo's thresholds as settings.
- **Nothing was spent or sent**, and the report's credit statement is what a live run
  would ask approval for, not a quote.
