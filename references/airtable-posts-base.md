# Airtable posts base: schema and setup

The `scrape-linkedin-posts` skill writes scraped LinkedIn posts and comments into an
Airtable base, then pushes a digest back into the CRM. `gtm-signal-scan` Step 6 reads
from the same base. This document is how you build that base in **your own** Airtable
workspace.

Nothing here is deployment-specific. The skill body carries `{KEY}` placeholders, never
IDs; the *shape* below is the portable part. Build the shape, record your own IDs in
`instance-config.json` (see [Recording your instance IDs](#recording-your-instance-ids)),
and the skill works against your workspace.

**Field names do not have to match.** The skill addresses every field by its Airtable
field ID, never by label. Name things whatever your team will understand — the
`Notes`-holding-a-LinkedIn-URL convention below is a legacy artifact of Airtable's
default template, and a fresh build should just call it `LinkedIn URL`.

## Build order

Link fields cannot be created until both sides exist, so build in this order:

1. `Contacts` and `Company` (the parent tables)
2. `Person Post` and `Company Posts` (link back to the parents)
3. `Post Comments` (links back to both post tables)

Create the base as an empty base, not from a template — Airtable templates ship
default tables and fields you will only have to delete.

## Tables

### 1. Contacts

One row per person you scrape. Created on demand by the skill when a target has no
existing row.

| Field | Type | Purpose |
|---|---|---|
| Name | Single line text | Person's name. Dedupe key (with LinkedIn URL). |
| LinkedIn URL | Single line text or URL | Their profile URL. The join key to `Person Post`. |
| Tracking | Single select | Options: `active`, `paused`, `archived`. Gates scheduled runs. See [The Tracking field](#the-tracking-field). |

### 2. Company

One row per company you scrape. Same shape as `Contacts`.

| Field | Type | Purpose |
|---|---|---|
| Name | Single line text | Company name. Dedupe key (with LinkedIn URL). |
| LinkedIn URL | Single line text or URL | Company page URL. Join key to `Company Posts`. |
| Tracking | Single select | Options: `active`, `paused`, `archived`. Gates scheduled runs. See [The Tracking field](#the-tracking-field). |

### 3. Person Post

One row per post by a person.

| Field | Type | Purpose |
|---|---|---|
| Name | Single line text (**primary**) | The author's bare first and last name, exactly as it appears on their `Contacts` row. See [The Name rule](#the-name-rule). |
| Post ID | Single line text | **Dedupe key.** Apify's `id`. Checked before every create. |
| Person LinkedIn URL | Single line text | Author's profile URL. |
| Company Name | Single line text | Author's employer at scrape time. |
| Post URL | URL | Permalink. |
| Post Content | Long text | Post body. |
| Post Type | Single select | Options: `Post`, `Repost`, `No Content`. |
| Posted Date | Date | From `postedAt.date`. |
| Likes | Number (integer) | From `engagement.likes`. |
| Comments Count | Number (integer) | From `engagement.comments`. |
| Shares | Number (integer) | From `engagement.shares`. |
| Scraped At | Date | When this row was written. |
| Contact | Link to `Contacts` | The author's parent row. Single record. |

### 4. Company Posts

One row per post by a company page. Identical to `Person Post` except for the
company-side join.

| Field | Type | Purpose |
|---|---|---|
| Name | Single line text (**primary**) | The bare company name, exactly as it appears on its `Company` row. See [The Name rule](#the-name-rule). |
| Post ID | Single line text | **Dedupe key.** |
| Company LinkedIn URL | Single line text | Company page URL. |
| Post URL | URL | Permalink. |
| Post Content | Long text | Post body. |
| Post Type | Single select | `Post`, `Repost`, `No Content`. |
| Posted Date | Date | |
| Likes | Number (integer) | |
| Comments Count | Number (integer) | |
| Shares | Number (integer) | |
| Scraped At | Date | |
| Company | Link to `Company` | The posting company's parent row. Single record. |

### 5. Post Comments

One row per comment, on either kind of post.

| Field | Type | Purpose |
|---|---|---|
| Comment ID | Single line text | **Dedupe key.** Apify's comment `id`. |
| Commenter Name | Single line text | From `actor.name`. |
| Commenter LinkedIn URL | Single line text | From `actor.linkedinUrl`. |
| Commenter Headline | Single line text | From `actor.position`. Often null — expected. |
| Comment Text | Long text | From `commentary`. |
| Commented At | Date | From `createdAt`. |
| Person Post | Link to `Person Post` | Populated **only** for comments on a person's post. |
| Company Post | Link to `Company Posts` | Populated **only** for comments on a company post. |
| Scraped At | Date | |

**The two link fields are mutually exclusive.** Every comment row fills exactly one and
leaves the other empty. The skill decides which by matching the comment's `postId`
against the `Post ID` of the row it just wrote.

## The Name rule

Both post tables have a **primary** `Name` field, and it carries the bare person or
company name, nothing else: `Jane Doe`, `Example Co`. Never a date suffix, never a post
type, never blank.

Two earlier versions of this engine got it wrong in opposite directions, which is why
the rule is written down (observed 2026-08-16):

- One wrote `First Last - YYYY-MM-DD` into `Name` as a scannable per-row label. That
  makes every row look unique in the grid and hides duplicates from a human reader.
- A later one stopped writing `Name` at all, leaving the primary field blank, which
  makes the table unreadable and the linked-record pickers useless.

Uniqueness and dedupe live on `Post ID`. The date lives in `Posted Date`. `Name` is
the human label for "whose post is this", and repeating the parent's name is the
point: it is what makes a filtered view of one person's posts legible.

## The Tracking field

`Contacts` and `Company` each carry a `Tracking` single-select with three options:
`active`, `paused`, `archived`. It is the off switch for scheduled runs.

**A recurring or scheduled `scrape-linkedin-posts` run touches only rows set to
`active`.** Rows set to `paused` or `archived` are skipped and counted in the report.
A manual run against a named target ignores Tracking entirely: a human asking for a
target is the decision, and the override is reported so the setting can be corrected
if it was not intentional.

An **empty** Tracking value is treated as `active`, so a base built before this field
existed keeps working. The skill reports how many rows were in scope by default
rather than by explicit setting, which is the nudge to go set them.

Why a field and not a deletion: without an off switch, the only way to stop a
scheduled job from spending actor budget on closed deals, departed contacts, and
out-of-scope companies is to delete their rows, which throws away the post history
that made them worth scraping. `paused` keeps the data and stops the spend.
`archived` says the row is kept for reference and will not come back.

The keys are optional in `instance-config.json`
(`AIRTABLE_FLD_CONTACTS_TRACKING`, `AIRTABLE_FLD_COMPANY_TRACKING`). Leave them empty
and every row is in scope for every scheduled run, which is the pre-existing behavior.

## Dates are bare dates

Both `Posted Date` fields reject an ISO timestamp (`2026-07-23T16:27:31.250Z`) with a
422. Truncate the actor's `postedAt.date` to `YYYY-MM-DD` before writing.
`Commented At` and `Scraped At` follow the same convention.

## Do not create these fields

The original base this schema was extracted from still carries four fields that are
deprecated and must never be written to. A fresh build should simply never create
them:

- `Person Post` → `Person Name` (superseded by the `Contact` link)
- `Company Posts` → `Company Name` (superseded by the `Company` link)
- Both post tables → `Has Content` (superseded by `Post Type: No Content`)
- Both post tables → `Comments Text` (a single flattened string per post, superseded
  by the `Post Comments` table)

They persist in the original base because Airtable has no API for field deletion —
they have to be removed by hand in the UI. That is a migration artifact, not a
schema requirement.

## Behaviors the schema has to support

Three things the skill relies on, worth understanding before you deviate:

- **Every write is deduped by ID first.** `Post ID` and `Comment ID` are checked
  against existing rows before any create. This is what makes repeated runs against
  overlapping targets safe.
- **Parent rows are deduped before creation.** The skill searches `Contacts` /
  `Company` by name or LinkedIn URL and only creates when nothing matches. Duplicate
  parent rows silently break the linking.
- **Zero-post targets still get a row.** A target with no posts in the window gets one
  row with `Post Type: No Content`, so "we checked and found nothing" is
  distinguishable from "we never checked." This mirrors the N/A convention in
  `skills/gtm-blueprint/references/field-provenance.md`.

Airtable caps batch writes at 50 records per request; the skill batches accordingly.

## Recording your instance IDs

Once the base exists, collect its IDs — these are what your deployment's
`instance-config.json` needs:

- **Base ID** — in the base URL: `airtable.com/appXXXXXXXXXXXXXX/...`
- **Table IDs** (`tbl...`) and **field IDs** (`fld...`) — from the base's API
  documentation at `airtable.com/appXXXXXXXXXXXXXX/api/docs`, or via the Metadata API.

Write them into `instance-config.json` under the `AIRTABLE_*` keys, then run
`python3 scripts/validate_instance_config.py`. The key list and where each value comes
from are in [instance-config.md](instance-config.md). Never edit IDs into a SKILL.md —
the skills resolve every ID from that file at run time, which is what keeps this repo
free of any one workspace's identifiers.

## Verification

Before the first real run:

- [ ] Five tables exist with the fields above, and the link fields resolve on both sides.
- [ ] `Post Type` has all three options, including `No Content`.
- [ ] `Contacts` and `Company` each have a `Tracking` single-select with `active`,
      `paused`, and `archived`, and a paused row is skipped by a scheduled run.
- [ ] Both post tables have `Name` as their **primary** field, and a dry-run row lands
      the bare person/company name in it with no date suffix.
- [ ] A manual test row in `Post Comments` can link to a `Person Post` row, and a
      second one to a `Company Posts` row.
- [ ] Your API token has `data.records:read`, `data.records:write`, and
      `schema.bases:read` on this base.
- [ ] A one-target dry run writes exactly one parent row and no duplicates when run
      twice against the same target.
