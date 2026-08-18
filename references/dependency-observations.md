# Dependency Observations Log

Third-party behavior drifts. This file records dated, observed behavior of external dependencies (Apify actors, CRM endpoints, Firecrawl, ATS pages) so skills cite living observations instead of hardcoding "always" or "never". Append-only; newest first. When two observations conflict, the skill handles BOTH cases and reports which occurred.

## Format

`YYYY-MM-DD | dependency | observation | run context`

## Log

- 2026-08-16 | harvestapi/linkedin-profile-posts | Actor RETURNED typed comment items with full commenter attribution (actor.name, actor.linkedinUrl, actor.position) when scrapeComments true, maxComments 10. Contradicts the prior standing note that comment items never return. Comment return is now classified INTERMITTENT: handle both cases. | Single-target run (person profile), 23 items, 2 authored posts, 6 comments captured.
- 2026-08-16 | harvestapi/linkedin-profile-posts | Captured comment count runs below the post's engagement.comments figure (6 captured vs 11 displayed). LinkedIn's public count includes replies-to-comments and unfetchable comments; the gap is normal, report it, don't chase it. | Same run.
- 2026-08-16 | jobs.gem.com (Gem ATS) | Plain fetch returns page metadata only, zero JD content (client-side rendered SPA). Firecrawl with waitFor 5000 extracts the complete posting first try. | JD extraction test.
- 2026-08-16 | Apollo org records | Org record for a recently merged company (acquirer + acquiree) was a merge artifact: funding history mixed both entities, linkedin_url pointed at the acquiree's page. Verify M&A-adjacent firmographics against primary press releases. | Org enrichment on a post-acquisition rebrand.
- 2026-08-16 | Built In category pages | Tool tags of adjacent listings render next to the wrong company logo on category/listing pages. Detail pages attribute correctly. | JD cross-check.
- 2026-08-11 (retro) | Airtable posts base | Both Posted Date fields reject ISO timestamps with a 422; bare YYYY-MM-DD required. | Batch scrape runs.
