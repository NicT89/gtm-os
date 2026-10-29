---
name: evidence-register
description: Build and maintain the evidence behind a report: highlighted web screenshots, evidence IDs, internal breadcrumbs, a claim ledger and an engagement question database. Use when a report, proposal or analysis needs sourced claims, when the user says "add evidence", "screenshot the source", "highlight the text", "evidence register", "breadcrumbs", "claim ledger", "open questions database", or before any gtm-intelligence-report is built.
---

# Evidence register

Every claim a client reads must trace to something they can check. This skill produces that trail: a screenshot with the referenced text highlighted for web sources, a breadcrumb for internal sources, a ledger linking claims to both, and a database of every question asked and answered.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## The four labels and the format

A claim line starts with its label, then a colon, then the claim, then the evidence IDs: `KNOWN: text [EV-03]`. The label is never trailing.

- **KNOWN**: read in a source you can cite. Needs at least one evidence ID.
- **INFERRED**: reasoned from known facts. Say what it rests on.
- **UNVERIFIED**: reported but not confirmed (for example a claim made on a call and not found publicly). Never promote it without a source.
- Contradictions between sources are findings. Record both sources and say which was used and why.

## Evidence IDs

| Prefix | Meaning | Proof an outsider can follow |
|---|---|---|
| `EV-nn` | Public web page | URL, exact text, date read, screenshot with that text highlighted |
| `EV-Wn` | Archived snapshot | archive URL with timestamp, screenshot of the snapshot |
| `INT-xx-mmss` | Call transcript | file path plus `[mm:ss]` |
| `INT-DOC-...` | Project document | project path and section |
| `INT-BK-...` | Brand record | kit ID, record type, field name |
| `INT-CRM-...` | CRM record | portal-agnostic description plus record type and record ID |
| `R-nnn` | Research URL read but not yet screenshotted | listed with status `screenshot pending`; never cited as KNOWN in a client-facing claim until captured |

## Procedure

1. **Probe before you cite.** `scripts/probe.py` prints the exact wording on a live page. Write the needle from that output, not from memory.
2. **List items** in `items.json` (id, url, needles). A needle prefixed with `=` must equal the whole text node (use for prices and short values).
3. **Capture** with `scripts/capture.py --items items.json --out evidence/`. Results merge into `capture_results.json`. Resolve every `CHECK` line: a needle not highlighted means the screenshot does not prove the claim.
4. **Archives** (web.archive.org) are usually blocked from sandboxes. Capture them through a real browser session and save as `<id>.png`.
5. **Database.** `scripts/evidence_db.py init`, then `ingest` the capture run, then add internal sources, claims and `claim_sources` rows. `summary` exits 1 if any active claim has no source: fix that before building a report.
6. **Compress** screenshots for embedding: `scripts/compress_images.py`.
7. **Questions.** Every question for the customer goes in `questions`; answers fill `answer_text`, `date_answered`, `answer_source`. Never delete a question; change its status and add a `question_events` row. At the start of a session and whenever a recording, transcript or email arrives, read `v_open_questions` and close what the new material answers.
8. **Persist.** Export the dump (`evidence_db.py export`). The text dump is the source of truth; the `.db` is rebuilt from it. See `references/local-sqlite-store.md` at the plugin root for where each copy lives.

## Rules

- Highlight the exact text, not the page. A full-page screenshot proves nothing.
- Do not cite an item whose capture failed or whose needle was not highlighted.
- Person-neutral wording: the company, never an individual, in claims and quotes.
- Read the page again before reusing a number from an earlier session; pages change.
- Screenshots are evidence of what a page said on the date read. Keep that date visible.

Details and pitfalls: `references/evidence-rules.md`.
