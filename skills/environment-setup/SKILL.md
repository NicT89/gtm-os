---
name: environment-setup
description: Diagnose and wire the connectors this engine runs on, from whatever state the user is already in. Use when the user says "set up my environment", "run environment-setup", "set up Apollo", "connect Airtable", "my Apify isn't working", "I haven't set up Firecrawl", "why is this skill saying no connector", "set up the Research Vault", or when any other skill stops because a connector is missing, unauthenticated, or its instance-config keys are empty. Produces a per-connector state diagnosis, the specific next action for each, the filled instance-config.json, and a proven one-target dry run.
---

# Environment Setup

Input: whatever the user already has. Output: every connector at S4 (wired and proven),
`instance-config.json` filled and validated, and a dry run that actually wrote a row.

The full per-connector procedure is the plugin root's
[references/environment-setup.md](../../references/environment-setup.md). This skill is
the decision flow over it. Read that file before acting; do not work from memory of it.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin
root VERSION file, notify on mismatch, continue.

## The rule that governs every step

**Not set up does not mean not owned.** The overwhelmingly likely case is that the user
already has the tool and has simply never shaped it for this engine: the custom fields do
not exist, the base has the wrong schema, the MCP server was never added, or the IDs were
never recorded. Probe first. Recommending a signup to someone who already pays for the
tool is the failure mode this skill exists to prevent.

## Step 1: Diagnose before asking anything

For each connector in scope, place it on the five-state ladder from the reference: S0
absent, S1 owned but unreachable, S2 reachable but unshaped, S3 shaped but unrecorded, S4
wired. Only S0 needs a signup, and S1 through S3 are the normal case.

Run the probes in the reference's order and stop at the first that answers: list the tools,
make the cheapest read-only call the connector offers, read the schema for the engine's
objects, then run `python3 scripts/validate_instance_config.py`. All four are free and
none of them spends a credit.

Ask the user only when probes 1 and 2 both fail, and ask it as a connection question, not
a purchase question: *"Do you already have a <tool> account? If so this is a connection
step, not a signup."*

## Step 2: Report the ladder before doing any work

Present one table: connector, current state, what is missing, what the next action is,
and whether that action costs money. The user decides what to fix and in what order. Do
not start creating objects in someone's CRM because a probe came back empty.

Required to run anything: Apollo, Airtable (posts base), Apify, Firecrawl. Optional and
never blocking: the Research Vault base, CB Insights, Brand Kit OS, a file home, a
warehouse. Say which of the user's gaps are actually blocking and which are not, because
a user told everything is required will stop at the first optional one.

## Step 3: Close the gaps, in dependency order

Follow the reference per connector. The order matters in three places:

1. **`INSTANCE_FIELD_PREFIX` is chosen before any Apollo custom field is created.** It
   becomes the field labels and the merge tokens; renaming later means editing every
   sequence.
2. **Airtable parent tables before child tables.** Link fields cannot be created until
   both sides exist.
3. **Objects before IDs.** A key cannot be recorded for a field that does not exist yet.

Human gates that stay gates: the human creates Apollo custom field definitions in the UI
(the API cannot), the human picks the field prefix, and the human approves anything that
spends. Everything the engine creates in Apollo carries "[Claude]" in its name, and
human-managed assets are never edited.

## Step 4: Record and validate

Write every resolved value into `instance-config.json` at the plugin root, never into a
SKILL.md. Then:

```bash
python3 scripts/validate_instance_config.py
```

It verifies shape, not existence. A clean pass means the file is well-formed, not that
the IDs are real. If a value the user needs has no key in the schema, add it to
`instance-config.example.json` in the same change per
[references/instance-config.md](../../references/instance-config.md); a `{KEY}` with no
schema entry fails CI, which is the check doing its job.

## Step 5: Prove it with one target

Setup is not done at Step 4. Run `scrape-linkedin-posts` against ONE target the user
names, and confirm the checks in the reference's "Prove it with one target" section:
bare-name parent row, bare `Name` and `YYYY-MM-DD` `Posted Date` on post rows, comment
rows linked to exactly one post row, CRM push landing in the intended field and nothing
else changed. Then run it a second time against the same target and confirm no
duplicates.

Report what was fixed, what remains at which state, and what the user must do themselves
(UI-only steps, purchases, auth in a browser). A connector left below S4 is named
explicitly along with which skills degrade because of it.

## What this skill never does

It never signs the user up for anything, never enters credentials on their behalf, never
guesses an ID or a base to get past a stop, never edits a human-managed CRM asset, and
never reports a connector as working on the strength of its tools appearing in the tool
list. S1 and S4 look identical until something is actually called.
