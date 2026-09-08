---
name: gtm-blueprint
description: Generate a customized 30-day GTM blueprint for any company, for outreach personalization fields or ad hoc proposals. Use when the user says "create a GTM blueprint", "run gtm-blueprint", "blueprint proposal for [company]", "populate the blueprint field", "write the 30-day plan for [company]", "set up blueprint enrichment for [client]", or whenever composing the `<prefix> Blueprint` field or any equivalent per-company plan field in a CRM. Classifies the company's GTM motion (PLG, enterprise, founder-led, channel, regulated vertical, or a custom motion when none of them fit), verifies enrichment-field completeness with a hard gate, composes from real data against motion-specific templates, and writes back to the connected CRM or delivers in chat.
---

# GTM Blueprint (v1.1.0)

Produce a 30-day GTM plan for a target company that reads custom because it IS custom: built from their real funding, team, stack, and motion. This composition process was built and operated against a live outreach pipeline before being packaged as a template. The plan is the demo: if it could be sent to a different company unchanged, it has failed.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the installed VERSION, notify on mismatch, continue.

If the CRM connector is unavailable or a tool call fails, stop and report which capability is missing. Never compose a blueprint from memory of prior records or from guesses; a wrong "fact" in a show-don't-tell email costs more than a delayed send.

## Modes

- **Ad hoc proposal**: input is a company name, domain, or URL; output is the blueprint in chat or a document. No CRM required; the gate relaxes to "three hard facts minimum" gathered from the web.
- **Field pipeline**: batch-compose and write a Blueprint custom field for CRM contacts (the outreach merge-variable use case). The gate is mandatory here.
- **Client provisioning**: audit a client's CRM via its MCP connector, create their Blueprint-equivalent field, rebuild the provenance map for their instance, and install this process.

## Instance configuration

Read `instance-config.json` at the plugin root and resolve every `{KEY}` in this skill. If the file is missing or a needed key is empty, STOP and point the user at the plugin root's `references/instance-config.md`. Never guess a field ID: writing a composed blueprint into the wrong custom field is silent and hard to undo.

- Seller context source: Brand Kit OS brand kit (canonical) if connected, else the CRM's own context center, else a company-context document the user names.
- CRM: `{CRM_PROVIDER}`. Blueprint field `{APOLLO_CF_CONTACT_BLUEPRINT}`, opener field `{APOLLO_CF_CONTACT_OPENER}`; write via the CRM's contact-update call using typed custom fields.
- Field prefix: `{INSTANCE_FIELD_PREFIX}` — the deployment's shorthand, used in field labels and merge tokens. The blueprint merge token is `{{contact.<prefix> Blueprint}}` and the opener is `{{contact.<prefix> Opener}}`, with `<prefix>` resolved from that key.
- Field provenance map: `references/field-provenance.md`. That file is a per-deployment artifact — rebuild it from the CRM's field inventory during provisioning.

## Step 1: Field completeness gate (MANDATORY before composing)

Blueprints synthesized from blank inputs fabricate or generalize; both are fatal to a show-don't-tell motion. So verify inputs first.

Workflows and enrichment jobs are usually invisible to CRM APIs. Never ask "did the workflow run"; instead check whether the OUTPUT field on the record is populated. Pull the full contact record, then either run `scripts/field_gate.py <record.json> --motion <funding|hiring>` (deterministic, loggable) or check manually against references/field-provenance.md.

Gate rules: account system enrichment complete (funding, dept sizes, technologies) AND LinkedIn Profile Summary present AND at least one of {Research Company Profile, posts digest}. Hiring motion additionally requires GTM Jobs w/ URL, JD Summary, and Role Archetypes on the account. Never compose from fewer than three hard facts.

On FAIL, remediate by populator before composing (paths in field-provenance.md): workflow fields → re-add to trigger list and re-check; Claude pipeline fields → run the pipeline; system enrichment → enrich the org. Remediation that spends credits (org enrichment, people match) is confirmed with the user first, costed per the plugin root's references/apollo-credit-costs.md. Log gate results to the audit log.

## Step 2: Gather context

Seller side: load positioning, offer, and voice from the configured context source; the blueprint proposes THEIR delivery in THEIR voice. Target side, in priority order: Research Company Profile (richest: cited recent developments and pain points), system enrichment fields, CB Insights when connected (funding stage and round with named lead investors for opener credibility, commercial maturity 1-5 to calibrate the plan's ambition, Mosaic score, competitors for positioning lines, recent news for recency hooks), JD summaries (hiring motion), posts digests (also for voice-matching the recipient's own language), website scrape as fallback. See references/field-provenance.md for the field dictionary including CBI field semantics.

**Preflight the SELLER source before reading the target.** The context source can be stale
or self-contradicting, and a seller-side error is worse than a target-side one: it goes into
every blueprint rather than one. Check that the brand's description, mission, and product
list describe the same business, and that the stated ICP matches who is actually being
composed for. On a mismatch, STOP and ask which is current rather than picking. Observed
2026-09-07: a brand kit's description said web development agency while its products
described an AI implementation retainer, and composing from the description would have
offered the wrong service to every recipient. Prefer the product list and mission over a
name or description field, which are the ones that go stale first, and say which you used.

**Pull the target's open job postings on every account, whatever the motion.** They are the
highest-yield single source in this engine. One posting returned the tool stack, the
reporting line, the role's KPI, and a buying signal. Read every role, not only the GTM ones.
The stack it names is the A11 fact that Step 4's composition rule requires, and it is
quotable because it is the company's own words. Zero postings is itself a finding: record
it, and read it alongside the headcount trend before assuming budget or new headcount. The
source order for a stack is in the plugin root's
[references/scraping-playbook.md](../../references/scraping-playbook.md).

## Step 3: Classify the GTM motion

Decide by observable signals, in this order: (1) B2C check: consumer sellers get no cold-outbound blueprint, propose channel framings or flag to the human. (2) PLG/dev-first: self-serve, open source, docs-heavy. (3) Enterprise sales-led: book-a-call CTA, high ACV, compliance buyers. (4) Founder-led early: <20 employees, no sales function. (5) Channel/partner-led: resellers, marketplaces, partner nav. (6) Regulated vertical: healthcare/finance/defense/gov buyers. (7) None fits cleanly: do NOT force the nearest preset — compose a custom motion aligned to the framework (the Custom motion section in references/motion-templates.md walks the four questions that build one). Multi-model companies get one blueprint per distribution model, matched to each contact's role.

**A contact who fails one motion has not failed all of them.** Motion validation is a sweep, not a first-match test: when a contact does not fit the motion you reached for, check them against every remaining one before setting them aside, and record which ones you checked and why each failed. Two different things can fail and they have different remedies — the ACCOUNT gates (does the company qualify for this motion at all) and the PERSONA fit (is this the right person inside a company that does qualify). A contact can be the perfect persona at a company that fails the account gates, in which case no amount of fixing the contact helps; a company can qualify while the contact is the wrong role, in which case the right person may already be in the CRM. Dismissing on the first failure throws away both. Write the sweep down: "checked against all five, fits none, here is the closest and what blocks it" is a reusable answer, and "not a fit" is not.

**When a job description exists, audit it — always, not when convenient.** The JD is the primary evidence for both halves of the check: it names the role, its seniority, the tools, and often the reporting line, which is what tells you which persona actually owns the req and therefore which motion the contact belongs in. Running persona validation without reading an available JD is guessing with the answer sitting on the page. So whenever a posting is on file, scrape it, audit the role and its reporting line against the persona under consideration, and **persist the full JD as a dated reference document**, not only as a summary field. Summaries are lossy in exactly the way that matters here: the reporting line, the seniority signals, and the tool list are the first things a summary drops, and they are the three things a re-check needs. A stored JD is also the only way to tell later whether a req changed or was quietly refilled.

The five presets are options, not a closed list, and the motion is the operator's call, not an automated verdict. Present the recommended classification with its evidence — the candidate classifications when signals conflict (a company could plausibly be two motions), or the custom path when the company fits none rather than defaulting to the closest label — and proceed to Step 4 only on the operator's selection. Do not switch the chosen motion silently once it is set. A blueprint built on the wrong motion reads templated to the one person who knows better, the recipient.

**How that gate behaves in the batch mode.** Field-pipeline runs compose across many contacts, and blocking on a selection for every one of them would either stall the run or push the agent into treating its own recommendation as the operator's answer, which removes the gate while appearing to keep it. So the gate fires selectively there: a company whose signals point cleanly at one preset proceeds on the recommendation, and every company whose signals conflict or that fits no preset is held OUT of the batch and surfaced as a single decision list for the operator to resolve before those blueprints are composed. Record the motion chosen for every record either way, so the quality gate below checks motion assignment and not only prose. Ad hoc and client provisioning modes are one company at a time; there the selection is always explicit.

## Step 4: Compose against the motion template

Read references/motion-templates.md for the five templates and the custom-motion builder for a company none of them fit, the exact output format (hyphen-bullet week lines, closer line, intro line lives in the email template not the field), and the composition rules: cite at least one real stack tool and one hard number, name their actual buyer, no flattery, no fabrication, falsifiability test. A custom motion follows the same format and the same rules; it is a different emphasis, not a lower standard.

**Only quote a fact recorded as `verified`.** The required real stack tool and hard number must come from a primary source, which in practice means the company's own site, filing, or job description. An enrichment vendor's estimate sizes the account and routes it; it does not go in the field. Inferred technographics never do. The falsifiability test does not catch this class of error, because a number that came from a tool reads exactly like a number that came from research.

## Step 5: Write back

Apollo: contacts_update with typed_custom_fields; verify persistence in the response. HubSpot: multi-line contact property. Clay: add-data-points column. No CRM: markdown/PDF proposal. Multi-line rendering must be verified with ONE contact's email preview before any batch write; HTML emails sometimes collapse line breaks.

**Write back what the run learned, not only what it composed. Field pipeline and client provisioning modes only.** Ad hoc proposal mode has no CRM record to write to, so it has no write queue: surface what the run learned in the single end-of-run list and stop there. A run gathers far more than
it spends: the A11 tool stack, the open roles, the aliases, the funding detail. Composing
uses one or two of those and the rest evaporates unless this step writes them. Do it here,
while the data is in hand, because during the run it costs nothing and a week later the same
field costs a full re-research.

Build the ledger with the plugin root's `scripts/gap_ledger.py`, one record at a time, and
follow it: write the write queue without asking, and surface the propose queue ONCE at the
end as a list rather than as a series of interruptions. The gate is in the plugin root's
[references/gap-ledger.md](../../references/gap-ledger.md) and it is not negotiable per run:
a verified fact fills an empty or stale machine field automatically, an estimate fills only
a field declared to accept one, an inferred fact is never written at all, and a value a
person entered is never overwritten however confident the run is. A blank a person left is
a gap, not a decision.

Record what was filled and what was declined in the run's Notes. A run that closes nothing
and says nothing is the failure this step exists to end.

## Client provisioning mode

1. Inventory the client's company and person fields via their connector's field-listing tool; rebuild references/field-provenance.md for their instance (populator + trigger + remediation per field).
2. Create the Blueprint field with their prefix (field definitions usually require UI creation; provide exact name, multi-line text type, modality).
3. Map their context source (Brand Kit OS or equivalent) as seller-side input.
4. Pilot on 3 contacts, human-review against the falsifiability test, then batch.

## Data handling and disclosure

Check the do-not-contact/exclusion list before composing for any contact; a blueprint for an excluded contact is wasted work and a governance defect. Use only public professional data (CRM enrichment, public posts, public web); prospect data stays inside the CRM and this workspace, never in third-party tools outside the configured stack. Disclosure is strategy here, not fine print: the outreach copy itself reveals that an AI engine sourced and researched the recipient (the engine IS the product), so keep that reveal intact in any sequence that carries these fields. In client provisioning mode, set the client's disclosure stance explicitly during setup; do not default to silence about AI involvement.

## Quality gate

Blueprints feed outreach a human sends. Before any batch write: sample-review 3 outputs, verify every cited fact against source data, confirm the human approves the template voice, and check motion assignment — every record in the batch carries a recorded `selected_motion` (the preset name, or `Custom motion: <phrase>`), no record was composed while its motion was still unresolved, and each sampled blueprint's week lines and closer match the motion it is recorded under. A blueprint composed against a motion nobody chose is the defect this gate exists to catch, and it does not announce itself in the prose. Log defects and gate results to the audit log; template changes are versioned in the changelog.
