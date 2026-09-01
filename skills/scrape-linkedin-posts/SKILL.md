---
name: scrape-linkedin-posts
description: Scrape recent LinkedIn posts and comments for a person or company and write them into the Airtable posts base, then push a summary back into Apollo. Use when the user says "scrape LinkedIn posts", "scrape [person/company]'s LinkedIn", "refresh their post data", "pull recent LinkedIn activity for [contact/account]", or when gtm-signal-scan's Step 6 needs a posts digest for Excellent-tier contacts. Works standalone against one named target, against a whole Apollo list or tier, or on a recurring schedule to refresh existing pipeline contacts and accounts.
---

# Scrape LinkedIn Posts

Apify scrape, Airtable write with linked-record dedupe, Apollo push-back. One pipeline, three entry points: single target, batch (list/tier), or scheduled refresh.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Scope per run

Floor 10 total targets, ceiling 50, per run. Each target gets ALL authored posts inside the 3-month lookback window (no per-target post cap, the window is the cap) and up to 15 comments per post. If asked for a single named person or company, that's a 1-target run and the floor does not apply.

## Model / effort guidance

First-time runs against a target (new Contacts/Company row, first CRM push for that record) should run at normal effort: dedupe, error recovery on schema mismatches, and the authored-vs-repost filter below all benefit from it, and a bad write is more expensive to fix than the tokens saved.

Scheduled-refresh mode (re-scraping targets that already have a Contacts/Company row and a proven field mapping) is a reasonable candidate for a cheaper/faster model at low effort, now that the authored-post filter and dataset projection below are explicit rules rather than something to infer from the raw data shape each run.

## Step 1: Resolve targets

Three modes, pick based on what the user asked for:

- **Single target**: user named one person or company. Resolve their LinkedIn URL from their Apollo contact/account record (contact/account custom fields, or the standard linkedin_url field), or ask the user for it if Apollo has none on file.
- **Batch**: user named an Apollo list, a tier (Excellent/Good), or gtm-signal-scan is calling this as its Step 6. Pull every contact/account in scope and their linkedin_url. Skip anyone with no LinkedIn URL and report them as skipped, don't guess a profile.
- **Scheduled refresh**: no explicit target, this run is on a cadence. Read the Contacts and Company tables in the Airtable base (below) and re-scrape the rows that are still in scope, since the 3-month lookback means new posts will have entered the window since the last run.

**Recurring and scheduled runs touch ONLY rows whose Tracking field is `active`** (`{AIRTABLE_FLD_CONTACTS_TRACKING}` on Contacts, `{AIRTABLE_FLD_COMPANY_TRACKING}` on Company). A row set to `paused` or `archived` is skipped and counted in the report; it is never re-scraped and never silently reactivated. This is the off switch: a scheduled job with no such switch keeps spending actor budget on deals that closed, people who left, and companies that went out of scope months ago, and the only way to stop it is to delete data. A row with an empty Tracking value is treated as `active`, so an existing base keeps working, but say in the report how many rows were in-scope by default rather than by explicit setting.

Manual runs are exempt: if a human names a target, scrape it regardless of Tracking. The user asking is the decision. Report that you overrode a non-active row so the setting can be corrected if that was not intended.

## Step 2: Airtable base and field reference

Read `instance-config.json` at the plugin root and resolve every `{KEY}` below to its value. If that file is missing, or any key needed here is empty, STOP and tell the user to run the setup in the plugin root's `references/instance-config.md`; never guess an ID and never write into a base you have not been given.

**Two exceptions, and only two.** `{AIRTABLE_FLD_CONTACTS_TRACKING}` and `{AIRTABLE_FLD_COMPANY_TRACKING}` are optional: when either is empty, do NOT stop. Treat every row in that table as `active`, proceed, and say in the Step 7 report that the run was unfiltered because the base has no Tracking field. A base built before that field existed must keep working, which is the whole point of the fallback.

Build the base first if it does not exist: the portable schema, build order, and the fields deliberately not to create are in `references/airtable-posts-base.md`. Field *names* do not matter — this skill addresses every field by ID.

Base `{AIRTABLE_POSTS_BASE_ID}`. Five tables:

- **Contacts** (`{AIRTABLE_TBL_CONTACTS}`): Name `{AIRTABLE_FLD_CONTACTS_NAME}`, LinkedIn URL `{AIRTABLE_FLD_CONTACTS_LINKEDIN_URL}`, Tracking `{AIRTABLE_FLD_CONTACTS_TRACKING}`.
- **Company** (`{AIRTABLE_TBL_COMPANY}`): Name `{AIRTABLE_FLD_COMPANY_NAME}`, LinkedIn URL `{AIRTABLE_FLD_COMPANY_LINKEDIN_URL}`, Tracking `{AIRTABLE_FLD_COMPANY_TRACKING}`.
- **Person Post** (`{AIRTABLE_TBL_PERSON_POST}`): Name (primary) `{AIRTABLE_FLD_PERSON_POST_NAME}`, Post ID `{AIRTABLE_FLD_PERSON_POST_POST_ID}`, Person LinkedIn URL `{AIRTABLE_FLD_PERSON_POST_PERSON_LINKEDIN_URL}`, Company Name `{AIRTABLE_FLD_PERSON_POST_COMPANY_NAME}`, Post URL `{AIRTABLE_FLD_PERSON_POST_POST_URL}`, Post Content `{AIRTABLE_FLD_PERSON_POST_POST_CONTENT}`, Post Type `{AIRTABLE_FLD_PERSON_POST_POST_TYPE}`, Posted Date `{AIRTABLE_FLD_PERSON_POST_POSTED_DATE}`, Likes `{AIRTABLE_FLD_PERSON_POST_LIKES}`, Comments Count `{AIRTABLE_FLD_PERSON_POST_COMMENTS_COUNT}`, Shares `{AIRTABLE_FLD_PERSON_POST_SHARES}`, Scraped At `{AIRTABLE_FLD_PERSON_POST_SCRAPED_AT}`, Contact (link) `{AIRTABLE_FLD_PERSON_POST_CONTACT_LINK}`.
- **Company Posts** (`{AIRTABLE_TBL_COMPANY_POSTS}`): Name (primary) `{AIRTABLE_FLD_COMPANY_POSTS_NAME}`, Post ID `{AIRTABLE_FLD_COMPANY_POSTS_POST_ID}`, Company LinkedIn URL `{AIRTABLE_FLD_COMPANY_POSTS_COMPANY_LINKEDIN_URL}`, Post URL `{AIRTABLE_FLD_COMPANY_POSTS_POST_URL}`, Post Content `{AIRTABLE_FLD_COMPANY_POSTS_POST_CONTENT}`, Post Type `{AIRTABLE_FLD_COMPANY_POSTS_POST_TYPE}`, Posted Date `{AIRTABLE_FLD_COMPANY_POSTS_POSTED_DATE}`, Likes `{AIRTABLE_FLD_COMPANY_POSTS_LIKES}`, Comments Count `{AIRTABLE_FLD_COMPANY_POSTS_COMMENTS_COUNT}`, Shares `{AIRTABLE_FLD_COMPANY_POSTS_SHARES}`, Scraped At `{AIRTABLE_FLD_COMPANY_POSTS_SCRAPED_AT}`, Company (link) `{AIRTABLE_FLD_COMPANY_POSTS_COMPANY_LINK}`.
- **Post Comments** (`{AIRTABLE_TBL_POST_COMMENTS}`): Comment ID `{AIRTABLE_FLD_POST_COMMENTS_COMMENT_ID}`, Commenter Name `{AIRTABLE_FLD_POST_COMMENTS_COMMENTER_NAME}`, Commenter LinkedIn URL `{AIRTABLE_FLD_POST_COMMENTS_COMMENTER_LINKEDIN_URL}`, Commenter Headline `{AIRTABLE_FLD_POST_COMMENTS_COMMENTER_HEADLINE}`, Comment Text `{AIRTABLE_FLD_POST_COMMENTS_COMMENT_TEXT}`, Commented At `{AIRTABLE_FLD_POST_COMMENTS_COMMENTED_AT}`, Person Post (link) `{AIRTABLE_FLD_POST_COMMENTS_PERSON_POST_LINK}`, Company Post (link) `{AIRTABLE_FLD_POST_COMMENTS_COMPANY_POST_LINK}`, Scraped At `{AIRTABLE_FLD_POST_COMMENTS_SCRAPED_AT}`.

**The primary Name field carries the bare person or company name, nothing else.** On a Person Post row it is the person's first and last name exactly as it appears on their Contacts row; on a Company Posts row it is the company name. Never append a date, a post type, or any other suffix, and never leave it blank. History on this rule (2026-08-16): earlier engine versions wrote "First Last - YYYY-MM-DD" as a scannable per-row label, and a later version stopped writing Name at all. Both are wrong. Uniqueness and dedupe live on Post ID; the date lives in Posted Date.

**Posted Date fields are bare dates, not datetimes.** Both Posted Date fields reject an ISO timestamp (e.g. `2026-07-23T16:27:31.250Z`) with a 422. Truncate the actor's `postedAt.date` to `YYYY-MM-DD` before writing. Commented At and Scraped At follow the same `YYYY-MM-DD` convention.

Note: a base migrated from an earlier version of this schema may still show four deprecated fields in the UI — Person Post "Person Name", Company Posts "Company Name", and "Has Content" / "Comments Text" on both post tables. Never write to them. Airtable has no API for field deletion, so they can only be removed by hand by the base owner. A newly built base should never create them at all.

Before creating a Contacts or Company row, search the table for an existing row matching on Name or the Notes/LinkedIn URL field first. Only create if nothing matches. This skill runs repeatedly against overlapping targets, duplicate parent rows would break the linking.

## Step 3: Run the Apify scrape

Actor `{APIFY_POSTS_ACTOR}`. One call per target batch. Parameters: `maxPosts` 0 (all posts, the window is the cap), `postedLimit` "3months", `scrapeComments` true, `maxComments` 15.

**The actor returns the target's full activity feed, not just their authored posts.** Roughly 80-90% of post items are typically things the target liked, commented on, or reposted from someone else, not things they wrote. Do not write these to Airtable or push them to the CRM; they will pollute the record with someone else's content attributed to the wrong person.

**Project only the fields you need when reading the dataset.** `get-dataset-items` supports a `fields=` parameter; use it (e.g. `fields="type,id,postId,content,commentary,postedAt.date,createdAt,engagement,author.publicIdentifier,author.name,linkedinUrl,repostedBy.publicIdentifier,commentIds,actor.name,actor.linkedinUrl,actor.position"`) instead of pulling the full ~167-field item for every row. The unprojected pull runs well past the context-per-tool-call limit; projecting up front cuts the token cost of this step by roughly half.

## Step 4: Parse the dataset

**Filter to authored posts first, before anything else.** Keep only items where `author.publicIdentifier` matches the target's LinkedIn slug (from the target's profile URL) AND `repostedBy` is null/absent. Items where `repostedBy.publicIdentifier` equals the target's slug are things they reposted or reacted to and get discarded, not written. Keep EVERY authored item that survives the filter (the 3-month window is the only cap), sorted by `postedAt.date` descending. Reposts and reactions are still worth reading before discarding: they often carry relationship intel (events, colleagues, investors) for the Step 7 report.

Two item types come back: `type: "post"` and `type: "comment"`.

- Post items: `id` (dedupe key = Post ID), `content`, `postedAt.date`, `postType`/repost detection, `engagement.likes`/`comments`/`shares`, `linkedinUrl`.
- Comment items: `id` (dedupe key = Comment ID), `commentary` (text), `createdAt`, `actor.name`, `actor.linkedinUrl`, `actor.position` (headline, often null), `postId` (matches the parent post's own `id`, this is the join key back to Person Post/Company Posts).

Comment-item return is INTERMITTENT (see the plugin root's `references/dependency-observations.md`): some runs return typed comment items with full commenter attribution, others return none despite `scrapeComments` being set. Handle both: when comment items arrive, write them; when they don't, note it in the Step 7 report. Never treat either behavior as guaranteed. Also expect the actor's returned comment count per post to run below the post's `engagement.comments` number: LinkedIn's public count includes replies-to-comments and comments the actor cannot fetch, so a gap between the two is normal and worth stating in the report, not a defect.

If a target has zero authored post items in the window, write one row with Post Type "No Content" (Name still carries the bare person/company name) and skip the comments step for that target entirely (there's nothing to have comments on).

## Step 5: Write to Airtable, deduped and linked

For each post: check Post ID against existing rows in the relevant table first, skip if found. Otherwise create the row, set Name to the bare person/company name, and link it to the target's Contacts/Company record (single-item array in the Contact/Company link field). Remember that Posted Date is a bare `YYYY-MM-DD` string.

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

Match to the Apollo contact/account by linkedin_url. Push via `apollo_contacts_update` / `apollo_accounts_update`, passing only the record id and `typed_custom_fields`, nothing else (these calls overwrite whatever fields you pass, don't blank out unrelated fields). This is a destructive write with no undo surfaced by the tool: double-check the record id and the authored-posts-only filter before calling it. Skip and report, don't guess, if no confident Apollo match exists. If a company has no Apollo Account object at all (contacts exist but the account was never created), skip the account-level push and flag it, don't create one without asking first.

## Step 7: Report

Targets scraped, posts written (new vs already-existed), comments written, the per-post gap between `engagement.comments` and comments actually captured, Apollo pushes (contacts succeeded/skipped, accounts succeeded/skipped with reasons), and anyone skipped in Step 1 for missing a LinkedIn URL. State whether comment items returned this run, and log that observation with the date to the plugin root's `references/dependency-observations.md`.

Also surface relationship intel found in the discarded reposts and in commenter identities: events attended, hosts, colleagues, investors, and recurring commenters.

## Step 8: Rebuild the scrape roster (every run, no exceptions)

**Every run ends by rebuilding `{SCRAPE_ROSTER_ARTIFACT}` from the live Contacts and Company tables.** Scheduled or manual, one target or fifty, success or partial failure: the roster is regenerated from what the tables actually contain right now, never patched incrementally from what this run happened to touch.

The roster lists every Contacts and Company row with its Tracking state, LinkedIn URL, and the date it was last scraped. It is the human-readable answer to "what is this scheduled job going to spend money on next week," and it is the artifact a human reads before approving a cadence change.

Rebuilding rather than appending is the point. An incrementally maintained roster drifts away from the tables silently: rows paused in Airtable stay listed as active, rows added by another run never appear, and the drift is invisible until a scheduled run scrapes something it should not have. A full rebuild from the live tables cannot drift, and it costs one read.

Write it to the run's working folder alongside the run manifest (the plugin root's `references/run-manifest.md`). It is a run artifact: it lives in the operator's own storage and is never committed to this repo.

## Breadcrumb mode (optional second-degree pass, human gate)

The people tagged in a target's posts and the people commenting on them are relationship edges worth following: they reveal who the target builds with, buys from, and answers to. After a first-degree run, offer the user a breadcrumb pass: list the tagged/commenting people found (name, headline, relationship context), let the human select which to scrape, and run those as a normal batch. **Never auto-scrape second-degree targets.** Each one costs actor spend and Airtable rows, so the selection is always a human gate. Record the relationship context ("commented on X's July 2026 post about the partner event") in the run report and the audit log so the edge survives the run; if your base carries a free-text notes field on Contacts, write it there too, but never overwrite the LinkedIn URL field to make room for it.

## Scheduling

This skill can be registered as a recurring scheduled task (via the `schedule` skill / scheduled-tasks tools) to run the "scheduled refresh" mode weekly or biweekly against the existing Contacts/Company tables, keeping post data current for personalization without a manual trigger each time.

Two rules make a cadence safe to leave running, and both are covered above: a scheduled run touches only `active` Tracking rows (Step 1), and every run rebuilds `{SCRAPE_ROSTER_ARTIFACT}` from the live tables (Step 8). Together they mean the standing answer to "what will this spend next week" is a current file rather than a guess, and pausing a target is a field edit rather than a deleted row. Confirm the connectors survive a scheduled invocation before depending on one: interactively-authenticated MCP servers may be unavailable headless, per the plugin root's `references/environment-setup.md`.

For scheduled-refresh runs specifically, this is the mode best suited to a cheaper/lower-effort model; see "Model / effort guidance" above. First-time runs against a new target should stay on a stronger model/effort setting.
