# GTM OS Setup Sequence

How a new user (or the AI operating for them) turns this repo into a running instance on
THEIR accounts. The repo ships the framework, blueprint, and playbook; everything
account-specific is a value resolved here, once, on first run. The framework is identical
across instances; only the underlying data differs.

Run the steps in order and confirm each one with the human before moving on.

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

## Step 1: Connectors

Confirm these MCP connectors are present and authenticated:

- **Apollo** (required) — signal source, CRM, enrichment, sequences, analytics.
- **Apify** (required for post scraping) — runs the LinkedIn posts actor.
- **Airtable** (required for the posts base) — the posts archive.
- **Firecrawl** (required) — the default extractor for all web content, per
  [references/scraping-playbook.md](references/scraping-playbook.md).
- **Google Drive** (optional) — file home; a local folder works instead.

If one is missing, stop and tell the user which and why. Do not improvise a substitute:
each skill degrades explicitly when a connector is absent, and a guessed substitute turns
that explicit degradation into a silent wrong answer.

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

## Step 3: Resolve the variables into `instance-config.json`

```bash
cp instance-config.example.json instance-config.json
```

Then fill it in:

1. **Airtable IDs.** Call the Airtable schema tools to read back the base ID, all five
   table IDs, and every field ID, and write them into the `AIRTABLE_*` keys.
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

## What stays local vs what flows back

- **Local, never committed:** `instance-config.json`, audit logs, run manifests, client
  data, rendered reports.
- **Flows back to the repo, as PRs with tokenized values:** skill improvements, new dated
  entries for `references/dependency-observations.md`, coverage updates for
  `references/mcp-coverage-map.md`.
