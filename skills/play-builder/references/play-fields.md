# Play fields: what goes in each, and what good looks like

The guidance `play-builder` writes plays against, field by field. Free-text fields are free
because plays differ completely between organizations; this file is what keeps free text from
becoming vague text. For each one it says what the field is for, the bar it has to clear, a
weak and a strong example, and a test. The examples are illustrative, not a menu: an
organization writes its plays in its own terms.

`check_plays.py` checks the structural fields below deterministically. It never judges the
free-text ones; that is the model's job against this file, and the operator's at review.

## Structural fields (checked by code)

| Field | Rule |
|---|---|
| `id` | Lowercase slug, unique. Never changes once records carry it. |
| `code` | Short, unique, and the prefix of every Apollo object the play owns: `(P1) [Claude] ...`. Pick codes the team will read on lists for years. |
| `label` | The name people say out loud. |
| `priority` | A number. Higher wins when more than one play's criteria fit. An override (a play that should beat another whenever both fit) gets the higher number; say so in its criteria too. |
| `signal_types` | The sourcing signals that can feed this play. Orientation for the scan, not a gate. |
| `exclusive_with` | Ids of plays that must never run against the same company at the same time. |
| `apollo.account_list`, `apollo.contact_list`, `apollo.sequence` | Names, each starting `(CODE)`. Objects this skill creates also carry `[Claude]`; a name without it marks a human-managed asset the play routes to but never edits (a warning, not a failure). Empty until built; the demo's preview mode reports empty ones. |
| `fields.standard` | Keys from instance-config.example.json (see `standard-fields.md`). |
| `fields.custom` | `label`, `object` (account or contact), `type`, `purpose` for each field only this play needs. |

## `entry_criteria` (free text, judged by the model)

**For:** deciding whether an account belongs in this play. The scan judges it against evidence
from free calls, so write it in terms of things that can be observed.

**Good looks like:** one to three sentences describing a situation at the company, in the
organization's own language, naming what would be seen if it were true. If it outranks another
play, it says so and says why.

- Weak: `hiring` (a keyword, not a situation: every company hiring anyone qualifies).
- Weak: `Companies that need our help with go-to-market.` (unobservable: no evidence decides it).
- Strong: `Nobody works in a dedicated go-to-market role yet, and the company has an open posting
  for its first GTM leader.` (two observable facts, both checkable by a free people search and
  the posting).

**Test:** hand the criteria and one real account's evidence to someone who has never seen the
play. They should reach the same yes or no you would, without asking what you meant.

## `evidence_to_check` (free text)

**For:** telling the scan which free calls and which parts of the result decide the criteria.

**Good looks like:** names the source and what to read in it. Includes the trap if there is one
(people search by title misses `Founding <role>` staff; by seniority it over-reports them).

- Weak: `Check Apollo.`
- Strong: `People search by organization id for GTM titles, read by title AND by seniority; the
  posting text for whether the role is the first of its kind.`

## `exit_criteria` (free text)

**For:** knowing when an account no longer belongs here, so re-assignment on the next run has
something to test against.

**Good looks like:** the observable change that ends the situation, and where it usually goes
next if that is predictable. `The posting closes or someone joins in a GTM role.`

## `persona` (free text)

**For:** who in the account the play writes to. Composition anchors on persona, not on the
signal (`outreach-audit`), so this decides which facts the opener can use.

**Good looks like:** the role and why it is theirs. `The founder or CEO running the search,
because the hire is their decision and the pipeline is theirs until it lands.` Not a title list
alone: people search already produces titles.

## `angle` (free text)

**For:** the conversation the play opens, in one sentence. It is not copy and it is not the
closer (the closer comes from the target's GTM motion).

- Weak: `We can help them grow.`
- Strong: `They are about to hand pipeline to one person; the question is what that person
  inherits.`

## `scheduled_tasks` (free text list)

**For:** recurring human or agent work the play needs outside the sequence, such as re-checking
whether a posting closed. Each item says the cadence and the action.

## `workflows` (structured, built in the Apollo UI)

**For:** the Apollo-side automation the play relies on. Apollo workflows cannot be created
through the connector, so each entry is a checklist item for the UI: `trigger_list` (the list
whose membership fires it), `fills` (the field keys it writes), `schedule`. Setup is verified by
reading those output fields on a record afterward, the way `field_gate.py` verifies outputs.
