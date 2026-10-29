# Evidence rules and pitfalls

## What counts as a good highlight
- The needle is the smallest string that makes the claim true ("$399", not the pricing paragraph).
- For a number, use `=` so the match is the whole text node and not the same digits elsewhere.
- When a page shows a value at several places, capture one item per placement or pick the one the claim cites.
- If the page loads text late, raise `wait` on that item.

## Failures seen in practice
- A single-item re-run overwrote the results file and lost the others: `capture.py` now merges.
- A model-summarised page read (WebFetch) produced quotes that were not on the page: re-read with `probe.py` before quoting.
- A claim in a card header disagreed with the body of the same page: record both, mark the claim UNVERIFIED or say which was used.
- A price on an archive snapshot sat outside the saved frame: highlight the row that is visible, and put the out-of-frame text in the notes column, labelled as such.
- Rate-limited or blocked pages return partial text: confirm `body_len` and `present` in `capture_results.json` before trusting a capture.

## Claim-to-source rule
A KNOWN claim with no row in `claim_sources` fails `v_claims_without_source`. An INFERRED claim names the claims it rests on in `label_basis`. UNVERIFIED claims name who reported them and where.

## Question database fields worth filling
priority (P1 needed to start, P2 needed in the first 60 days, P3 as time allows), addressed_to (a role, never a name), why_it_matters, related_deliverable, date_asked, asked_in_source, then on answer: date_answered, answer_text, answer_source, answer_confidence, answered_by_role, answered_in_version, follow_up.
