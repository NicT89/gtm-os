# GTM OS Setup Sequence

How a new user (or the AI operating for them) turns this repo into a running instance on
THEIR accounts. The repo ships the framework, blueprint, and playbook; everything
account-specific is a value resolved here, once, on first run. The framework is identical
across instances; only the underlying data differs.

Run the steps in order and confirm each one with the human before moving on.

**The per-connector procedure lives in one place:
[references/environment-setup.md](references/environment-setup.md).** This file is the
sequence; that file is the detail for each tool, and the `environment-setup` skill is
the invocable front door that runs it (`"set up my environment"`, `"set up Apollo"`,
`"connect Airtable"`). Any skill that stops because a connector is missing routes there
too, so there is exactly one setup procedure rather than a version of it per skill.

**Before anything else, read the rule that governs the whole module: not set up does not
mean not owned.** Most users already have Apollo, Airtable, Apify, and Firecrawl. What
they do not have is those tools *shaped for this engine* — the custom fields do not
exist, the base has the wrong schema, the MCP server was never added, or the IDs were
never recorded. Diagnose which of those it is before suggesting anyone sign up for
anything.

## The variable rule (load-bearing)

Skills in this repo reference deployment values as `{KEY}` tokens — CRM custom field IDs,
Airtable base/table/field IDs, list names, your field prefix. **The repo never contains a
resolved value for any specific instance.** Resolved values live in one local,
git-ignored file:

```
instance-config.json          (repo root; gitignored; created in Step 3)
```

`instance-config.example.json` is the template, `references/instance-config.md` explains
every key and where to find its value, and `scripts/validate_instance_config.py` checks
your file before you rely on it.

**Local vs repo.** Operators with a private fork or local branch may keep resolved values
in their local copies for convenience; those values must never flow back to the public
repo. When porting a skill improvement from a local copy into this repo, re-tokenize
every instance value before committing — every ID becomes a `{KEY}`, and any key that
does not exist yet gets added to `instance-config.example.json` in the same change. CI
cannot catch a leaked ID, so this is a review gate: the PR checklist in
[MAINTAINING.md](MAINTAINING.md) includes "no resolved instance values."

## Step 1: Diagnose the connectors

Do not ask the user what they have. Probe, then place each connector on the five-state
ladder from [references/environment-setup.md](references/environment-setup.md):

| State | Meaning |
|---|---|
| **S0** | No account with the vendor |
| **S1** | Account exists; Claude cannot reach it (no MCP server, or auth broken) |
| **S2** | Reachable; the GTM OS objects do not exist yet (custom fields, base schema, lists) |
| **S3** | Objects exist; their IDs are not in `instance-config.json` |
| **S4** | Recorded and proven by a live call |

**Only S0 needs a signup. S1 through S3 are the normal case and none of them cost
money.** The probes — list the tools, make the cheapest read-only call, read the schema,
run the config validator — are all free and answer the question faster than asking does.

In scope:

- **Apollo** (required) — signal source, CRM, enrichment, sequences, analytics.
- **Apify** (required for post scraping) — runs the LinkedIn posts actor.
- **Airtable** (required for the posts base; optional for the Research Vault) — the
  posts archive and the research data spine.
- **Firecrawl** (required) — the default extractor for all web content, per
  [references/scraping-playbook.md](references/scraping-playbook.md).
- **CB Insights, Brand Kit OS, Google Drive, a warehouse** (all optional) — each skill
  states its degradation when one is absent.

Report the ladder to the user before changing anything, saying which gaps actually block
a run and which do not. Do not improvise a substitute for a missing connector: each skill
degrades explicitly when one is absent, and a guessed substitute turns that explicit
degradation into a silent wrong answer.

Note that interactively-authenticated connectors may be unavailable in headless or
scheduled runs. A skill that hard-stops on a missing connector will hard-stop there,
which is correct, but worth knowing before you schedule anything.

## Step 2: Build the Airtable posts base

The full schema — five tables, build order, field types, the primary `Name` rule, the
fields deliberately not to create, and the verification checklist — is in
[references/airtable-posts-base.md](references/airtable-posts-base.md). That file is the
single canonical copy; follow it rather than any summary.

Two things to know before you start: build the parent tables first (link fields cannot be
created until both sides exist), and create the base empty rather than from an Airtable
template, which ships default tables you would only have to delete.

## Step 2b: Build the Research Vault base (optional)

The Vault is the persistent research data spine: every fact any skill captures lands
there with full provenance, so re-running research is a mechanical diff rather than a
fresh read. Schema (four tables plus a Field Keys reference table, and the write rules
every skill obeys) is in [references/research-vault.md](references/research-vault.md).

It is a **separate base** from the posts base, and it is optional. Skip it and
`company-deep-research`, `gap-closer`, `event-attribution`, and the fan-out harness all
degrade to report-only: full reports, no persisted facts, and each says so. They never
write into the posts base instead.

Skip it only deliberately, though. Without the Vault there is no baseline, so the second
research run on a company cannot tell you what changed since the first, which is most of
what makes the second run worth paying for.

## Step 3: Resolve the variables into `instance-config.json`

```bash
cp instance-config.example.json instance-config.json
```

Then fill it in:

1. **Airtable IDs.** Call the Airtable schema tools to read back the base ID, all five
   table IDs, and every field ID, and write them into the `AIRTABLE_*` keys. If you
   built the Vault in Step 2b, its base and five table IDs go into the
   `AIRTABLE_VAULT_BASE_ID` and `AIRTABLE_TBL_VAULT_*` keys; leave all six empty if you
   did not. The two `*_TRACKING` field keys are likewise optional.
2. **CRM custom fields.** Apollo custom field definitions cannot be created via API: the
   human creates them in the Apollo UI (multi-line text, contact or account modality as
   listed in `skills/gtm-blueprint/references/field-provenance.md`), then the AI resolves
   their IDs and writes them into the `APOLLO_CF_*` keys.
3. **Field prefix.** `INSTANCE_FIELD_PREFIX` is the short prefix on the CRM fields this
   engine creates. It becomes the field labels — `<prefix> Opener` and `<prefix>
   Blueprint` — and the merge tokens that reference them. Pick it once; renaming later
   means editing every sequence.
4. **List names and everything else.** Per the key-by-key reference in
   [references/instance-config.md](references/instance-config.md).

Validate before going further:

```bash
python3 scripts/validate_instance_config.py
```

It checks that every `{KEY}` the skills reference exists, that your file defines exactly
the schema's keys, and that the values look like the right kind of ID. It verifies
*shape*, not existence — it cannot tell you an ID is real. That is what Step 4 is for.

## Step 4: Verify with a dry run

Run `scrape-linkedin-posts` against ONE target the user names. Confirm:

- a `Contacts` row is created with the bare person name;
- `Person Post` rows carry the bare `Name` (no date suffix) and a `Posted Date` of the
  form `YYYY-MM-DD`;
- comment rows link to exactly one post row;
- the CRM push lands in the intended custom field and nothing else on the record changed.

Run it a second time against the same target: it must create no duplicate parent row and
no duplicate post rows. Fix any resolution error before any batch use — a wrong field ID
found on target one is cheap, and found on target fifty is not.

## Step 5: Report environment for rendered deliverables

Full detail, including the headless-run caveat, is in
[references/environment-setup.md](references/environment-setup.md#the-platform-capabilities-not-vendor-connectors).
`scripts/render_report.py` needs Python 3.10+ plus `reportlab`, `matplotlib`, and
`pillow`:

```bash
pip install reportlab matplotlib pillow
python3 scripts/render_report.py --selftest
```

The selftest renders a one-page sample exercising every block and chart type and prints a
JSON result line. If your Python is externally managed, install into a virtualenv rather
than forcing a system-wide install. This step is optional: it is only needed for PDF
deliverables (`jd-intake` output, run reports), not for the CRM-side skills.

## Step 6: File home and cadence

Choose the artifact home (a local folder Claude structures, or Google Drive with the same
structure) per the [README](README.md), then register the recurring runs you want: the
weekly signal scan, and the scheduled posts refresh.

Before you schedule the posts refresh, set the `Tracking` field on the Contacts and
Company rows you actually want re-scraped. A scheduled run touches only `active` rows;
that field is the off switch, and without it every row is in scope every week. See
[references/airtable-posts-base.md](references/airtable-posts-base.md#the-tracking-field).

Multi-step runs also maintain a manifest so a dropped connector or a dead session is a
resume rather than a restart, and so spend is stated before it happens. That convention
is in [references/run-manifest.md](references/run-manifest.md); it needs no setup beyond
having chosen a working folder here.

## What stays local vs what flows back

- **Local, never committed:** `instance-config.json`, audit logs, run manifests, the
  scrape roster, client data, rendered reports, and everything in the Research Vault.
- **Flows back to the repo, as PRs with tokenized values:** skill improvements, new dated
  entries for `references/dependency-observations.md`, coverage updates for
  `references/mcp-coverage-map.md`.
