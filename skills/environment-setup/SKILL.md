---
name: environment-setup
description: Diagnose and wire the connectors this engine runs on, from whatever state the user is already in. Use when the user says "set up my environment", "run environment-setup", "set up Apollo", "connect Airtable", "my Apify isn't working", "I haven't set up Firecrawl", "why is this skill saying no connector", "set up the Research Vault", or when any other skill stops because a connector is missing, unauthenticated, or its instance-config keys are empty. Produces a per-connector state diagnosis, the specific next action for each, the filled instance-config.json, a proven one-target dry run, and — only with the user's explicit approval — a redacted setup report filed upstream.
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
objects, then run `python3 scripts/validate_instance_config.py`.

**All of those are free EXCEPT the Firecrawl probe, which performs a scrape and spends a
credit.** State that one credit before running it, per the plugin root's
[references/environment-setup.md](../../references/environment-setup.md), which is the
authoritative per-connector procedure. Describing the whole diagnosis as free was wrong
until 1.9.2 and had this skill spend unannounced, which is the credit gate failing in the
one place a new user meets it first.

Ask the user only when probes 1 and 2 both fail, and ask it as a connection question, not
a purchase question: *"Do you already have a <tool> account? If so this is a connection
step, not a signup."*

Then run the config side of the same diagnosis, which is deterministic and needs no
connector at all:

```bash
python3 scripts/setup_status.py
```

It reports every config key as **set**, **default**, or **unset**, grouped by
connector, with what each gap blocks. The `default` state is the one to read closely:
those keys are non-empty, they work, and they arrived by copying the example rather
than by anyone deciding. `READY_WITH_DEFAULTS` is not done.

## Step 2: Report the ladder before doing any work

Present one table: connector, current state, what is missing, what the next action is,
and whether that action costs money. The user decides what to fix and in what order. Do
not start creating objects in someone's CRM because a probe came back empty.

Required to run anything: Apollo, Airtable (posts base), Apify, Firecrawl. Optional and
never blocking: the Research Vault base, CB Insights, Brand Kit OS, a file home, a
warehouse. Say which of the user's gaps are actually blocking and which are not, because
a user told everything is required will stop at the first optional one.

**Say which support tier their platforms are on, once, here.** The user picks their own
stack, and the plugin root's [references/platform-support.md](../../references/platform-support.md)
is the honest answer about each one: Native means the skills are written against that
platform's real semantics and a deployment has run it end to end; Generic means the motion
runs with the same gates and audits but nobody built the platform-specific path, so field
mapping is theirs and its failure modes are undocumented; Not built means there is no path
here at all, whatever the vendor's own MCP server can do. State the tier and the specific
thing they lose, then continue. Do not talk anyone out of their stack, do not imply a
Generic platform is unsupported, and never imply it is equivalent to Native — that last one
sets an expectation of deterministic behavior that was never built.

## Step 3: Close the gaps, in dependency order

Follow the reference per connector. The order matters in three places:

1. **`INSTANCE_FIELD_PREFIX` is chosen before any Apollo custom field is created.** It
   becomes the field labels and the merge tokens; renaming later means editing every
   sequence.
2. **Airtable parent tables before child tables.** Link fields cannot be created until
   both sides exist.
3. **Objects before IDs.** A key cannot be recorded for a field that does not exist yet.

**Replace the shipped defaults, do not inherit them.** For every key
`setup_status.py` reports as `default`, ask the user one question and record their
answer, even when the answer is "the default is right." `CRM_PROVIDER` is the one
that matters most: it ships as `apollo` and the field-writing calls are named for
Apollo, so a user on a different CRM has a fork to plan, not a label to edit. Re-run
the report after each pass; the target is `READY`, not `READY_WITH_DEFAULTS`.

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

## Feedback checkpoints (offer at each; the approval is the tool call)

This module has been read far more than it has been watched. The failure it exists to
prevent — telling somebody to buy a tool they already pay for — can only be observed on
someone else's half-configured accounts, so the run reports itself instead of leaving the
write-up as homework nobody does.

Offer to file a report at exactly three moments:

1. **After Step 2**, once the ladder is on screen and before anything has been changed.
   This is the highest-value one: it captures the diagnosis, which is the part under test.
2. **After Step 5**, when a write has been proven.
3. **Whenever the run stops early** — a blocked purchase, a UI-only step the user will not
   do now, a probe that could not be resolved. An abandoned run is a finding, not a
   non-event, and it is the one that never gets reported voluntarily.

It is a two-step flow, and the second step is where the user approves:

```bash
python3 scripts/setup_feedback.py --report <report.json>
python3 scripts/setup_feedback.py --report <report.json> --submit --confirm <token>
```

The first renders the exact issue body and prints a token derived from it, and sends
nothing. The second files it, and the host's own approval prompt for that command is the
acceptance gate — you are not collecting consent in conversation and then reporting the
answer yourself. **Do not ask for permission in prose and then run the submit command as
if that settled it.** Show the rendered body, say what filing it does, and let the tool
call carry the decision.

The token is a digest of the body that was displayed. If a note is edited or the ladder
changes after rendering, the token no longer matches and the submission is refused, so
nothing can be filed that was not first put on screen — including under a permission
setting that would otherwise run this script unattended.

`--schema` prints the input shape. The report carries connector names, S0-S4 states, the
checkpoint, the outcome, whether a state was misdiagnosed, and short free-text notes.
**Sensitive values in notes are stripped automatically** — credentials, workspace IDs,
email addresses, and links outside vendor documentation are each replaced with a visible
`[redacted: <kind>]` marker, and the body says how many were removed. Write the note
naturally; do not pre-sanitize it and do not talk the user into rephrasing.

**Rules that do not bend:**

- **A no ends it.** Do not re-ask at the next checkpoint, do not ask a second way, and do
  not treat silence as consent. Continue the setup exactly as if the offer had not been
  made.
- **Never put anything in a note the user has not said.** The notes are their account of
  what happened, not your summary of their workspace. Redaction protects against values
  leaking; it does not license writing observations on their behalf.
- **The rendered body is the last word.** If the user objects to anything in it, change the
  report and render again. Never file a body they have not seen in final form.

If `gh` is missing or unauthenticated, the script says so and prints the body for the user
to paste. That is a fine outcome; do not go looking for another way to send it.

## What this skill never does

It never signs the user up for anything, never enters credentials on their behalf, never
guesses an ID or a base to get past a stop, never edits a human-managed CRM asset, and
never reports a connector as working on the strength of its tools appearing in the tool
list. S1 and S4 look identical until something is actually called.
