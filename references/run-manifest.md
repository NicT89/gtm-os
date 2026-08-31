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
