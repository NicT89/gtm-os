---
name: event-attribution
description: Reconcile event attendee lists against the CRM and tag every matched record with event-source attribution. Use when the user says "run event-attribution", "reconcile this attendee list", "attribute the [event name] leads", or shares a Luma export, badge-scan CSV, or registration list after a field event. Produces matched/created CRM records with event tags, the unmatched remainder for human review, and the attribution summary that closes the loop on event spend.
---

# Event Attribution

Input: an attendee list (Luma export, badge scans, registration CSV) plus the event's name, date, and city. Output: every attendee either matched to a CRM record or created as one, tagged with the event source, plus a summary that makes the event's pipeline contribution queryable forever.

Field events are the highest-spend, worst-attributed channel in most GTM motions. The failure mode is mechanical: the list lives in a CSV, the CRM never hears about it, and six months later nobody can say whether the event sourced pipeline. This skill exists to make that failure impossible.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Connector preflight

This skill needs the CRM (`{CRM_PROVIDER}`) to match and create records, and the Research Vault to log the run. The Run row needs `{AIRTABLE_VAULT_BASE_ID}`, `{AIRTABLE_TBL_VAULT_RUNS}`, and `{AIRTABLE_TBL_VAULT_ENTITIES}`; if any is empty, produce the matched/created records and the summary, skip the Run row, and say plainly that the event was not logged to the Vault. Do not write a partial Run row. Without the CRM, stop: there is nothing to attribute against. Route the user to the `environment-setup` skill (the plugin root's `references/environment-setup.md`); not set up almost never means not owned.

## Protocol

1. **Normalize the list.** Parse to name, email, company, title. Flag rows missing email (badge scans often drop it); they match on name + company with lower confidence.
2. **Match against the CRM, email first.** Exact email match wins. No email match: name + company domain, marked lower confidence. Ambiguous matches (two people, same name) go to the human review pile, never auto-merged.
3. **Existing records**: append the event touch (event name, date, city, source list) to the record's activity or the designated event field. NEVER overwrite existing source attribution; an account sourced by outbound that later attends an event keeps both touches. Attribution is additive.
4. **Net-new records**: create with the event as original source, tagged per the house naming convention: everything the engine *creates* carries "[Claude]" in its name. The no-edit rule applies to human-managed **fields and names**, not to the record as a whole: appending an event touch to the activity log or the designated event field (step 3) is exactly what this skill is for, and is not an edit of a human-managed field. Never overwrite a human's source attribution, owner, stage, or naming. State the count and any credit cost BEFORE creating; bulk creation is a gated spend.
5. **Unmatched remainder**: rows that matched nothing and lack enough data to create cleanly go to a human-review list with the reason per row. Report the match rate; below roughly 60 percent usually means the export is malformed, so stop and say so rather than churning out junk records.
6. **Write the summary**: a Run row in the Research Vault (event as Target) and a summary the human can forward: attendees, matched, created, review pile, and the follow-up segments (customers attended, open opportunities attended, net-new). The segments are the sales team's next-day call list; deliver them the same day.

## Attribution queries this enables

Once tagged, the warehouse or CRM can answer: pipeline sourced by event X, influenced-by-event revenue (opportunities whose contacts attended any event), cost per matched attendee, and event-to-opportunity conversion by city. Those four queries justify or kill next quarter's event budget; name them in the summary so the team knows to ask.
