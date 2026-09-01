---
name: gtm-architecture-composer
description: Compose a five-layer GTM OS architecture proposal for a company from its completed onboarding intake. Use when the user says "compose the architecture", "run gtm-architecture-composer", "draft the GTM OS for [company]", or after company-deep-research and jd-intake have produced a substantially Known template. Produces the layered architecture, the phased 60-day / 6-month / 12-month sequence, and the client-ready PDF.
---

# GTM Architecture Composer

Input: a completed (or substantially completed) onboarding template plus the company's Vault facts. Output: an architecture proposal a GTM engineer could start executing Monday. Format anchor: section 4 of a `company-deep-research` report.

Do not compose from an empty intake. If more than a third of the template's A-D fields are Unknown with no Extended Search enrichment, stop and run company-deep-research first; an architecture built on guesses is a liability with a logo on it.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Connector preflight

This skill reads the Vault, writes facts and open questions back, and renders a PDF. The Vault write needs `{AIRTABLE_VAULT_BASE_ID}`, `{AIRTABLE_TBL_VAULT_ENTITIES}`, `{AIRTABLE_TBL_VAULT_FACTS}`, and `{AIRTABLE_TBL_VAULT_QUESTIONS}`; check all four, not just the base. If **any** of them is empty, treat the Vault as absent: compose from the intake alone, write nothing back, and say so in the proposal. Partial configuration degrades the same way as no configuration, because a half-written proposal is worse than an honestly report-only one.

If `scripts/render_report.py`'s dependencies are missing, deliver the markdown and say the PDF was not rendered. Either way, route the user to the `environment-setup` skill (the plugin root's `references/environment-setup.md`) rather than improvising: not set up almost never means not owned.

## The five layers

Walk them in order; every element cites the intake field or Vault fact that justifies it.

1. **Data spine**: the canonical warehouse and the tables that matter (accounts, contacts, activities, product usage, revenue). If the company runs two warehouses (a merger signature), the proposal must name the consolidation question explicitly rather than pick a winner without evidence.
2. **Integration layer**: how each stack tool connects to the spine. Use references/mcp-coverage-map.md to mark which tools have MCP paths (agent-operable), which are API-only (bulk/scheduled), and which are closed. The decision rule: MCP for agent workflows, API for bulk sync, the warehouse stays queryable.
3. **Agent workflows**: the recurring GTM motions worth automating, each mapped to the four pillars (customer acquisition, sales journey, onboarding, retention/expansion) and stamped with its human gates. Draft-for-human on all outbound; credentials never held by agents.
4. **Micro apps**: the lightweight rep-facing and customer-facing tools (account views, calculators, prep tools) that turn spine data into daily leverage. Match the company's existing build culture; if they already ship public tools, extend that pattern.
5. **Observability**: run manifests, cost tracking, CRM-sync health, and attribution capture. Every automated motion must be able to answer "did it run, what did it cost, did it move pipeline."

## The phased sequence

- **60 days**: instrument and stabilize. The attribution gaps and sync-health checks land here because everything after depends on trusting the data.
- **6 months**: the two or three agent workflows with the clearest revenue or cost line, plus the first micro apps.
- **12 months**: the compounding layer: health scores feeding renewal motions, expansion signals, and the observability that proves ROI.

Each phase item carries: the intake field it answers to, the owner persona, the dependency it waits on, and how success is measured in pipeline, retention, or cost terms. No initiative ships without a measurement line.

## Output

Markdown to the run folder, facts and open questions to the Vault, client-facing PDF through scripts/render_report.py (status tables and timeline charts are supported natively). No em dashes. Attach the Ask list as the final section; the architecture's open risks ARE the unanswered questions.
