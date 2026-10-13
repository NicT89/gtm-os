# Outcomes and the learning loop

An outcome is something a prospect did after outreach: replied, booked a meeting, bounced.
The learning loop reads outcomes and proposes changes to scoring and plays. This file is the
contract both sides follow. `scripts/check_outcomes.py` checks it.

## Where outcomes live: the CRM first

**An outcome is written to your CRM wherever the CRM will take the write.** That is your
system of record, and its activity timeline (notes, emails, meetings, tasks) keeps the full
history with dates, which a single custom field cannot.

| CRM | How outcomes get there |
|---|---|
| Apollo | Sequence replies and bounces are recorded by Apollo itself; the engine reads them rather than writing them. Anything Apollo does not record (a meeting booked outside a sequence, a deal outcome) is written as an engine note where the connector allows it |
| HubSpot | Written as a note associated with the contact and company, through the pre-sync check in `references/hubspot-adapter.md` |

Only when the CRM cannot take a write does the record go to the fallback named by
`{OUTCOME_FALLBACK}`: `airtable` or `sqlite`, in your own storage. Empty means CRM only.
Launch99 does not hold your outcome records; GTM MCP receives only what you send it for
analysis.

## The outcome record

| Field | Rule |
|---|---|
| `event` | One of `reply`, `positive_reply`, `meeting_booked`, `bounce`, `unsubscribe`, `opportunity_created`, `closed_won`, `closed_lost` |
| `occurred_on` | YYYY-MM-DD |
| `crm` | `apollo` or `hubspot` |
| `contact_id`, `account_id` | At least one |
| `play` | The play the contact was enrolled under. Required: an outcome with no play credits nothing |
| `enrolled_on` | YYYY-MM-DD, the date of the snapshot below. Not after `occurred_on` |
| `account_score`, `persona_score` | Numbers as they were at enrollment, or null |
| `variant` | The message variant sent, or null |
| `unknown` | Every snapshot field that is null. **A silent null reads as zero** to anything that averages it |
| `source` | `crm_native`, `engine_note`, `fallback_airtable` or `fallback_sqlite` |
| `run_mode` | `LIVE`, `FIXTURE`, `SIMULATED` or `PREVIEW`, as defined in `references/run-manifest.md` |

### Credit goes to the snapshot, not today's values

Plays are re-assigned every run and scores change. If a reply were credited to the
contact's current play, a play re-assigned last week would take credit for the old one's
reply. So every record carries the play and scores **as they were at enrollment**, and the
loop credits those.

### The note format

When an outcome is written as a CRM note, it takes this fixed block, so it can be read back
exactly:

```
[GTM OS outcome v1]
event: meeting_booked
occurred_on: 2026-09-24
play: first-gtm-hire
enrolled_on: 2026-09-10
account_score: 64
persona_score: unknown
variant: A
run_mode: LIVE
```

The contact, company and CRM come from the note's own associations. `check_outcomes.py`'s
`render_note` and `parse_note` are this format, and they round-trip.

## The learning loop

1. **Gather** the outcome records for a period from the CRM (and the fallback, if used).
2. **Check** them: `python3 scripts/check_outcomes.py records.json`.
3. **Analyze** them in GTM MCP (`references/gtm-mcp.md`). The analysis returns proposals.
4. **Check the proposals**: `python3 scripts/check_outcomes.py --proposals proposals.json
   --scoring <your scoring config>`.
5. **A human decides** on each one. Approved changes are made to the scoring config or plays
   file by hand or through `play-builder`, and recorded in the changelog with the evidence.

### Proposals

Each proposal names its `target` (a scoring-config path or a play id), the `change`, a
`hypothesis`, the `sample_size`, the `evidence` counts it rests on, and a `status`:
`proposed` or `insufficient_data`.

- **The minimum sample is yours to set,** as `learning.min_sample` in your scoring config. No
  default ships: how few outcomes is too few depends on your volume, and a number chosen for
  you would be invented. Without it, proposals fail the check.
- **Below the minimum, a proposal must say `insufficient_data`.** It still reports what it
  saw; it just does not recommend acting on it.
- **There is no `applied` status.** Applying a change is a human decision, made outside the
  loop, and the checker rejects any other status.
