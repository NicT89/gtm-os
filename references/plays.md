# Plays: how an account is routed, and why that part is not a list of options

A **play** is one outbound route: who it targets, the situation that qualifies an account
for it, and the Apollo objects it owns (account list, contact list, sequence, fields,
scheduled tasks, workflows). Every sourced account gets exactly one play, or is held.

It is the third of three terms, and none of them may be used for another
(`references/signals-doctrine.md` defines the other two):

| Term | What it is | Decides |
|---|---|---|
| **Signal type** | What pulled the account into a run: `hiring` or `funding` | Search filters, which account fields the opener's hard number can come from |
| **GTM motion** | The target company's own go-to-market shape (PLG, enterprise, and so on) | The blueprint's plan and its closer |
| **Play** | Our route to the account, defined by the deployment | List, sequence, persona, `play_fit` points |

Until 1.11.0 the engine called plays "motions" and shipped one operator's five of them
(M1-M5) as if they were the engine's. Both were defects: the word collided with GTM motion,
and one company's routing was presented as everyone's.

## Where plays live

In the deployment's own plays file, named by `{PLAYS_FILE}` in instance-config.json and
written by the `play-builder` skill. The repo ships only `examples/demo/plays.demo.json`,
whose plays are labeled illustrative. The field-by-field guidance for writing a play is the
`play-builder` skill's `references/play-fields.md`, and it is not restated here.

## Deterministic where it is universal, guided where it is yours

Plays are the clearest case of the repo-wide rule in CLAUDE.md. What differs between
organizations is free text, written against guidance and judged by the model; what is the
same everywhere is checked by code:

- **Guided, judged by the model:** entry criteria, exit criteria, persona, angle, the
  evidence to check. A plays file whose criteria are enumerated options would force every
  company onto one company's axes.
- **Deterministic, checked by `skills/play-builder/scripts/check_plays.py`:** the file's
  shape, unique codes, a numeric priority, criteria written as a sentence rather than a
  keyword, known standard fields, and the Apollo naming rule below.
- **Deterministic, in `score.py`:** `play_fit` points for the assigned play, and a hold for
  an account with none. `score.py` never assigns a play.

## Assigning a play (gtm-signal-scan Step 1.5)

1. **Gather evidence before judging, and gather it free.** A people search by
   `organization_ids` costs nothing; the search filters already say which signal sourced
   the account. Not found is not absent: vary the query before concluding a role does not
   exist.
2. **Judge every play's entry criteria against that evidence**, not just the first that
   looks close. Where more than one fits, the higher `priority` wins; that is how an
   override (a recency play that outranks a quadrant) works without any special case.
3. **If the evidence cannot decide, hold the account** and name the free call that would
   decide it. A guessed play spends enrichment credits on a route nobody chose.
4. **Record the decision on the record**, in the standard Play fields
   (`{APOLLO_CF_ACCOUNT_PLAY}` and `{APOLLO_CF_ACCOUNT_PLAY_ASSIGNED_ON}`, and the contact
   equivalents): the code, one line of reasoning, the evidence, and the date. A play that
   lives only in a run's reasoning is a play nobody can audit later.
5. **Re-assign every run; never trust the stored value.** Reqs get filled and leaders land,
   so a play is a property of current state. When it changes, record the change with its
   date and reason rather than overwriting silently, as `references/gap-ledger.md` requires
   of every machine-written field.

**An account has one scoring play; its contacts may route to different plays.** The
account's play is the highest-priority play whose criteria it meets. It is the play
`score.py` reads (`account["play"]`) for `play_fit`, and the one recorded in the account
Play fields. Contacts are routed separately, by persona: a founder and a GTM lead at the same
account may belong to two different plays, and each contact belongs to exactly one, recorded
in the contact Play fields. A play may declare `exclusive_with`: plays whose relationship
with the recipient is different in kind (a recruiting track and a sales track at the same
company, for example) must never run against the same company at once.

## Naming: every Apollo object a play touches carries its code

- **Lists and sequences** start with the play's code in parentheses: `(P1) [Claude] First GTM
  Hire`. Objects Claude creates also carry `[Claude]`; a play may route to a list a human built
  without it, and that list is then human-managed: routed to, never edited. `check_plays.py`
  fails a missing code and warns on a missing `[Claude]`.
- **Sequences created by `play-builder`** get the name at creation, inactive. **Renaming an
  existing sequence is a UI action.** Apollo has no additive way to rename one:
  `apollo_sequences_update` takes the full step tree and deletes every step absent from the
  payload. Do not use the API to save a manual step.
- **A play triggered by an absence** (no live postings, say) may have no account list,
  because a list is built from what a search returns. Its missing list is not evidence the
  play was retired.
- A list may deliberately span two plays while a distinguishing field is unresolved. A
  sequence may not: a sequence enrolls one play's contacts or it has no enrollment rule.

## A worked shape: the 2x2 plus an override

One common way to write plays, and the one the demo uses, is two free-to-resolve questions
(does the company have a GTM team? is it hiring GTM?) giving four quadrants, plus a recency
play that outranks two of them. It is an example of how criteria can be structured, not a
default: a company selling to clinics, or to school districts, will route on entirely
different situations, and its plays should say so in its own words.
