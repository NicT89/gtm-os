---
name: gtm-blueprint
description: Generate a customized 30-day GTM blueprint for any company, for outreach personalization fields or ad hoc proposals. Use when the user says "create a GTM blueprint", "run gtm-blueprint", "blueprint proposal for [company]", "populate the blueprint field", "write the 30-day plan for [company]", "set up blueprint enrichment for [client]", or whenever composing the `<prefix> Blueprint` field or any equivalent per-company plan field in a CRM. Classifies the company's GTM motion (PLG, enterprise, founder-led, channel, regulated vertical), verifies enrichment-field completeness with a hard gate, composes from real data against motion-specific templates, and writes back to the connected CRM or delivers in chat.
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

## Step 3: Classify the GTM motion

Decide by observable signals, in this order: (1) B2C check: consumer sellers get no cold-outbound blueprint, propose channel framings or flag to the human. (2) PLG/dev-first: self-serve, open source, docs-heavy. (3) Enterprise sales-led: book-a-call CTA, high ACV, compliance buyers. (4) Founder-led early: <20 employees, no sales function. (5) Channel/partner-led: resellers, marketplaces, partner nav. (6) Regulated vertical: healthcare/finance/defense/gov buyers. Multi-model companies get one blueprint per distribution model, matched to each contact's role.

When signals conflict or classification is uncertain (a company could plausibly be two motions), do not guess: present both candidate classifications to the human with the evidence for each and let them pick. A blueprint built on the wrong motion reads templated to the one person who knows better, the recipient.

## Step 4: Compose against the motion template

Read references/motion-templates.md for the five templates, the exact output format (hyphen-bullet week lines, closer line, intro line lives in the email template not the field), and the composition rules: cite at least one real stack tool and one hard number, name their actual buyer, no flattery, no fabrication, falsifiability test.

## Step 5: Write back

Apollo: contacts_update with typed_custom_fields; verify persistence in the response. HubSpot: multi-line contact property. Clay: add-data-points column. No CRM: markdown/PDF proposal. Multi-line rendering must be verified with ONE contact's email preview before any batch write; HTML emails sometimes collapse line breaks.

## Client provisioning mode

1. Inventory the client's company and person fields via their connector's field-listing tool; rebuild references/field-provenance.md for their instance (populator + trigger + remediation per field).
2. Create the Blueprint field with their prefix (field definitions usually require UI creation; provide exact name, multi-line text type, modality).
3. Map their context source (Brand Kit OS or equivalent) as seller-side input.
4. Pilot on 3 contacts, human-review against the falsifiability test, then batch.

## Data handling and disclosure

Check the do-not-contact/exclusion list before composing for any contact; a blueprint for an excluded contact is wasted work and a governance defect. Use only public professional data (CRM enrichment, public posts, public web); prospect data stays inside the CRM and this workspace, never in third-party tools outside the configured stack. Disclosure is strategy here, not fine print: the outreach copy itself reveals that an AI engine sourced and researched the recipient (the engine IS the product), so keep that reveal intact in any sequence that carries these fields. In client provisioning mode, set the client's disclosure stance explicitly during setup; do not default to silence about AI involvement.

## Quality gate

Blueprints feed outreach a human sends. Before any batch write: sample-review 3 outputs, verify every cited fact against source data, confirm the human approves the template voice. Log defects and gate results to the audit log; template changes are versioned in the changelog.
