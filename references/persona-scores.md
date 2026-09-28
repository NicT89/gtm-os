# Persona scores: for each contact and for each company

The account score says whether a company is worth pursuing. A persona score says whether a
**person** there is the right one to write to, and the company view says whether the right
people are reachable at all. Both come from GTM MCP (`references/gtm-mcp.md`); this file says
what goes in, what comes out, and what is yours to define.

## What is yours: the persona, in your words

A persona is organization-specific, so it is **guided free text**, never a list of options
(the rule in CLAUDE.md, "Deterministic where it is universal, guided where it is theirs").
It lives in each play's `persona` field, and the guidance for writing it is in
`skills/play-builder/references/play-fields.md`. It is not restated here.

A persona definition the score can use names three observable things:

- **The role** and why it is theirs. "The founder or CEO running the search, because the hire
  is their decision" is scoreable. "Decision makers" is not: every title qualifies.
- **The seniority** the role implies, when it matters.
- **What disqualifies**, when something does. "Not an agency-side marketer" saves credits.

## What is universal: the inputs

These are the same for every organization, which is why they are computed rather than judged.

| Level | Input | From |
|---|---|---|
| Contact | Role match against the play's persona | Title from the free people search |
| Contact | Seniority match | Seniority from the free people search |
| Contact | Reachability tier | The tier table in `references/apollo-credit-costs.md` |
| Contact | Activity recency | The posts base, when the contact has been scraped |
| Company | Account score | `gtm-signal-scan` Step 2 |
| Company | Persona coverage | How many of the play's personas have at least one reachable contact |

An input that is not known is **flagged, not scored as zero**, the same rule as the account
score. A contact who was never scraped has unknown activity recency, not low activity.

## What comes out

- **For each contact:** a score, the play it was scored against, and the unknown inputs listed
  by name.
- **For each company:** the account score, persona coverage, and which personas have no
  reachable contact yet, which is where people search should look next.

Scores go to the CRM through the normal write path (the play's standard fields in Apollo, the
portal map's properties in HubSpot), and the score at enrollment is what an outcome record
carries (`references/outcomes.md`).

## Until GTM MCP is live

There are no persona scores. People are ranked by role fit and reachability with
`skills/gtm-signal-scan/scripts/rank_people.py`, exactly as in 1.11.0.
