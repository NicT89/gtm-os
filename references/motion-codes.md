# Motion codes: M1-M5, and where they must be written down

`M1`-`M5` appear in `references/signals-doctrine.md`'s `Routes to` column, in Apollo list
names, and in sequence enrollment rules. Until 1.9.4 **no legend for them existed anywhere**,
which made every routing cell unreadable to anyone who did not already know the scheme — and
the operator who built them reported forgetting which was which.

This file is that legend. It was **recovered from live artifacts, not invented**: each row's
definition is the enrollment criterion written in the corresponding Apollo sequence's own
description, cross-checked against the Apollo list names and the doctrine's routing column.

## The five

| Code | Enrollment criterion | Target persona | Apollo sequence |
|---|---|---|---|
| **M1** | >= 1 GTM persona in seat, and **no** live GTM job postings | The GTM person | `GTM Outbound AI- No Jobs Posting` |
| **M2** | Funded ($2M+ in 6 months), **no** GTM team, **not** hiring GTM | Founder / co-founder | `[Claude] Founder Direct - Funding Signal` |
| **M3** | **No** GTM team, hiring their **first** GTM leader | Founder / CEO running the search | `(Assisted)First GTM Hire` |
| **M4** | >= 1 GTM persona in seat **and** hiring additional GTM roles | The GTM team member | `[Claude] GTM Team Expansion` |
| **M5** | A GTM leader has been in seat **<= 9 months** | The new leader | `[Claude] First 90 Days` |

## The shape: a 2x2 plus a recency override

M1-M4 are the four quadrants of one 2x2, which is what `signals-doctrine.md` signal 6 means
by "the 2x2 routing axis":

```
                  NOT hiring GTM        Hiring GTM
                +---------------------+---------------------+
  HAS GTM team  |        M1           |        M4           |
                |  (the GTM person)   | (the GTM member)    |
                +---------------------+---------------------+
  NO GTM team   |        M2           |        M3           |
                |    (the founder)    |  (founder/CEO)      |
                +---------------------+---------------------+
```

**M5 is not a fifth quadrant. It is an override on recency** and it OUTRANKS M3 and M4: a
company that would route to M4 routes to M5 instead when its GTM leader is <= 9 months in
seat, because a new leader's first ninety days is a different conversation from a team's
expansion. Doctrine signal 4 states the override; signal 5 sends a filled req to M5 as well.

Two consequences worth stating, because both are easy to get wrong:

**M1's trigger is an ABSENCE.** It fires on no live postings, which is why M1 was the only
code with no Apollo list — a list is built from things a search returns, and this motion is
defined by what a search does not. Its absence from the workspace is not evidence it was
retired.

**The quadrant is decidable for free.** Both axes come from calls that cost nothing: GTM
persona presence is a people search by `organization_ids`, and hiring status is already a
filter on the company search. So motion assignment does not need enrichment and should not
wait for it. See `skills/gtm-signal-scan/SKILL.md`.

## Not a client motion: the job-search tracks

Two sequences are the operator's own job search and are **not** GTM motions:
`[Claude] Job Search - Hiring Manager Track` and `[Claude] Job Search - Recruiter Track`.
Their own descriptions carry the rule and it is load-bearing: **never run a company in a
job-search track and a client motion (M1-M5) at the same time**, and never run both
job-search tracks at one company. The register is different in kind — a role-fit
conversation, never a pitch and never a service offer — so a company mis-filed into M1-M5
does not merely get the wrong sequence, it gets the wrong relationship.

Code these `JS-HM` and `JS-REC` so they never read as an M-code.

## Where the code must be written

A motion that lives only in a skill's reasoning is a motion nobody can audit later. **Every
Apollo object a motion touches carries its code in its own name**, at the front, in
parentheses:

- **Lists** — `(M4) GTM Team Buyers`. Already the convention for M2, M3/M4, M4 and M5.
- **Sequences** — `(M4) [Claude] GTM Team Expansion`. **Not yet done for any sequence**, which
  is the gap: the lists say which motion they serve and the sequences they feed do not.
- **Tasks** — `[JS-HM] Email <name> - <company> (<why this person>)`.
- **Account and contact custom fields** that record a routing decision name the code in the
  value, with the date it was assigned.

`M3/M4` is a legitimate name for a list that deliberately spans two motions while the
distinguishing field is still unresolved. It is not legitimate on a sequence: a sequence
enrolls one motion's contacts or it has no enrollment rule.

## When a company's motion changes

Motion is a property of the company's current state, not a permanent label, and the state
moves: a req gets filled, a leader lands, a team is hired. **Re-derive the quadrant on every
run rather than trusting the stored value**, and when it changes, record the change with its
date and reason instead of overwriting silently — the same rule `references/gap-ledger.md`
applies to every other machine-written field.
