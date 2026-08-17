# Airtable posts base: schema and setup

The `scrape-linkedin-posts` skill writes scraped LinkedIn posts and comments into an
Airtable base, then pushes a digest back into the CRM. `gtm-signal-scan` Step 6 reads
from the same base. This document is how you build that base in **your own** Airtable
workspace.

Nothing here is deployment-specific. The record IDs in the skill body are one
deployment's; the *shape* below is the portable part. Build the shape, record your own
IDs (see [Recording your instance IDs](#recording-your-instance-ids)), and the skill
works against your workspace.

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

### 2. Company

One row per company you scrape. Same shape as `Contacts`.

| Field | Type | Purpose |
|---|---|---|
| Name | Single line text | Company name. Dedupe key (with LinkedIn URL). |
| LinkedIn URL | Single line text or URL | Company page URL. Join key to `Company Posts`. |

### 3. Person Post

One row per post by a person.

| Field | Type | Purpose |
|---|---|---|
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

Once the base exists, collect its IDs — these are what your deployment's skill
configuration needs:

- **Base ID** — in the base URL: `airtable.com/appXXXXXXXXXXXXXX/...`
- **Table IDs** (`tbl...`) and **field IDs** (`fld...`) — from the base's API
  documentation at `airtable.com/appXXXXXXXXXXXXXX/api/docs`, or via the Metadata API.

Record them wherever your deployment keeps instance values. Until the instance-config
extraction lands (roadmap v1.4.0), that means editing the ID block in
`skills/scrape-linkedin-posts/SKILL.md` Step 2 to your own values.

## Verification

Before the first real run:

- [ ] Five tables exist with the fields above, and the link fields resolve on both sides.
- [ ] `Post Type` has all three options, including `No Content`.
- [ ] A manual test row in `Post Comments` can link to a `Person Post` row, and a
      second one to a `Company Posts` row.
- [ ] Your API token has `data.records:read`, `data.records:write`, and
      `schema.bases:read` on this base.
- [ ] A one-target dry run writes exactly one parent row and no duplicates when run
      twice against the same target.
