# Instance configuration

Every value that is specific to *your* workspace — CRM custom field IDs, Airtable
base and field IDs, list names, your field prefix — lives in one file:
`instance-config.json` at the plugin root. The skills never hardcode these; they
reference keys by name, like `{AIRTABLE_POSTS_BASE_ID}`, and resolve them from that
file at run time.

This is what makes the engine installable by anyone. It also means **a skill will
stop rather than guess** if a key it needs is missing — which is the correct
behavior, because the alternative is writing data into the wrong field or the wrong
Airtable base.

## Setup

```bash
cp instance-config.example.json instance-config.json
# fill in the values, then:
python3 scripts/validate_instance_config.py
```

`instance-config.json` is gitignored. It describes your workspace, not the
template — it must never be committed here.

## What each group of keys is, and where to find it

### `INSTANCE_*`

| Key | Value |
|---|---|
| `INSTANCE_NAME` | Your company or deployment name. Used in reports and audit logs. |
| `INSTANCE_FIELD_PREFIX` | Short prefix on the CRM fields this engine creates, e.g. `ACME`. It becomes the field labels (`ACME Blueprint`) and the merge tokens (`{{contact.ACME Blueprint}}`). Pick it once — renaming later means editing every sequence. |

### `CRM_PROVIDER`

`apollo` is the reference implementation. The skills' logic is provider-agnostic,
but the field-writing calls are named for Apollo; adapting to HubSpot or Clay means
changing those calls, not the gates or the composition rules.

### `APOLLO_CF_CONTACT_*` and `APOLLO_CF_ACCOUNT_*`

Custom field IDs, 24-character hex strings. These fields must be **created in the
CRM UI first** — the API cannot create field definitions, only populate them.

To find an ID: create the field, then fetch a record that has it and read the key
from the `typed_custom_fields` object. In Apollo, `apollo_contacts_search` returns
these on each contact.

Which fields to create, and their types, is in
`skills/gtm-blueprint/references/field-provenance.md`. The two the engine writes
are the opener and the blueprint (both multi-line text); the rest it reads.

Optional keys — leave empty if you do not use that connector, and the validator
will not complain: the CB Insights fields, Named Investors, Available GTM Roles,
LinkedIn Company Summary, Persona Intelligence, Has LinkedIn, Startup/SMB Fit.

### `APOLLO_LIST_*`

List **names**, not IDs — the engine routes records by adding them to named lists.
Create these in the CRM first. The enrichment list is the one your profile-enrichment
workflow triggers on, so its name must match what that workflow watches.

### `AIRTABLE_*`

Build the posts base first: `references/airtable-posts-base.md` has the full schema,
the build order, and the fields deliberately not to create.

- **Base ID** (`app…`) — from the base URL: `airtable.com/appXXXXXXXXXXXXXX/…`
- **Table IDs** (`tbl…`) and **field IDs** (`fld…`) — from the base's API docs at
  `airtable.com/appXXXXXXXXXXXXXX/api/docs`, or the Metadata API.

Field *names* are yours to choose. The skill addresses everything by ID, so calling
a field `LinkedIn URL` instead of `Notes` costs nothing.

### `APIFY_POSTS_ACTOR`

Defaults to `harvestapi/linkedin-profile-posts`. Change it only if you have
substituted a different scraping actor, in which case the parsing in
`scrape-linkedin-posts` Step 4 will need to match its output shape.

## Validation

`scripts/validate_instance_config.py` runs two checks:

1. **Reference check** — every `{KEY}` used anywhere in `skills/` or `references/`
   exists in `instance-config.example.json`. This runs in CI on every push and
   catches a typo'd key before it becomes a confusing runtime failure.
2. **Config check** — when `instance-config.json` exists, it must define exactly the
   schema's keys, leave no required key empty, and use plausible ID formats
   (`app…`, `tbl…`, `fld…`, 24-hex).

The config check verifies *shape*, not existence. It cannot tell you an ID is real —
only that it looks like the right kind of thing. The first live run is still the
real test, which is why `scrape-linkedin-posts` starts with a single target.

## Adding a new key

1. Add it to `instance-config.example.json` with an empty value.
2. Reference it from the skill by wrapping the key name in single braces, the same
   way `AIRTABLE_POSTS_BASE_ID` is referenced above.
3. If it is optional, add it to `OPTIONAL_KEYS` in the validator.
4. Run the validator.

Note that the reference check scans this file too, so an illustrative key name here
must be a real one — writing a made-up example in brace form fails CI, which is the
check doing its job.

If a value changes per *run* rather than per deployment, it is not a config key —
it is a runtime placeholder like `{MOTION}`, and belongs in the validator's
`RUNTIME_PLACEHOLDERS` set instead.
