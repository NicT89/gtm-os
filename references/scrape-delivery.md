# Scrape delivery: how scraped data reaches your posts base

GTM MCP runs the scrape (`references/gtm-mcp.md`). **Your Airtable connector does the write.**
Launch99 never holds your Airtable credentials, and you decide where the data is stored.
This file is the contract between the two, and `scripts/check_scrape_rows.py` is its gate.

## The shape

GTM MCP returns deliveries, one per posts-base table:

```json
{"deliveries": [{"table": "Person Post", "rows": [{"Post ID": "...", "Name": "..."}]}]}
```

Every row matches `references/airtable-posts-base.md` **1:1**: the same table names, the same
field names, the same option values. The checker reads the schema from that file at run
time, so there is one schema and no second copy of it here.

## Rules the checker enforces

- Only tables and fields the posts base defines. No invented columns.
- **No link fields.** The service cannot know your record ids, so links (`Contact`,
  `Company`, `Person Post`, `Company Post`) are filled by the plugin after it finds or creates
  the parent row.
- Each table's dedupe key is present: `Post ID` on posts, `Comment ID` on comments, `Name` on
  `Contacts` and `Company`.
- Single selects use a declared option. Dates are bare `YYYY-MM-DD`. Integers are integers.
  URLs are http(s).

## Writing the rows

1. Run `python3 scripts/check_scrape_rows.py delivery.json`. Fix or drop every failing row;
   never write one through.
2. Look up each row's dedupe key in the base before creating it, as
   `skills/scrape-linkedin-posts/SKILL.md` already does.
3. Write through your Airtable connector, filling the link fields from the parent rows.
4. **Read back** the written fields and compare values, not status. A write that returns
   success can still store nothing.

The posts-base rules that are about meaning, not shape (the Name rule, the Tracking field,
bare dates) stay in `references/airtable-posts-base.md` and apply unchanged.
