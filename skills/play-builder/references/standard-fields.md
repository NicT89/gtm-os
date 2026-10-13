# Standard and custom Apollo fields

**Standard** fields are the ones the engine's skills read or write for every customer,
whatever their plays. They are created once, at onboarding. **Custom** fields belong to a
play (or to an optional connector) and are created only when a play that needs them is
built. The line follows the repo rule: what is universal is fixed here; what differs by
organization is declared per play.

Each field's ID goes in `instance-config.json` under the key named here; the labels use the
deployment's field prefix (`{INSTANCE_FIELD_PREFIX}`), never "[Claude]", because a field
label becomes a merge token and "[Claude]" would land inside every
`{{contact.<prefix> Opener}}`.

## Standard (created at onboarding)

| Key | Object | Type | Written by |
|---|---|---|---|
| `APOLLO_CF_CONTACT_OPENER` | contact | multi-line text | `gtm-signal-scan` Step 6, per `outreach-audit`'s spec |
| `APOLLO_CF_CONTACT_BLUEPRINT` | contact | multi-line text | `gtm-blueprint` |
| `APOLLO_CF_CONTACT_LINKEDIN_PROFILE_SUMMARY` | contact | multi-line text | the enrichment workflow |
| `APOLLO_CF_CONTACT_RESEARCH_COMPANY_PROFILE` | contact | multi-line text | the research workflow or `company-deep-research` |
| `APOLLO_CF_CONTACT_LINKEDIN_POSTS` | contact | multi-line text | `scrape-linkedin-posts` |
| `APOLLO_CF_CONTACT_PERSONA_INTELLIGENCE` | contact | multi-line text | the enrichment workflow |
| `APOLLO_CF_ACCOUNT_LINKEDIN_COMPANY_SUMMARY` | account | multi-line text | the enrichment workflow |
| `APOLLO_CF_ACCOUNT_COMPANY_LINKEDIN_POSTS` | account | multi-line text | `scrape-linkedin-posts` |
| `APOLLO_CF_ACCOUNT_PLAY`, `APOLLO_CF_CONTACT_PLAY` | both | text | `gtm-signal-scan` Step 1.5: `CODE \| reasoning \| evidence` |
| `APOLLO_CF_ACCOUNT_PLAY_ASSIGNED_ON`, `APOLLO_CF_CONTACT_PLAY_ASSIGNED_ON` | both | date | `gtm-signal-scan` Step 1.5 |

## Custom (created with the play that needs them)

| Key | Needed by |
|---|---|
| `APOLLO_CF_ACCOUNT_GTM_JOBS_WITH_URL`, `APOLLO_CF_ACCOUNT_JD_SUMMARY`, `APOLLO_CF_ACCOUNT_ROLE_ARCHETYPES`, `APOLLO_CF_ACCOUNT_AVAILABLE_GTM_ROLES` | Plays fed by the hiring signal (the field gate requires the first three for it) |
| `APOLLO_CF_ACCOUNT_CBI_MOSAIC_SCORE`, `APOLLO_CF_ACCOUNT_CBI_COMMERCIAL_MATURITY`, `APOLLO_CF_ACCOUNT_NAMED_INVESTORS` | Only with the CB Insights connector |
| `APOLLO_CF_ACCOUNT_TECH_STACK_DETAILS`, `APOLLO_CF_CONTACT_HAS_LINKEDIN`, `APOLLO_CF_CONTACT_STARTUP_SMB_FIT` | Deployment-specific; create only if a play names them |

A play's own new fields go in its `fields.custom` with a purpose, and get an instance key only
if a skill needs to read them by key.

## Creating them

The Apollo connector exposes `apollo_fields_create`, which contradicts the older note in
this repo that the API cannot create field definitions. It has not been exercised end to end
here yet, so the first live use creates **one** field and reads it back before doing more.

1. **Look first.** `apollo_fields_index` for the modality. Not set up does not mean not owned:
   a field with the same purpose may exist under another label. Reuse it and record its ID.
2. **Show the exact list and get approval per field**: modality, label, type. The tool itself
   requires explicit confirmation; a field appears on every record of its modality, and
   picklist or enrichment fields cannot be cleanly undone.
3. **Create plain fields only** (`computed_type` omitted). Do not create AI or enrichment
   columns from this skill: composition belongs to the skills, where the gates are.
4. **Read the field back** from `apollo_fields_index` and confirm label and type. Apollo has
   accepted fields and stored nothing before (CLAUDE.md, "read the write back"). Only then
   write its ID into `instance-config.json`.
5. **Fallback:** the Apollo UI. The procedure after creation is the same.
