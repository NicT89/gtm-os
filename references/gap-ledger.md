# The gap ledger: leave every system more complete than you found it

The engine reads far more than it writes. It learns a company's tool stack in Step 2, spends
it once in Step 4, and lets it evaporate. The next run pays for the same research again.

**Gaps are work to do, not findings to report.** A reported gap nobody actions is a silent
gap with better manners. Nobody schedules "go fill in the empty fields", because there is no
moment when that is anybody's job, so it has to be the run's job.

## Why during the run and not later

**A run is the only moment when closing a gap is free.** The data is already in hand and
already paid for. Writing it costs no extra call and no extra credit.

A week later the same field costs a full re-research: the postings call, the scrape, the
reconciliation against what is already there. Observed 2026-09-07: a run held eleven
verified tools for a company, used one of them in a composed field, and dropped the other
ten on the floor. The field that would have held them already existed and was empty.

Assume the workspace is incomplete. It nearly always is, and a run that only consumes
context while never repairing it leaves the next run exactly as poor as this one.

## What makes this dangerous, and the gate that fixes it

A bad blueprint gets caught: a human reads it before it sends. **A bad field write is not
caught by anything.** It propagates into every later run, and nothing downstream can tell a
written fact from a researched one. Auto-filling a CRM is how one wrong value becomes the
whole workspace's wrong value.

So every write is gated on two questions: how well the fact is known, and who put the
current value there.

| field state \ confidence | verified | medium (vendor estimate) | inferred |
|---|---|---|---|
| **empty** | write | write **only** if the field accepts estimates, else propose | propose |
| **stale** (machine-written) | write | propose | propose |
| **human-entered** | propose | propose | propose |
| **filled and fresh** | skip | skip | skip |

`scripts/gap_ledger.py` is that table, and `tests/test_gap_ledger.py` asserts it cell by
cell rather than spot-checking, because a wrong cell here is not visible anywhere else.

### The two rules that carry the table

**Never overwrite a human without asking.** Somebody who typed a value made a decision. The
engine may propose a replacement and may not quietly make one, whatever its confidence, and
however old the value is. Age does not demote a person's decision to a machine's. The one
exception is not an exception: a field a person left BLANK is a gap, not a choice.

**Inferred facts are never written.** They are how a vendor's absent value becomes a number
in an email. Apollo returning `organization_revenue: 0.0` for a private company is the
worked example: written once, it is indistinguishable from a researched zero forever after,
and the falsifiability test cannot catch it because the number came from a tool.

### Absence is not zero

`0`, `0.0` and `false` are values. Only `null`, an empty string, and an empty list or object
are gaps. Conflating a real zero with a missing value is the defect this whole module exists
to prevent, and it is asserted directly in the tests.

## Running it

```bash
python3 scripts/gap_ledger.py --record record.json          # human-readable
python3 scripts/gap_ledger.py --record record.json --json   # for the audit trail
python3 scripts/gap_ledger.py --schema                      # the input shape
```

Exit 0 means every gap this run can close is closed and nothing needs a person. Exit 1 means
the propose queue is not empty. Exit 2 is a malformed record.

Each field carries its `confidence`, its `provenance` (`machine`, `human`, or `unknown`), an
`updated_at`, and optionally its own `stale_after_days` and an `accepts_estimates` flag. The
default freshness window is 90 days, deliberately generous: churning a field every run costs
credits and teaches people to ignore the diff.

## What a skill does with the result

1. **Write the write queue.** No approval needed; that is what the gate is for.
2. **Surface the propose queue once**, at the end, as a list rather than as a series of
   interruptions. Say what each item would become and what it would cost.
3. **Record both in the run's Cost Summary and Notes**, so a later reader can tell which
   fields this run filled and which it declined to.
4. **Never silently skip the propose queue.** A run that closes nothing and says nothing is
   the behavior this document exists to end.

## Where the gaps usually are

Three places, in the order they cost the most:

- **The CRM.** Fields that exist, are empty, and would be filled by research the run already
  does. `Tech Stack Details` is the canonical case: it exists in the reference deployment,
  A11 research fills it, and nothing wrote to it before 1.9.0.
- **The seller's own brand kit.** A stale positioning line poisons every blueprint rather
  than one, and nothing checks it. Propose, never write: brand positioning is a human's
  decision by definition. `gtm-blueprint` Step 2's preflight is where the drift surfaces.
- **The Vault.** An entity with no aliases, a fact with no source URL, a question never
  closed. These degrade retrieval quietly rather than loudly.
