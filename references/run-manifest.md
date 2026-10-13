# Run Manifest Convention (resumability + cost budgeting)

Every multi-step engine run (a signal scan, a deep-research pass, a scrape batch, a fan-out) maintains a manifest so a dropped connector, a dead session, or a model switch never loses work. Proven need: the Apify MCP transport dropped mid-scrape during the first live-fire deployment; the rerun succeeded only because the run state was reconstructable.

## The manifest

One JSON file per run, written to the run's working folder at start and updated after EVERY completed step (not batched at the end):

```json
{
  "run_id": "run-2026-08-16-cobalt",
  "target": "Cobalt Systems",
  "skill": "company-deep-research",
  "started_at": "2026-08-16T14:00:00Z",
  "vault_run_record": "recXXXXXXXXXXXXXX",
  "budget": {
    "stated_to_human": true,
    "apollo_credits_planned": 10,
    "actor_spend_planned_usd": 2.50,
    "spent_so_far": {"apollo_credits": 4, "actor_usd": 1.10}
  },
  "steps": [
    {"id": "extract-jd", "status": "done", "artifact": "jd.md", "at": "..."},
    {"id": "site-sweep", "status": "done", "artifact": "site/", "at": "..."},
    {"id": "org-map", "status": "in_progress", "resume_hint": "completed C-suite and VP bands; Director band next"},
    {"id": "post-scrape", "status": "pending", "depends_on": "org-map"}
  ]
}
```

## Rules

1. **Write-ahead**: the step list is written before execution starts, so the plan survives even a first-step failure.
2. **Update-on-complete**: each finished step updates its row with status, artifact path, and timestamp before the next step begins.
3. **Resume protocol**: a resuming session reads the manifest, verifies each `done` step's artifact actually exists, re-runs any step whose artifact is missing, and continues from the first non-done step using its `resume_hint`.
4. **Idempotent steps**: steps that write to external systems (Airtable, CRM) must check-before-create (dedupe by natural key: Post ID, email, run ID) so a resumed run never double-writes.

## Cost budgeting

Costs are stated BEFORE spend, covering all meters, not just the obvious one:

- **Apollo credits** (reveals; search is free)
- **Actor spend** (Apify runs are metered per result; estimate from the target count)
- **Scrape volume** (Firecrawl page counts on large crawls)
- **Token cost** (for fan-out runs: rough per-agent estimate times agent count)

The pre-spend statement to the human names each meter, the estimate, and the cap. Actual spend lands in the manifest's `spent_so_far` as it accrues and in the Vault Run row's Cost Summary at the end. A run projected to exceed its stated cap STOPS and asks; it does not finish and apologize.

**Compute that, do not remember it.** `scripts/run_cost.py` takes the meters and caps and returns the tally, the Cost Summary line in the Vault's exact format, and a non-zero exit the moment any meter is over its cap. Before 1.10.0 nothing produced the number, so a rule that depends on comparing spend to cap depended on someone doing arithmetic in their head and writing it down afterwards. On the 2026-09-07 run the figure was tracked by hand in a chat window and would have been lost with the conversation.

It also carries the write half, because since 1.9.0 runs fill fields as well as spend on them. A run that spent credits and filled nothing is a different event from one that spent the same and closed six gaps, and only one of those is worth repeating.

## Run mode: every result says what kind of run produced it

Since 1.10.0 the engine can produce results without touching a live system (the offline
demo), so every report, run artifact and manifest carries a `run_mode`, and every row in a
report carries a label. There are four, defined here and nowhere else:

| Label | Input | Logic | Spend and writes |
|---|---|---|---|
| `SIMULATED` | Synthetic accounts and people | The engine's real decision code | None |
| `FIXTURE` | A hand-written stand-in for an API or model response | Not applicable: the row IS the stand-in | None |
| `PREVIEW` | Synthetic input through a real deployment's config | The engine's real decision code | None |
| `LIVE` | Real calls against the operator's own tools | The engine's real decision code | Real, behind the human gates |

The rule the labels exist to enforce: **a result that is not `LIVE` is never reported as
evidence about a real account, and a `FIXTURE` is never reported as something the engine
produced.** A demo opener is a fixture; quoting it to a prospect as "what the engine writes"
is the same defect as quoting an unsourced number.

`scripts/demo.py` emits `SIMULATED` (default) or `PREVIEW` (`--config`), and
`tests/test_demo.py` fails if any report row lacks a label. Live skills write
`"run_mode": "LIVE"` into their run artifacts; a run artifact with no `run_mode` predates
this convention and should be read as live.
