// GTM research fan-out — a Workflow-tool script, NOT a standalone ES module.
//
// READ THIS BEFORE "FIXING" THE PARSE ERROR AT THE BOTTOM OF THIS FILE.
//
// A standard ES-module parser rejects this file with "Illegal return statement"
// on the final `return`, and reports `args`, `log`, `phase`, `agent`, and
// `pipeline` as undefined. Both reports are correct about the syntax and wrong
// about the file. This is not a module that gets imported: it is a script BODY
// that the Workflow tool wraps in an async function before executing. Inside
// that wrapper the top-level `return` and `await` are legal, and the globals
// below are injected by the harness:
//
//   args      the invocation payload (contract in references/fanout-harness.md)
//   log(msg)  progress line surfaced to the operating session
//   phase(t)  marks the phase boundary named in meta.phases
//   agent()   spawns one subagent; returns its schema-validated result
//   pipeline() stages work per item so later items start before earlier finish
//
// The final `return` is how a workflow yields its result. Deleting it, or
// wrapping the body in a function to satisfy a linter, does not fix a bug — it
// removes this script's only output and the run silently returns nothing.
//
// So this file is excluded from JS linting in .coderabbit.yaml rather than
// edited to parse standalone. If you need to check it, check it against the
// contract in references/fanout-harness.md, not against a module parser.

export const meta = {
  name: 'gtm-research-fanout',
  description: 'Parallel company research: one researcher per company, critic pass, validated writes to the Research Vault',
  whenToUse: 'After the orchestrating session has pre-created Entity and Run rows and the human has approved the cost statement. Never self-invoked.',
  phases: [
    { title: 'Research', detail: 'one researcher agent per company, Firecrawl-only' },
    { title: 'Critique', detail: 'completeness critic per company against the template field list' },
    { title: 'Write', detail: 'provenance validation, supersede diff, Vault writes' },
  ],
}

// args contract (see references/fanout-harness.md):
// { companies: [{name, domain, entity_id}], run_id, run_record_id,
//   vault: {base_id, facts_table, questions_table},
//   budget: {max_pages_per_company, max_companies}, as_of_date }

const FIELD_KEYS = 'A1-A10 company basics/identity/product/motion/partners; B1-B7 org and people; C1-C9 funnel, pricing, onboarding, health, renewals, escalation; D1-D6 stack and data; E1-E7 role/scope/culture'

const FACTS_SCHEMA = {
  type: 'object',
  required: ['facts', 'questions', 'audit_notes'],
  properties: {
    facts: { type: 'array', items: { type: 'object', required: ['field_key', 'value', 'source_url', 'source_type', 'method', 'confidence'], properties: {
      field_key: { type: 'string' }, value: { type: 'string' }, source_url: { type: 'string' },
      source_type: { type: 'string' }, method: { type: 'string' }, confidence: { enum: ['high', 'medium', 'low'] } } } },
    questions: { type: 'array', items: { type: 'object', required: ['question', 'field_key', 'persona_group'], properties: {
      question: { type: 'string' }, field_key: { type: 'string' }, persona_group: { type: 'string' }, notes: { type: 'string' } } } },
    audit_notes: { type: 'string' },
  },
}

const CRITIC_SCHEMA = {
  type: 'object',
  required: ['missing_field_keys', 'weak_facts', 'extra_questions'],
  properties: {
    missing_field_keys: { type: 'array', items: { type: 'string' } },
    weak_facts: { type: 'array', items: { type: 'object', required: ['field_key', 'reason'], properties: { field_key: { type: 'string' }, reason: { type: 'string' } } } },
    extra_questions: { type: 'array', items: { type: 'object', required: ['question', 'field_key', 'persona_group'], properties: { question: { type: 'string' }, field_key: { type: 'string' }, persona_group: { type: 'string' } } } },
  },
}

const WRITE_SCHEMA = {
  type: 'object',
  required: ['written_facts', 'superseded_pairs', 'written_questions', 'rejected'],
  properties: {
    written_facts: { type: 'number' },
    superseded_pairs: { type: 'array', items: { type: 'object', properties: { field_key: { type: 'string' }, old_value: { type: 'string' }, new_value: { type: 'string' } } } },
    written_questions: { type: 'number' },
    rejected: { type: 'array', items: { type: 'object', properties: { field_key: { type: 'string' }, reason: { type: 'string' } } } },
  },
}

const cap = args.budget?.max_companies ?? 10
const companies = args.companies.slice(0, cap)
if (companies.length < args.companies.length) {
  log(`BUDGET CAP: running ${companies.length} of ${args.companies.length} companies; skipped: ${args.companies.slice(cap).map(c => c.name).join(', ')}`)
}

const researchPrompt = (c) => `You are fanout-researcher for ${c.name} (${c.domain}). Research this company for a GTM onboarding intake. Rules, all mandatory:
- Firecrawl ONLY for web content (markdown, onlyMainContent). Load Firecrawl tools via ToolSearch. Maximum ${args.budget?.max_pages_per_company ?? 12} page scrapes; map the sitemap first and choose pages deliberately: pricing, customers, partners, about/team, careers, docs, newsroom.
- NO paid enrichment tools (no Apollo reveals, no actors). Public web only.
- The intake taxonomy: ${FIELD_KEYS}. Aim for breadth across A, C, D before depth anywhere.
- Every fact: field_key, value (complete sentence, no em dashes), source_url (the exact page), source_type (primary-site, press-release, job-posting, linkedin, github, review-site), method 'firecrawl', confidence. Facts you infer get method 'inference', '(inferred)' in the value, and confidence low; source_url may then be empty.
- Partner taxonomy check: classify integrations as API vs embedded/white-label vs channel; check the PARTNER side's FAQ and legal pages for white-label credit lines.
- Code footprint: search GitHub for the company org under current and former names; note platform modules and infra repos.
- Merged or acquired recently? Note it in audit_notes and treat enrichment-style aggregator pages as suspect; prefer primary press releases.
- What you cannot establish becomes a question routed to the likeliest-to-know persona (Sales, Marketing, Customer Success, Product, Ops/RevOps, Finance, Engineering, Leadership, Support/Chatbot).
- audit_notes: 5-10 lines on what you scraped, what was thin, what a rerun should hit. Capture date for all facts is ${args.as_of_date}.
Return ONLY the structured object.`

const criticPrompt = (c, research) => `You are the completeness critic for ${c.name}. A researcher produced this intake research: ${JSON.stringify(research).slice(0, 20000)}
Against the field taxonomy (${FIELD_KEYS}), answer ONLY: (1) missing_field_keys: fields with no fact and no question; (2) weak_facts: facts whose source does not actually support the claim or whose confidence is overstated (be specific in reason); (3) extra_questions: questions that should exist for the missing fields, persona-routed. You may NOT add facts. Subtraction of overconfidence only.`

const writerPrompt = (c, research, critique) => `You are the Vault writer for ${c.name}. Load the Airtable MCP tools via ToolSearch (create_records_for_table, search_records, update_records_for_table, get_table_schema).
Vault: base ${args.vault.base_id}, Facts table ${args.vault.facts_table}, Questions table ${args.vault.questions_table}. Entity record ${c.entity_id}, Run record ${args.run_record_id}.
Input facts: ${JSON.stringify(research.facts).slice(0, 20000)}
Critic verdicts: ${JSON.stringify(critique)}
Protocol, in order:
1. Downgrade confidence to low on any fact the critic flagged weak (do not drop it unless the source contradicts the claim outright; then reject it).
2. Validate provenance on every fact: source_url present OR method inference with '(inferred)' in value. Incomplete provenance -> reject with reason, never write.
3. Read the table schema, then for each surviving fact search current-status facts for this entity + field_key. Same value: skip (no duplicate). Different value: create the new fact (Status current, Supersedes -> old record, Agent 'fanout-writer', Captured At ${args.as_of_date}, Run link), then flip the old record to superseded. No match: create fresh.
4. Write all questions (researcher's plus critic's extra_questions) as open Questions rows: entity link, field_key, persona_group, channel 'interview' unless the question text implies a support-channel path.
5. Return the counts, every superseded pair (field_key, old_value, new_value), and every rejection with reason.`

phase('Research')
const results = await pipeline(
  companies,
  (c) => agent(researchPrompt(c), { label: `research:${c.name}`, phase: 'Research', schema: FACTS_SCHEMA }),
  (research, c) => research
    ? agent(criticPrompt(c, research), { label: `critique:${c.name}`, phase: 'Critique', schema: CRITIC_SCHEMA, effort: 'high' })
        .then(critique => ({ research, critique }))
    : null,
  (bundle, c) => bundle
    ? agent(writerPrompt(c, bundle.research, bundle.critique), { label: `write:${c.name}`, phase: 'Write', schema: WRITE_SCHEMA })
        .then(w => ({ company: c.name, ...w, missing: bundle.critique.missing_field_keys }))
    : null,
)

const done = results.filter(Boolean)
const failed = companies.filter((c, i) => !results[i]).map(c => c.name)
const supersededTotal = done.reduce((n, r) => n + r.superseded_pairs.length, 0)
log(`Fan-out complete: ${done.length}/${companies.length} companies, ${done.reduce((n, r) => n + r.written_facts, 0)} facts, ${supersededTotal} superseded (the change report), failures: ${failed.join(', ') || 'none'}`)

return {
  run_id: args.run_id,
  companies_done: done,
  companies_failed: failed,
  change_report: done.filter(r => r.superseded_pairs.length).map(r => ({ company: r.company, superseded: r.superseded_pairs })),
  rejected_facts: done.filter(r => r.rejected.length).map(r => ({ company: r.company, rejected: r.rejected })),
}
