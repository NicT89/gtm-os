# The local SQLite store

GTM OS keeps one small SQLite database per engagement beside the connectors. This explains what it is for, what it adds that the connectors cannot, and where it lives.

## What it holds

Sources and evidence (URL, exact text, date read, screenshot file), claims and which sources support them, every question ever asked of the customer with its answer, date, source and confidence, an event trail per question, an efficacy log (what each tool saved or cost, measured or estimated), and the register of research reports. Schema: `skills/evidence-register/scripts/schema.sql`.

## Why a local database next to HubSpot, Apollo and Brand Kit OS

Each connector is the system of record for its own objects. None of them is built to record the work around them. Observed in this repo and in live runs:

| Need | HubSpot, Apollo, Brand Kit OS | Local database |
|---|---|---|
| Provenance per claim: which page said it, on what date, with a screenshot | no field for it on a deal, account or kit record | `sources` + `claim_sources`, with a view that fails when a claim has no source |
| Question lifecycle: asked, answered, by whom, when, how confident | no native object; notes are unstructured | `questions` + `question_events`, queryable by status and priority |
| Closed vocabularies | Brand Kit OS company size accepts fixed buckets only; HubSpot enumerations take fixed internal values | free columns, exact numbers (a stated 30 to 150 stays 30 to 150) |
| Calculated or protected fields | HubSpot `hs_mrr` and `hs_arr` cannot be written; Apollo has accepted fields and silently discarded them (CLAUDE.md) | stores what you decided, with the basis |
| Cross-system joins | each connector sees only itself | one place to compare CRM, enrichment and brand-kit facts |
| Cost and rate limits | calls cost credits or hit limits; some require approval per write | free, offline, instant, no approval |
| History and diffs | latest value only, or per-system history | a text dump that diffs in version control |
| Efficacy of the tools themselves | not recorded anywhere | `efficacy_log`, with `measured` versus `estimate` |

Honest limits: it is not a CRM, it has one writer at a time, and a binary `.db` cannot be diffed or merged. It augments the connectors; it never replaces them, and anything a connector should own (a customer, a deal) is written there, not here.

## Where it lives

| Option | Survives devices and sessions | Team access | Trade-offs |
|---|---|---|---|
| **A. Local device folder (default)** | only on that device | none | fastest; zero setup; lost with the device unless backed up |
| **B. Text dump (`.sql`) as a project file, `.db` rebuilt per session** | yes | everyone with project access | needs a rebuild step (one command); the dump is the source of truth; works where a project store refuses binaries (observed: the store rejects NUL bytes) |
| **C. Binary `.db` in a synced drive folder** | yes | whoever has the folder | concurrent writers can corrupt or fork the file; not diffable; acceptable for one person on several devices |
| **D. Hosted database (for example Supabase Postgres)** | yes | yes, with roles | needs hosting, credentials and a migration of the schema; the right step when several people write at once |

Recommendation (inferred, not yet measured across teams): A as the working copy, B as the shared record. At the start of a session rebuild the `.db` from the project's dump; at the end export the dump and write it back. Move to D only when more than one person writes in the same week.

```bash
python3 skills/evidence-register/scripts/evidence_db.py rebuild engagement.db engagement.sql
# ... work ...
python3 skills/evidence-register/scripts/evidence_db.py export engagement.db engagement.sql
```

Never put client data in this repo. The dump belongs in the engagement's project or folder.

## How to explain it in one minute

The connectors hold the customers, the deals and the brand. The database holds why we believe things: what each fact came from, what we still need to ask, what the answer was and when, and what our own tools saved. It is local so it is free, instant and private; the dump is shared so the whole team sees the same record.
