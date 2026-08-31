# Research Vault (persistent research data spine)

The Vault is where all company and people research lands. Skills write facts here with full provenance; conversation memory is never the system of record. One Airtable base per instance (move to Supabase only if volume demands it; the schema ports 1:1).

Instance values are resolved by [SETUP.md](../SETUP.md) into `instance-config.json` at the plugin root (git-ignored). This reference carries the schema only; your base and table IDs live in that file, and skills address them by key the same way they address the posts base:

| Key | Value |
|---|---|
| `{AIRTABLE_VAULT_BASE_ID}` | The Vault base (`app...`) |
| `{AIRTABLE_TBL_VAULT_FIELD_KEYS}` | Field Keys table (`tbl...`) |
| `{AIRTABLE_TBL_VAULT_ENTITIES}` | Entities table |
| `{AIRTABLE_TBL_VAULT_FACTS}` | Facts table |
| `{AIRTABLE_TBL_VAULT_RUNS}` | Runs table |
| `{AIRTABLE_TBL_VAULT_QUESTIONS}` | Questions table |

All six keys are optional in the schema: an install that does not run the Vault leaves them empty and every Vault write step degrades to report-only. A skill that finds them empty says so and skips the write; it never guesses a base. Building the Vault is Step 3b of [SETUP.md](../SETUP.md), routed through [environment-setup.md](environment-setup.md) like every other connector.

## Why this shape

Three requirements drove the design, all from production (the first live-fire deployment):

1. **Attribution**: every fact must answer "who captured this, from where, when, and how confident are we." A fact without a source URL or an (inferred) tag is not a fact.
2. **Re-validation as a mechanical diff**: rerunning research must not overwrite history. New facts SUPERSEDE old ones; the set of superseded facts between two runs IS the gap/change report. No separate audit step to design.
3. **Fan-out safety**: many agents writing concurrently must not collide or blur attribution. Append-only facts keyed by run and agent make parallel writes safe by construction.

## Tables

### Field Keys (reference table)
One row per taxonomy code (A1-E7 plus `other`) with its section and its verbatim question from the onboarding template, so nobody has to memorize what B3 means. Facts and Questions keep single-select Field Key columns whose option names match this table's Key column.

### Entities
Canonical companies and people. One row per real-world thing, ever. People get entity rows once the engine holds dedicated research on them (scraped posts, facts, run targeting), linked to their employer via Related Entities.

| Field | Type | Rules |
|---|---|---|
| Entity Name | primary text | Canonical current name (post-rebrand name, e.g. "Cobalt Systems" not "Meridian Data") |
| Entity Type | select: company, person | |
| Domain | text | Companies only, bare domain |
| LinkedIn URL | text | |
| Aliases | long text | Prior names, rebrand history, one per line. Rebrands NEVER create a second entity row |
| Notes | long text | Human context only: role, warnings, constraints. System IDs never live in Notes |
| External IDs | dedicated text columns per system (e.g. `Apollo Org ID` for the vendor's global company record, `Apollo Record ID` for the saved account/contact in YOUR workspace). Add a column per system rather than packing IDs into Notes |
| Related Entities | link to Entities | Person-to-employer, subsidiary-to-parent, partner-to-partner |

### Facts
Append-only. The atom of the whole system.

| Field | Type | Rules |
|---|---|---|
| Fact | primary text | Short scannable label, a few words. Never repeat the field key (it has its own column) and never carry the detail (that is Value) |
| Field Key | select | The onboarding template taxonomy (A1-E7) plus `other`. This is the join key between research and the intake spine |
| Value | long text | The fact itself, complete sentences, no em dashes |
| Value Type | select: text, number, date, url, json | |
| Source URL | text | REQUIRED unless Method is `inference`, then Value carries "(inferred)" |
| Source Type | select: primary-site, press-release, job-posting, linkedin, github, review-site, enrichment-tool, support-channel, human-answer, inference | |
| Method | MULTI-select: firecrawl, webfetch, apify-actor, apollo, github-search, manual, agent-interview, inference | One fact can combine methods. New methods are added as options, never free-typed |
| Captured At | date | The capture date, not the write date, if they differ |
| Agent | text | Which agent or session wrote it (e.g. "cowork-fable", "fanout-researcher-3") |
| Confidence | select: high, medium, low | |
| Status | select: current, superseded | New facts land `current`. Superseding flips the OLD row, never deletes it |
| Entity | link to Entities | |
| Run | link to Runs | |
| Supersedes | link to Facts | Points at the row this one replaces |

**Supersede protocol (refined in production)**: before writing a fact, query current facts for the same Entity + Field Key. Supersede on CONTRADICTION or REPLACEMENT: if the new fact corrects or enriches-and-replaces the old one, write the new row with Supersedes → old row and flip the old row to `superseded`. COEXIST on COMPLEMENT: two facts under the same field key that are both true and about different aspects both stay `current` (a B5 fact naming the team and a B5 fact naming its director are complements, not conflicts). If the value is the same, do not write a duplicate. The re-validation report for a run is: all rows that run superseded, paired with their replacements.

### Runs
One row per research execution (a skill invocation, a fan-out batch, a scheduled refresh).

| Field | Type |
|---|---|
| Run ID | primary text, `run-YYYY-MM-DD-target[-n]` |
| Date | date |
| Target | text, human-readable summary only |
| Target Entities | link to Entities: every company AND person the run researched. People researched by a run must exist as Person entities |
| Skills | MULTI-select from the known skill roster; new skills are added as options, never free-typed |
| Cost Summary | text, written ONLY after the run completes, fixed format: `Apollo credits: N \| Actor USD: N \| Firecrawl credits: N \| Status: final`. Pre-run estimates live in Notes |
| Artifacts | long text: file paths and URLs to what the run produced. Where the base supports attachments, drop the files in directly |
| Notes | long text |

### Questions
The Ask column, made durable and agent-consumable. gap-closer reads from here.

| Field | Type | Rules |
|---|---|---|
| Question | primary long text | ONE question per row, phrased ready to ask. Multi-part questions are split so each can close independently |
| Field Key | select | Same taxonomy as Facts |
| Persona Group | MULTI-select: Sales, Marketing, Customer Success, Product, Ops/RevOps, Finance, Engineering, Leadership, Support/Chatbot | Likeliest-to-know routing; more than one persona may plausibly hold the answer |
| Channel | select: interview, email-draft, linkedin-draft, support-chat, forum, other | |
| Status | select: open, drafted, asked, partial, answered, retired | `partial` = part of the question is answered; Notes and Answer Fact say what remains |
| Asked At / Answered At | dates | |
| Notes | long text | Why the question matters and what the answer would change, written for the human who will ask it. Never restate the field key or cite pipeline internals (critic names, run mechanics) |
| Entity | link to Entities | |
| Answer Fact | link to Facts | Set when answered; the answer is written as a Fact with Source Type `human-answer` or `support-channel`, and the question flips to `answered` |

## Write rules for every skill and agent

1. Resolve the entity first. Search Entities by name, domain, AND aliases before creating. A rebrand or acquisition updates Aliases on the existing row.
2. Open (or reuse) a Run row before writing facts. Facts without a Run link fail review.
3. Provenance complete or the write is rejected: Source URL (or inference tag), Source Type, Method, Captured At, Agent, Confidence. No exceptions, including for "obvious" facts.
4. Append, supersede, never edit Values in place and never delete.
5. Questions close through Facts: an answered question always produces a Fact row carrying the answer's provenance (who answered, on what platform, raw text in Value, date).
6. Report the diff: any run that superseded facts ends by listing old → new pairs. That list is the change report; do not write a separate one.
