# Multi-Agent Research Fan-Out Harness

How the engine researches N companies in parallel without losing attribution, duplicating entities, or blowing budgets. The harness is a deterministic orchestration script (scripts/fanout_workflow.js) that spawns one researcher per company plus a completeness critic, with ALL durable output landing in the Research Vault. Conversation memory is never the store.

Runs only on explicit human opt-in, with the cost statement given first (see references/run-manifest.md). A fan-out is a spend event: Firecrawl pages, actor calls, and tokens all meter per company.

## Design decisions and why

**1. The orchestrator pre-creates rows; researchers only append.**
Entity resolution is the one operation that is unsafe under concurrency: two researchers meeting "Meridian Data" and "Cobalt Systems" (the same company either side of a rebrand) would create duplicate entities. So the sequential orchestrator resolves or creates every Entity row AND the batch's Run row BEFORE fan-out, then hands each researcher its pre-created record IDs. Researchers never create Entities or Runs; they append Facts and Questions linked to the IDs they were given. Parallel appends to distinct rows cannot collide.

**2. Researchers return structured facts; a writer stage commits them.**
Each researcher's contract is a JSON schema (facts + questions + audit notes), not direct database writes. A separate writer stage validates provenance completeness (source URL or inference tag, source type, method, captured-at, confidence) and runs the supersede protocol before anything touches the Vault. This puts the write rules in ONE place instead of N researcher prompts, and a researcher that hallucinates a malformed fact fails validation instead of polluting the base.

**3. Attribution is structural, not remembered.**
Every fact carries Agent = "fanout-researcher-{index}" and the batch Run link. When a fact is later challenged, the trail is: fact → run → cost summary → the researcher's audit notes. Captured At is the scrape date the researcher observed, not the write time.

**4. Re-validation is the same run, run again.**
Refreshing a company is not a special mode. The researcher works from a clean prompt; the writer stage diffs its facts against current ones per Entity + Field Key: same value means no write, changed value means supersede. The orchestrator's final report lists every superseded → replacement pair per company. That list IS the change report, mechanically.

**5. The critic closes the loop before the write.**
Per company, a critic agent receives the researcher's output plus the onboarding-template field list and answers one question: what is missing? Unresearched fields become Questions rows (routed by persona); weakly sourced facts get flagged for the writer to downgrade confidence. The critic never adds facts; it only subtracts overconfidence.

**6. Stages pipeline; nothing barriers.**
Company A's critic runs while company B is still researching. The only sequential points are the orchestrator's pre-create (before) and the summary (after).

## Concurrency, budget, failure

- Default width: whatever the host Workflow tool schedules. The script sets no concurrency limit of its own; `max_companies` (default 10) caps how many companies a run will process, not how many run at once. Pass more and the platform queues them. If you need a specific width, measure it on your host rather than assuming one.
- Budget guard: the script takes a per-company page estimate and a hard cap in args; it stops launching new researchers when projected spend meets the cap and reports what it skipped. No silent truncation.
- A researcher that dies returns null; the writer skips it and the summary lists the company as FAILED with the resume path (rerun with just that company; the pre-created rows are reused).
- The scrape rules inside researchers are the standard ones: Firecrawl markdown, no paid enrichment tools inside fan-out (Apollo reveals and actor runs stay in the sequential orchestrator where the human gate lives).

## Invocation

The harness lives at scripts/fanout_workflow.js and is invoked through the platform's Workflow tool with args:

```json
{
  "companies": [{"name": "Cobalt Systems", "domain": "cobaltsystems.example", "entity_id": "recXXX"}],
  "run_id": "run-YYYY-MM-DD-batch",
  "run_record_id": "recYYY",
  "vault": {"base_id": "{AIRTABLE_VAULT_BASE_ID}", "facts_table": "{AIRTABLE_TBL_VAULT_FACTS}", "questions_table": "{AIRTABLE_TBL_VAULT_QUESTIONS}"},
  "budget": {"max_pages_per_company": 12, "max_companies": 10},
  "as_of_date": "YYYY-MM-DD"
}
```

The orchestrating session fills entity_id and run_record_id from its pre-create step, and passes as_of_date explicitly (workflow scripts cannot read the clock). Instance IDs come from the instance config at call time; the script file itself stays tokenized.
