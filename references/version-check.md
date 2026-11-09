# Version check

Every skill runs this first and never blocks on it. This file is the only place the
procedure is written; a SKILL.md cites it and does not restate it, so a change to the chain
reaches every skill at once.

## Why a chain

A deployment that cannot reach `raw.githubusercontent.com` (observed 2026-11-05 on a
customer account whose network allowlist did not include it) used to get "could not fetch"
and no signal at all that an update existed. The installed plugin knows its own version and
nothing else; the fetch is the only way a user learns that the connector they are missing
shipped last week.

## The procedure

1. Read the installed version: the `VERSION` file at the plugin root.
2. Fetch the current version, trying each source in order and stopping at the first that
   returns a version string. Give each fetch a short deadline (about ten seconds where the
   fetch tool accepts one; otherwise do not wait on a stalled connection) and count a
   timeout as that source failing, so a blocked host costs seconds, not the minutes a
   host's default fetch timeout can hold a skill for:
   1. `https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION` (plain text)
   2. `https://api.github.com/repos/NicT89/gtm-os/contents/VERSION` (JSON; the `content`
      field is base64)
   3. `https://github.com/NicT89/gtm-os/releases/latest` (the final URL's tag, `vX.Y.Z`)
3. Compare as three integers (major, minor, patch), not as strings.
4. Say one line, then continue with the skill:

| Outcome | Say |
|---|---|
| Installed equals current | Nothing, or "GTM OS X.Y.Z, current." |
| Current is newer | "GTM OS X.Y.Z installed; A.B.C is available. Update the plugin when convenient; continuing on X.Y.Z." |
| Every source failed | "Version check unverified: could not reach [hosts tried]. Continuing on X.Y.Z." |

Only the installed version is ever older in a way that matters; an installed version newer
than `main` means a development clone and is reported as current.

## What it never does

It never blocks, never retries beyond the three sources, never asks the user to fix their
network, and never claims a version it did not read. "Unverified" is a complete and
acceptable outcome; the skill carries on with what is installed. A failed version fetch
is not a tool failure in the sense a skill's own stop rules mean (`gtm-blueprint` stops
when a CRM call fails, for instance): those rules govern the skill's work, and this check
is finished, with outcome "unverified", before that work starts.

## Where the outcome is recorded

Skills that produce a report or file an issue record the installed version and the check's
outcome, so a reader knows whether the run was on current code. The two issue schemas carry
it as `version_check` (`current`, `update-available` or `unverified`; `scripts/feedback.py
--schema` and `scripts/setup_feedback.py --schema`), and a report that omits it renders
"not recorded" rather than a guess. A run report under `runs/` names both in its header.
