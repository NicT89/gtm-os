---
name: scrape-linkedin-posts
description: Scrape recent LinkedIn posts and comments for a person or company and write them into the Airtable posts base, then push a summary back into Apollo. Use when the user says "scrape LinkedIn posts", "scrape [person/company]'s LinkedIn", "refresh their post data", "pull recent LinkedIn activity for [contact/account]", or when gtm-signal-scan's Step 6 needs a posts digest for Excellent-tier contacts. Works standalone against one named target, against a whole Apollo list or tier, or on a recurring schedule to refresh existing pipeline contacts and accounts.
---

# Scrape LinkedIn Posts

Apify scrape, Airtable write with linked-record dedupe, Apollo push-back. One pipeline, three entry points: single target, batch (list/tier), or scheduled refresh.

## Scope per run

Floor 10 total targets, ceiling 50, per run. Each target gets up to 5 posts and up to 10 comments per post, looking back 3 months. If asked for a single named person or company, that's a 1-target run and the floor does not apply.

## Step 1: Resolve targets

Three modes, pick based on what the user asked for:

- **Single target**: user named one person or company. Resolve their LinkedIn URL from their Apollo contact/account record (contact/account custom fields, or the standard linkedin_url field), or ask the user for it if Apollo has none on file.
- **Batch**: user named an Apollo list, a tier (Excellent/Good), or gtm-signal-scan is calling this as its Step 6. Pull every contact/account in scope and their linkedin_url. Skip anyone with no LinkedIn URL and report them as skipped, don't guess a profile.
- **Scheduled refresh**: no explicit target, this run is on a cadence. Read the Contacts and Company tables in the Airtable base (below) for every existing row and re-scrape all of them, since the 3-month lookback means new posts will have entered the window since the last run.

## Step 2: Airtable base and field reference

Read `instance-config.json` at the plugin root and resolve every `{KEY}` below to its value. If that file is missing, or any key needed here is empty, STOP and tell the user to run the setup in the plugin root's `references/instance-config.md`; never guess an ID and never write into a base you have not been given.

Build the base first if it does not exist: the portable schema, build order, and the fields deliberately not to create are in `references/airtable-posts-base.md`. Field *names* do not matter — this skill addresses every field by ID.

Base `{AIRTABLE_POSTS_BASE_ID}`. Five tables:

- **Contacts** (`{AIRTABLE_TBL_CONTACTS}`): Name `{AIRTABLE_FLD_CONTACTS_NAME}`, LinkedIn URL `{AIRTABLE_FLD_CONTACTS_LINKEDIN_URL}`.
- **Company** (`{AIRTABLE_TBL_COMPANY}`): Name `{AIRTABLE_FLD_COMPANY_NAME}`, LinkedIn URL `{AIRTABLE_FLD_COMPANY_LINKEDIN_URL}`.
- **Person Post** (`{AIRTABLE_TBL_PERSON_POST}`): Post ID `{AIRTABLE_FLD_PERSON_POST_POST_ID}`, Person LinkedIn URL `{AIRTABLE_FLD_PERSON_POST_PERSON_LINKEDIN_URL}`, Company Name `{AIRTABLE_FLD_PERSON_POST_COMPANY_NAME}`, Post URL `{AIRTABLE_FLD_PERSON_POST_POST_URL}`, Post Content `{AIRTABLE_FLD_PERSON_POST_POST_CONTENT}`, Post Type `{AIRTABLE_FLD_PERSON_POST_POST_TYPE}`, Posted Date `{AIRTABLE_FLD_PERSON_POST_POSTED_DATE}`, Likes `{AIRTABLE_FLD_PERSON_POST_LIKES}`, Comments Count `{AIRTABLE_FLD_PERSON_POST_COMMENTS_COUNT}`, Shares `{AIRTABLE_FLD_PERSON_POST_SHARES}`, Scraped At `{AIRTABLE_FLD_PERSON_POST_SCRAPED_AT}`, Contact (link) `{AIRTABLE_FLD_PERSON_POST_CONTACT_LINK}`.
- **Company Posts** (`{AIRTABLE_TBL_COMPANY_POSTS}`): Post ID `{AIRTABLE_FLD_COMPANY_POSTS_POST_ID}`, Company LinkedIn URL `{AIRTABLE_FLD_COMPANY_POSTS_COMPANY_LINKEDIN_URL}`, Post URL `{AIRTABLE_FLD_COMPANY_POSTS_POST_URL}`, Post Content `{AIRTABLE_FLD_COMPANY_POSTS_POST_CONTENT}`, Post Type `{AIRTABLE_FLD_COMPANY_POSTS_POST_TYPE}`, Posted Date `{AIRTABLE_FLD_COMPANY_POSTS_POSTED_DATE}`, Likes `{AIRTABLE_FLD_COMPANY_POSTS_LIKES}`, Comments Count `{AIRTABLE_FLD_COMPANY_POSTS_COMMENTS_COUNT}`, Shares `{AIRTABLE_FLD_COMPANY_POSTS_SHARES}`, Scraped At `{AIRTABLE_FLD_COMPANY_POSTS_SCRAPED_AT}`, Company (link) `{AIRTABLE_FLD_COMPANY_POSTS_COMPANY_LINK}`.
- **Post Comments** (`{AIRTABLE_TBL_POST_COMMENTS}`): Comment ID `{AIRTABLE_FLD_POST_COMMENTS_COMMENT_ID}`, Commenter Name `{AIRTABLE_FLD_POST_COMMENTS_COMMENTER_NAME}`, Commenter LinkedIn URL `{AIRTABLE_FLD_POST_COMMENTS_COMMENTER_LINKEDIN_URL}`, Commenter Headline `{AIRTABLE_FLD_POST_COMMENTS_COMMENTER_HEADLINE}`, Comment Text `{AIRTABLE_FLD_POST_COMMENTS_COMMENT_TEXT}`, Commented At `{AIRTABLE_FLD_POST_COMMENTS_COMMENTED_AT}`, Person Post (link) `{AIRTABLE_FLD_POST_COMMENTS_PERSON_POST_LINK}`, Company Post (link) `{AIRTABLE_FLD_POST_COMMENTS_COMPANY_POST_LINK}`, Scraped At `{AIRTABLE_FLD_POST_COMMENTS_SCRAPED_AT}`.

Note: a base migrated from an earlier version of this schema may still show four deprecated fields in the UI — Person Post "Person Name", Company Posts "Company Name", and "Has Content" / "Comments Text" on both post tables. Never write to them. Airtable has no API for field deletion, so they can only be removed by hand by the base owner. A newly built base should never create them at all.

Before creating a Contacts or Company row, search the table for an existing row matching on Name or the Notes/LinkedIn URL field first. Only create if nothing matches. This skill runs repeatedly against overlapping targets, duplicate parent rows would break the linking.

## Step 3: Run the Apify scrape

Actor `harvestapi/linkedin-profile-posts`. One call per target batch. Parameters: 5 posts per profile, 10 comments per post, 3 month lookback window.

## Step 4: Parse the dataset

Two item types come back: `type: "post"` and `type: "comment"`.

- Post items: `id` (dedupe key = Post ID), `content`, `postedAt.date`, `postType`/repost detection, `engagement.likes`/`comments`/`shares`, `linkedinUrl`.
- Comment items: `id` (dedupe key = Comment ID), `commentary` (text), `createdAt`, `actor.name`, `actor.linkedinUrl`, `actor.position` (headline, often null), `postId` (matches the parent post's own `id`, this is the join key back to Person Post/Company Posts).

If a target has zero post items in the window, write one row with Post Type "No Content" and skip the comments step for that target entirely (there's nothing to have comments on).

## Step 5: Write to Airtable, deduped and linked

For each post: check Post ID against existing rows in the relevant table first, skip if found. Otherwise create the row and link it to the target's Contacts/Company record (single-item array in the Contact/Company link field).

For each comment: check Comment ID against existing Post Comments rows first, skip if found. Otherwise create the row, populate exactly one of the Person Post / Company Post link fields (array of the one matching record ID, found by matching `postId` against the Post ID you just wrote or already had), leave the other link field empty.

Batch all creates/updates in groups of 50 (Airtable API limit per request).

## Step 6: Push back to Apollo

Custom field IDs, resolved from `instance-config.json`:

- Contact-level "LinkedIn Posts": `{APOLLO_CF_CONTACT_LINKEDIN_POSTS}`.
- Account-level "Company LinkedIn Posts": `{APOLLO_CF_ACCOUNT_COMPANY_LINKEDIN_POSTS}`.

Never write posts data to a field named "View professional posts". Earlier versions of this engine used it; it is permanently deprecated because a silent-empty scrape wrote a false "no posts" verdict for someone who does post. It has no config key, by design.

For each target just scraped, build:

```json
{
  "linkedin_url": "...",
  "scraped_at": "YYYY-MM-DD",
  "has_content": true,
  "posts": [
    {"post_url": "...", "posted_date": "...", "type": "Post", "content": "...", "likes": 0, "comments_count": 0, "shares": 0,
     "comments": [{"name": "...", "headline": "...", "text": "..."}]}
  ]
}
```

`has_content: false` and `posts: []` if the target had no posts in the window.

Match to the Apollo contact/account by linkedin_url. Push via `apollo_contacts_update` / `apollo_accounts_update`, passing only the record id and `typed_custom_fields`, nothing else (these calls overwrite whatever fields you pass, don't blank out unrelated fields). Skip and report, don't guess, if no confident Apollo match exists. If a company has no Apollo Account object at all (contacts exist but the account was never created), skip the account-level push and flag it, don't create one without asking first.

## Step 7: Report

Targets scraped, posts written (new vs already-existed), comments written, Apollo pushes (contacts succeeded/skipped, accounts succeeded/skipped with reasons), and anyone skipped in Step 1 for missing a LinkedIn URL.

## Scheduling

This skill can be registered as a recurring scheduled task (via the `schedule` skill / scheduled-tasks tools) to run the "scheduled refresh" mode weekly or biweekly against the existing Contacts/Company tables, keeping post data current for personalization without a manual trigger each time.
