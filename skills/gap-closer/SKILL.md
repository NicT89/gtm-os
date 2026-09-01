---
name: gap-closer
description: Close open research questions by routing them to the people and channels likeliest to answer them. Use when the user says "run gap-closer", "close the open questions", "work the Ask list", or after an intake leaves Questions rows open in the Research Vault. Produces persona-grouped question batches, channel-appropriate drafts for human sending, agent-run support-channel sessions where wired, and answered questions written back as sourced Facts.
---

# Gap Closer

Input: open Questions rows in the Research Vault for one entity. Output: answers converted to Facts with full provenance, questions flipped to `answered`, and drafts queued for the human where a human must send.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Connector preflight

This skill reads Questions and writes Facts in the Research Vault, so it needs **three** keys resolved, not one: `{AIRTABLE_VAULT_BASE_ID}`, `{AIRTABLE_TBL_VAULT_QUESTIONS}`, and `{AIRTABLE_TBL_VAULT_FACTS}` (plus `{AIRTABLE_TBL_VAULT_ENTITIES}` to link an answer to its entity). Check all of them before starting. A base ID with empty table IDs is the dangerous middle state: it looks configured, passes a base-only check, and then fails partway through with questions already flipped to `asked`.

If any required key is empty, stop before touching anything, name the specific keys that are missing, and route the user to the `environment-setup` skill (the plugin root's `references/environment-setup.md`). Never substitute another base or table. Not set up almost never means not owned.

## The four rules (non-negotiable, set 2026-08-17)

1. **Source always documented.** Every answer records who answered, on what platform, the raw text of the answer, and the date. The Fact row carries all four; the Question links to the Fact. An undocumented answer is not an answer.
2. **Maximum 3 questions per outreach to a real person.** People answer short asks and ignore questionnaires. Support channels and chatbots are exempt from the cap; they are built for volume.
3. **Group by likeliest-to-know persona.** Pricing and cycle questions go to sales reps, roadmap to PMs, process and tooling to ops, escalation and health to CS, commissions to finance. The Persona Group field on each Question is the routing key; batch questions sharing a persona into one outreach.
4. **LinkedIn and email are draft-for-human.** The agent researches the target, writes the message with context and send instructions, and stops. The human sends from their own accounts. Agents NEVER hold credentials for a person's social or email identity. Support chats and public forum posts may be agent-operated once that channel's wiring is explicitly approved.

## Protocol

1. Pull open Questions for the entity, sorted by Persona Group then Field Key.
2. For each persona group, pick the channel: `interview` questions wait for a scheduled call (emit them as a prep list, never cold outreach); `support-chat` runs immediately if wired; `email-draft` and `linkedin-draft` produce drafts respecting the 3-question cap and the outreach-audit quality bar (specific signal, honest framing, soft CTA).
3. Identify the target person for each human-channel batch: name, role, why they are likeliest to know, and the verified contact path. If no verified path exists, the batch stays `drafted` with a note; never guess an email address.
4. On send (by the human) flip questions to `asked` with Asked At. On answer, write the Fact (Source Type `human-answer` or `support-channel`, Method `agent-interview` or `manual`, raw text in Value), link it from the Question, flip to `answered` with Answered At.
5. Questions that stay unanswered after two respectful attempts flip to `retired` with a note, not a third touch. Cadence rules from the outreach kit apply: max two touches per person per week, stop on any reply, never work more than two people at one company in the same week.

## What this skill never does

It never sends anything itself on human channels, never fabricates an answer to close a question, never exceeds the question cap to "be efficient", and never contacts anyone on a do-not-contact list. When in doubt about whether a channel is wired for agent operation, it is not.
