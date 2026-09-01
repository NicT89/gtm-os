# Environment Setup Module

The single canonical procedure for getting a tool from "the user has it" to "the
engine can use it." Every skill routes here when a connector it needs is missing,
unauthenticated, or unconfigured. The `environment-setup` skill is the invocable
front door; this file is the per-connector detail it reads.

## The rule that governs this whole document

**Not set up does not mean not owned.**

The overwhelmingly common case is that the user already has the tool. They have an
Apollo seat, an Airtable workspace, an Apify account, a Firecrawl key. What they do
not have is that tool *shaped for this engine*: the custom fields do not exist yet,
the base has the wrong schema, the MCP server was never added, or the IDs were never
written into `instance-config.json`.

So the first move is never "go sign up." The first move is **probe, then place them
on the ladder below.** Recommending a signup to someone who already pays for the tool
is the failure mode this module exists to prevent, and it costs trust the first time
it happens.

## The five-state ladder

Every connector sits in exactly one of these states. Diagnose before you act.

| State | Meaning | What is missing |
|---|---|---|
| **S0 — Absent** | No account with the vendor at all | The account |
| **S1 — Owned, unreachable** | Account exists; Claude cannot call it | MCP server, or auth on it |
| **S2 — Reachable, unshaped** | Claude can call it; the GTM OS objects do not exist | Custom fields, base schema, lists |
| **S3 — Shaped, unrecorded** | Objects exist; the engine does not know their IDs | Keys in `instance-config.json` |
| **S4 — Wired** | Recorded and proven by a live call | Nothing |

Only S0 needs a signup. **S1 through S3 are the normal case and none of them require
buying anything.** A user who says "I don't have Apollo set up" is almost always at
S1, S2, or S3.

### Probing, in order

Run these before asking the user anything. They are cheap, read-only, and they
answer the question faster than a conversation does.

1. **Is the MCP server present?** List the available tools. If `apollo_*` /
   `airtable_*` / `firecrawl_*` / Apify tools appear, the user is at S2 or better.
   If the tools are absent, that is S0 or S1, and you cannot yet tell which.
2. **Does it authenticate?** Make the cheapest read-only call the connector offers
   (below, per tool). A 401/403 is S1 with broken auth. A clean read is S2 or better.
3. **Are the GTM OS objects there?** Read the schema (Apollo custom fields, Airtable
   base tables). Missing objects is S2.
4. **Is `instance-config.json` filled for this connector?** Run
   `python3 scripts/validate_instance_config.py`. Empty or missing required keys for
   a connector that is otherwise fine is S3.
5. **Only if steps 1 and 2 both fail:** ask the user, in these words or close to
   them: *"Do you already have a <tool> account? If so this is a connection step,
   not a signup."* Do not narrate a signup flow until they say no.

**Never guess a substitute for a missing connector.** Each skill degrades explicitly
when one is absent; an improvised replacement turns a stated degradation into a
silent wrong answer.

---

## Apollo (required — CRM, signals, enrichment, sequences)

**Cheapest probe:** `apollo_contacts_search` with a tiny page size. Search is free;
it costs no credits and it returns `typed_custom_fields` on each contact, which is
also how you read custom field IDs.

| State | How you know | The move |
|---|---|---|
| S0 | No account, user confirms | Sign up at apollo.io. A paid plan is needed for the API and for reveals. |
| S1 | No `apollo_*` tools, or calls 401 | Add the Apollo MCP server and authenticate it. Confirm the plan includes API access. |
| S2 | Calls work; `typed_custom_fields` lacks the engine's fields | Create the custom fields (below). |
| S3 | Fields exist; `APOLLO_CF_*` keys empty | Read the IDs and write them into `instance-config.json`. |

**S2, the custom fields.** Apollo's API cannot create field *definitions*, only
populate them. The human creates them in the Apollo UI; the AI then resolves their
IDs. Which fields, their modality (contact vs account), and their types are listed in
`skills/gtm-blueprint/references/field-provenance.md`. The two the engine *writes*
are the opener and the blueprint, both multi-line text; the rest it reads. Field
labels use your `INSTANCE_FIELD_PREFIX`, so pick that prefix before creating any of
them: renaming later means editing every sequence that references the merge token.

**S2, the lists.** `APOLLO_LIST_*` keys are list **names**, not IDs. Create them in
Apollo first. The enrichment list name must match exactly what your profile
enrichment workflow watches, or the workflow silently never fires.

**S3, reading the IDs.** Custom field IDs are 24-character hex strings. Create the
field, fetch any record that carries it, and read the key out of
`typed_custom_fields`.

**Do not** create, rename, or delete anything in Apollo that a human manages.
Everything the engine creates carries "[Claude]" in its name; that convention is what
makes the boundary auditable.

---

## Airtable (required — the posts base, and optionally the Research Vault)

Two independent bases. A user can be at S4 on one and S0 on the other, and the
skills degrade separately, so diagnose them separately.

**Cheapest probe:** list bases, then read the target base's schema.

### The posts base

| State | How you know | The move |
|---|---|---|
| S0/S1 | No `airtable_*` tools, or no workspace | Add the Airtable MCP server; create a free workspace if genuinely absent. |
| S2 | Base missing, or its tables do not match | Build it per [airtable-posts-base.md](airtable-posts-base.md). |
| S3 | Base correct; `AIRTABLE_*` keys empty | Read table and field IDs and record them. |

Build the base **empty**, not from an Airtable template: templates ship default
tables you would only have to delete. Build the parent tables (`Contacts`, `Company`)
first, because link fields cannot be created until both sides exist. Field *names*
are yours to choose; the skill addresses everything by ID.

The token needs `data.records:read`, `data.records:write`, and `schema.bases:read`
on the base.

### The Research Vault (optional; skills degrade to report-only without it)

One base per instance, four tables plus a Field Keys reference table, schema in
[research-vault.md](research-vault.md). If the six `AIRTABLE_*VAULT*` keys are empty,
the Vault write steps in `company-deep-research`, `gap-closer`, `event-attribution`,
and the fan-out harness all skip cleanly and say so. They never write into the posts
base as a substitute, and they never invent a base.

Read the IDs the same way: base ID from the URL (`airtable.com/appXXXXXXXXXXXXXX/...`),
table and field IDs from `airtable.com/appXXXXXXXXXXXXXX/api/docs` or the Metadata API.

---

## Apify (required for post scraping)

**Cheapest probe:** list actors, or fetch the account record. Both are free; actor
*runs* are not.

| State | How you know | The move |
|---|---|---|
| S0 | No account | Sign up at apify.com. The free tier has monthly credit; scraping at volume needs a paid plan. |
| S1 | No Apify tools, or auth fails | Add the Apify MCP server and authenticate with an API token. |
| S2 | Connected; the posts actor is not available to the account | Confirm access to `{APIFY_POSTS_ACTOR}` (default `harvestapi/linkedin-profile-posts`). |
| S3 | `APIFY_POSTS_ACTOR` empty or pointing at a substituted actor | Record it. A substituted actor means `scrape-linkedin-posts` Step 4 parsing must be re-matched to its output shape. |

Actor runs are metered per result. Any run that spends is stated to the human before
it starts, per [run-manifest.md](run-manifest.md).

---

## Firecrawl (required — the default web extractor)

**Cheapest probe:** scrape a single well-known static page and check for non-empty
markdown.

| State | How you know | The move |
|---|---|---|
| S0 | No account | Sign up at firecrawl.dev; the free tier covers evaluation. |
| S1 | No `firecrawl_*` tools, or 401 | Add the Firecrawl MCP server and authenticate. |
| S4 | A test scrape returns markdown | Done. Firecrawl needs no instance-config keys. |

Firecrawl is not optional in practice even though it needs no config: ATS pages,
app-shell marketing sites, and docs portals are client-side rendered, so a plain
fetch returns metadata and zero content. Without Firecrawl, an empty extraction means
"not extracted," never "not present," and every skill that falls back must say so in
its report. See [scraping-playbook.md](scraping-playbook.md).

---

## Optional connectors

None of these block a run. Each skill states the degradation when one is absent.

| Connector | What it adds | Absent behavior |
|---|---|---|
| **CB Insights** | Funding stage, named investors, commercial maturity | Those three `APOLLO_CF_ACCOUNT_CBI_*` / `NAMED_INVESTORS` keys stay empty; the validator permits it. Funding comes from primary sources instead. |
| **Brand Kit OS** | Structured seller-side brand voice, positioning, audience | `gtm-blueprint` falls back to the CRM context center or a document you name. |
| **Google Drive / Box / OneDrive** | File home for briefs, reports, audit logs | A local folder works identically. Choose one and say which. |
| **A warehouse (BigQuery, Supabase)** | The data spine layer in `gtm-architecture-composer` | The architecture proposal names the gap instead of designing around it. |

Coverage status and the MCP-vs-API decision for any tool a client already runs is in
[mcp-coverage-map.md](mcp-coverage-map.md). Rows carry a verified date; re-verify any
row older than a quarter before citing it to a client.

---

## The platform capabilities, not vendor connectors

Two requirements that are not accounts and are easy to miss.

**Workflow tool (for `fanout-harness`).** `scripts/fanout_workflow.js` runs through
the host's multi-agent Workflow tool. If the session has no Workflow tool, the
fan-out cannot run; research the companies sequentially through
`company-deep-research` instead and say that is what you are doing. Do not simulate
a fan-out with a loop of subagents that skip the writer stage's provenance
validation.

**Python report environment (for rendered PDFs).** `scripts/render_report.py` needs
Python 3.10+ plus `reportlab`, `matplotlib`, and `pillow`:

```bash
pip install reportlab matplotlib pillow
python3 scripts/render_report.py --selftest
```

The selftest renders a one-page sample exercising every block and chart type and
prints a JSON result line. If your Python is externally managed, install into a
virtualenv rather than forcing a system-wide install. This is needed only for PDF
deliverables (`jd-intake` output, run reports, architecture proposals), not for the
CRM-side skills.

**Headless and scheduled runs.** Interactively-authenticated MCP connectors may be
unavailable in a scheduled or headless run. A skill that hard-stops on a missing
connector will hard-stop there, which is correct behavior, but it is worth knowing
before you register a recurring run. Verify a connector survives a scheduled
invocation before you depend on it for one.

---

## The placeholders the repo ships with

`instance-config.example.json` ships two kinds of value, and they fail in opposite
directions.

**Empty placeholders** (`""`) are loud. A skill that needs one stops and says so, and
the validator reports it as required-but-empty. These get fixed because they hurt.

**Non-empty shipped defaults** are quiet, and they are the ones that bite. Copying the
example inherits them wholesale, they work, nothing fails, and nobody ever decides
whether they are right for this workspace. Today there are three:

| Key | Ships as | When it is wrong |
|---|---|---|
| `CRM_PROVIDER` | `apollo` | Any deployment on a different CRM. The field-writing calls are named for Apollo, so this is a real fork, not a label. |
| `APIFY_POSTS_ACTOR` | `harvestapi/linkedin-profile-posts` | You have standardized on a different actor. Substituting one means `scrape-linkedin-posts` Step 4's parsing must be re-matched to its output shape. |
| `SCRAPE_ROSTER_ARTIFACT` | `scrape-roster.md` | The name collides with something in your artifact home. |

Run the status report to see all three states at once:

```bash
python3 scripts/setup_status.py
```

It classifies every key as **set** (chosen: non-empty and different from what ships),
**default** (non-empty but still byte-identical to the example: works, never decided),
or **unset**, groups them by connector, and says what each gap blocks and how to close
it. Exit 0 means runnable, 1 means a required key is still open. Add `--json` to log
the verdict to the audit trail.

Three verdicts, and the middle one is the point:

- `INCOMPLETE` — a required key is unset. Something will hard-stop.
- `READY_WITH_DEFAULTS` — runnable, but values were inherited rather than chosen.
  Walk the user through each one and get a yes or a change. A confirmed default is
  finished; an unexamined one is a latent surprise.
- `READY` — every key holds a deliberate value.

Do not treat `READY_WITH_DEFAULTS` as done and move on. Reaching `READY` takes one
question per key, and it is the difference between a deployment that was configured
and one that was merely copied.

## Finishing: record, validate, prove

Setup is not complete at S3. It completes at S4, and S4 requires a live call.

1. **Record.** Every resolved value goes into `instance-config.json` at the plugin
   root, never into a SKILL.md. That file is gitignored because it describes one
   workspace, not the template. Adding a value the schema does not know about means
   adding the key to `instance-config.example.json` in the same change; see
   [instance-config.md](instance-config.md).

2. **Validate the shape.**

   ```bash
   python3 scripts/validate_instance_config.py
   ```

   It checks that every `{KEY}` the skills reference exists, that your file defines
   exactly the schema's keys, and that values look like the right kind of ID. It
   verifies shape, not existence: it cannot tell you an ID is real.

3. **Prove it with one target.** Run `scrape-linkedin-posts` against a single named
   person. Confirm a `Contacts` row is created with the bare name, `Person Post` rows
   carry the bare `Name` and a `YYYY-MM-DD` `Posted Date`, comment rows link to
   exactly one post row, and the CRM push lands in the intended field with nothing
   else on the record changed. Then run it a second time against the same target: no
   duplicate parent row, no duplicate post rows.

   A wrong field ID found on target one is cheap. Found on target fifty it is not.

## What never happens during setup

- No credential is ever written into this repo, a SKILL.md, or a run artifact. `.env`
  and `.env.*` are gitignored; the audit is
  `git log --all -p | grep -iE 'APOLLO|APIFY|API_KEY'` and it must come back empty.
- No resolved instance value flows back to the public repo. Porting a skill
  improvement from a local copy means re-tokenizing every ID to a `{KEY}` first.
- No skill guesses an ID, a base, or a field. Missing config is a stop, and the stop
  routes here.
- No connector is declared working on the strength of its tools appearing in the
  tool list. S1 and S4 look identical until something is actually called.
