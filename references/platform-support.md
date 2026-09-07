# Platform support

You choose your stack. This file says how well this engine speaks each platform, so you
know what you are getting before you wire anything.

There are **two different questions** here, and conflating them is how a client ends up
disappointed:

1. *Does the vendor publish an MCP server?* — that is `references/mcp-coverage-map.md`,
   a market fact that changes monthly.
2. *Has GTM OS been built against that platform's semantics?* — that is this file, a fact
   about **our** work, and it is the one that determines quality.

Salesforce is the clean illustration. It has an official, hosted MCP server, so the
coverage map's answer is yes. GTM OS has never been built against it: no field map, no
write path, no exercised run. The honest answer to "can I run this on Salesforce" is
therefore *"yes, generically, and it will be noticeably worse than Apollo"* — not a flat
yes and not a flat no.

## The three tiers

| Tier | What it means | What you get |
|---|---|---|
| **Native** | Skills are written against this platform's actual MCP semantics — its calls, its ID shapes, its field types — and a deployment has run it end to end. | The full motion. Deterministic field writes, verified persistence, documented failure modes. |
| **Generic** | The platform is reachable over MCP and the engine can read and write through it, but no platform-specific path was built. The skills' gates, composition rules, and audits all still apply. | The motion runs. You supply the field mapping yourself, writes are not verified the same way, and platform-specific failure modes are undocumented — nobody has hit them here yet. |
| **Not built** | No GTM OS path exists. The vendor may well have an excellent MCP server; we have not built against it. | The integration is yours to build, or move the data with n8n/API per the coverage map. Nothing here reads or writes it, so treat any skill's claims about it as unverified. |

**A generic platform is a real option, not a warning label.** Every gate, every
falsifiability test, every no-fabrication rule binds the same way regardless of tier. What
you lose is the accumulated platform knowledge: the silent failure modes, the exact input
keys, the field-type mismatches that only show up on the fiftieth record.

## Where each platform sits today

Tier is assigned on **evidence in this repository**, not on impressions. The evidence
column names what you can go read; `tests/test_platform_support.py` checks that the claim
still matches the repo.

### Native

| Platform | Role | Evidence in this repo |
|---|---|---|
| **Apollo** | CRM, signals, enrichment, sequences | Named calls (`apollo_contacts_update`, `typed_custom_fields`), 24-hex custom-field IDs in `instance-config.example.json`, `references/apollo-credit-costs.md`, per-field provenance in `skills/gtm-blueprint/references/field-provenance.md` |
| **Airtable** | Posts base, Research Vault | Field-level `AIRTABLE_FLD_*` keys for every column, schema in `references/airtable-posts-base.md`, `references/research-vault.md` |
| **Apify** | LinkedIn post and comment scraping | Named actor key, the exact input key (`targetUrls`) and its silent-failure mode, dataset field projection, in `skills/scrape-linkedin-posts/SKILL.md` |
| **Firecrawl** | Default web extractor | The extraction path and its scrape-cost note in `references/environment-setup.md` and `references/scraping-playbook.md` |

### Generic

| Platform | Role | What is and is not there |
|---|---|---|
| **HubSpot** | CRM | `gtm-blueprint` names the write target (a multi-line contact property). No field provenance map, no verified-persistence path, no credit model. |
| **Clay** | Enrichment / CRM-adjacent | `gtm-blueprint` names the write target (add-data-points column). Same gaps as HubSpot. |
| **CB Insights** | Funding, investors, commercial maturity | Optional. Field semantics documented; absent behavior defined — the keys stay empty and funding comes from primary sources. |
| **Brand Kit OS** | Seller-side voice and positioning | Optional. `gtm-blueprint` falls back to the CRM context center or a document you name. |
| **Google Drive / Box / OneDrive** | Artifact home | Optional, and a local folder is exactly equivalent. |
| **Supabase / BigQuery** | Warehouse spine | Optional. `gtm-architecture-composer` designs against it; absent, it names the gap instead. |

### Not built

**Salesforce, Zapier, n8n as a CRM, Metabase, NetSuite, Gainsight**, and anything else not
listed above. Several have first-rate MCP servers — see the coverage map. What is missing
is our side, and this file will keep saying so until that changes.

## What a skill must do about this

Any skill that touches a platform outside the Native tier says so **before** it acts, once,
in plain terms:

> Your CRM is HubSpot, which this engine supports generically rather than natively. The
> motion, gates, and audits are identical; what you lose is the verified field-write path
> and the documented failure modes we have for Apollo. You will map fields yourself, and
> a write that silently no-ops will not be caught for you.

Do not bury it, do not repeat it every step, and **do not talk anyone out of their stack.**
A person running HubSpot well is better served than one migrating to Apollo they do not
want. State the tier, state the specific thing they lose, continue.

Never imply a Generic platform is unsupported, and never imply it is equivalent to Native.
Both are false, and the second is the expensive one: it sets an expectation of
deterministic behavior that has not been built.

## Moving a platform between tiers

Generic becomes Native when all four are true, and not before:

1. The platform's own calls and ID shapes are named in the skills that write to it.
2. A field map exists for it, the way `field-provenance.md` exists for Apollo.
3. A deployment has run the motion end to end on it, and its failure modes are written
   down — including at least one that surprised somebody.
4. The row here moves in the same PR, with the evidence column filled in.

Promotion is not a judgment call about how good the vendor is. It is a claim about what
this repo contains, and `tests/test_platform_support.py` will fail if the claim outruns it.
