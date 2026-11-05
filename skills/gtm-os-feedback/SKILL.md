---
name: gtm-os-feedback
description: Report a bug, request a feature, or send feedback on a GTM OS skill to the maintainers as a redacted GitHub issue the user approves before it is filed. Use when the user says "report this bug", "send feedback", "file an issue", "request a feature", "this skill did the wrong thing", "tell the maintainer", "GTM OS should be able to", "log this for the plugin", or when any skill produces a result the user says is wrong and they want it fixed upstream rather than worked around. Routes security reports to the private channel first; otherwise collects the kind, the skill, the version and the surface, strips instance IDs, email addresses, credentials and private links (names are removed by the reporter, not detected), shows the exact body, waits for the user's yes, and files it only through a command the user approves. Works without gh or a shell by handing over the body and the matching issue form.
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

## Step 0: Is this a security report?

Before anything else. A credential or an instance value found in this repo, a skill or
script that can write outside the records it was asked to touch or past one of the human
gates, a redaction gap, or prompt injection a skill obeyed: these never become a public
issue. Point the user at the private route in `SECURITY.md` (the email address and what to
include are there), do not render, do not file, and stop. Everything below is for the
other kind of report.

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
what happened, never your summary of their workspace. **The redactor recognizes shapes,
not meaning.** It strips Airtable IDs, 24-character hex CRM field IDs, email addresses,
long digit runs, credential patterns, and links to anything other than vendor documentation
or this repo (a link to any other GitHub repository is stripped). It does not detect names,
and it does not know every vendor's ID format. Before rendering, ask the user to replace any
prospect, customer or person name with a role or a placeholder ("a Tier 1 account", "the VP
we targeted") and to do the same for any identifier from a system the list above does not
name. The preview is the second check, not the only one. If the defect surfaced in this
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
naturally beyond the name rule above; do not pre-sanitize them and do not talk the user into
rephrasing.

**Show the rendered title and body to the user in full, then stop and wait for their
reply.** If they object to anything in it, change the report and render again. Never file a
body they have not seen in final form, and never file one they have not answered yes to. A marker
where a real finding used to be (an Airtable ID that was the point of the bug) is fine:
say "the posts table" instead of the ID and render again.

## Step 3: File it, or hand it over

With `gh` available:

```bash
python3 <plugin root>/scripts/feedback.py --report feedback.json --submit --confirm <token>
```

**Two gates, and neither substitutes for the other.** First, the user's explicit yes in a
reply after the body was shown: without it the submit command is never issued, whatever
the host's permission setting. Second, the host's own approval prompt on the command: say
what filing does (a public issue on `NicT89/gtm-os`, under their GitHub account) and let
the tool call carry it; a yes in conversation does not license running the command as if
it were pre-approved. The token is a digest of the title and body that were displayed: an
edit after rendering changes it and the submission is refused, so nothing can be filed
that was not first put on screen.

Without `gh`, or without a shell: give the user the rendered body and the `paste_url` from
the render step. The URL opens the matching issue form with the title filled in; they paste
the body. In a chat session with no shell at all, write the body yourself in exactly the
rendered shape (the form's fields are the same sections) and apply the redaction rules by
hand, naming each thing you left out.

Report the issue URL back, and if the same defect blocked a run, say what the user can do
in the meantime (the stop message usually says).

## Rules that do not bend

- **A no ends it.** Do not re-ask, do not ask a second way, and do not treat silence as
  consent. No reply is a no.
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
