---
name: gtm-os-feedback
description: Report a bug, request a feature, or send feedback on a GTM OS skill to the maintainers as a redacted GitHub issue the user approves before it is filed. Use when the user says "report this bug", "send feedback", "file an issue", "request a feature", "this skill did the wrong thing", "tell the maintainer", "GTM OS should be able to", "log this for the plugin", or when any skill produces a result the user says is wrong and they want it fixed upstream rather than worked around. Collects the kind, the skill, the version and the surface, strips instance IDs, names, credentials and private links, shows the exact body, and files it only through a command the user approves. Works without gh or a shell by handing over the body and the matching issue form.
---

# GTM OS feedback

The loop that improves the engine. A company running its own copy sees defects the
maintainer never will; this skill turns the moment they notice one into an issue upstream,
without anything from their instance travelling with it.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION and compare it to the
VERSION file at the plugin root. Say an updated version is available only when the remote
version is newer, then continue. The installed version goes in the report; a defect already
fixed upstream is still worth filing, with that noted, because it says the update did not
reach them.

## What it needs

Python 3 and the plugin root (two directories above this skill's base directory). `gh`
authenticated to GitHub lets it file the issue from here; without `gh`, or in a chat
session with no shell, it ends with a body to paste and a link to the right form. Both are
fine outcomes. Never look for another way to send it.

## Step 1: Classify, in the user's words

Three kinds, and the kind decides the sections:

| Kind | When | Sections |
|---|---|---|
| `bug` | A skill, script, gate or reference did the wrong thing | what you ran, what happened, what you expected |
| `feature` | Something the engine should do and does not | what you want, what it would let you do, how you handle it today |
| `skill-feedback` | A skill ran to completion and the result could be better | what worked, where it fell short, what you would change |

Then the target: the skill directory name, or `plugin`, `setup`, `docs`, `scripts`,
`connectors`, `other`. The script rejects anything else, on purpose: a free-typed name is
where a client or workspace identifier would otherwise ride along.

**Ask for each section and write only what the user says.** The report is their account of
what happened, never your summary of their workspace. If the defect surfaced in this
conversation, offer the relevant lines back to them to confirm, rather than filing your
narration of it. If a connector state is known from an `environment-setup` run, include it;
do not probe connectors to find out.

## Step 2: Render, and show the exact body

Write the report as JSON (`python3 <plugin root>/scripts/feedback.py --schema` prints the
shape) to a file in the user's working directory, then:

```bash
python3 <plugin root>/scripts/feedback.py --report feedback.json
```

This prints the title, the body after redaction, a confirmation token, and the paste URL.
It sends nothing. Workspace IDs, CRM field IDs, email addresses, credentials and links
outside vendor documentation are each replaced in place with a visible
`[redacted: <kind>]` marker, and the body says how many were removed. Write the sections
naturally; do not pre-sanitize them and do not talk the user into rephrasing.

**Show the rendered body to the user in full.** If they object to anything in it, change
the report and render again. Never file a body they have not seen in final form. A marker
where a real finding used to be (an Airtable ID that was the point of the bug) is fine:
say "the posts table" instead of the ID and render again.

## Step 3: File it, or hand it over

With `gh` available:

```bash
python3 <plugin root>/scripts/feedback.py --report feedback.json --submit --confirm <token>
```

**The host's approval prompt on that command is the acceptance gate.** Do not ask for
permission in prose and then run the submit command as if that settled it. Say what filing
it does (a public issue on `NicT89/gtm-os`, under their GitHub account), and let the tool
call carry the decision. The token is a digest of the body that was displayed: an edit
after rendering changes it and the submission is refused, so nothing can be filed that was
not first put on screen, including under a permission setting that would otherwise run
this script unattended.

Without `gh`, or without a shell: give the user the rendered body and the `paste_url` from
the render step. The URL opens the matching issue form with the title filled in; they paste
the body. In a chat session with no shell at all, write the body yourself in exactly the
rendered shape (the form's fields are the same sections) and apply the redaction rules by
hand, naming each thing you left out.

Report the issue URL back, and if the same defect blocked a run, say what the user can do
in the meantime (the stop message usually says).

## Rules that do not bend

- **A no ends it.** Do not re-ask, do not ask a second way, and do not treat silence as
  consent.
- **Nothing from the instance.** No resolved IDs, prospect or customer names, credentials,
  run artifacts, or links into their workspace, even when they would make the bug clearer.
  The maintainer can ask for a redacted reproduction in the thread.
- **Never file on their behalf from memory.** If the user leaves before approving, the
  report stays in their working directory, unsent.
- **One issue per defect.** Two things wrong are two reports.

## What this skill never does

It never edits the plugin to work around the defect (that is a fork change, per
`FORKING.md`), never opens a pull request, never files to any repository other than
upstream, and never includes a connector state it did not get from an actual
`environment-setup` run.
