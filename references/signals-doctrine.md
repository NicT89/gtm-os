# Signals Doctrine
### The canonical buying-signal taxonomy for the GTM Engine. Every signal maps to a source, cost, decay window, motion route, and action. Apollo's native buying-intent settings cap at 6 options; this document is the richer definition the engine actually runs on.

Rule: a signal without an owner and an action is trivia. A signal is ACTIVE for a deployment only when its row is fully filled in and its gate is wired into the scan.

| # | Signal | Source (tool) | Cost | Decay | Routes to | Action |
|---|---|---|---|---|---|---|
| 1 | Funding event (stage, amount, recency) | Apollo system fields + CB Insights pre-filter | Free search; 1 credit org enrich | 6 months | M2/M3 by team state | Weekly scan gate |
| 2 | First GTM leadership posting | Apollo job postings + JD content | 1 credit/company | Posting lifetime | M3 | JD-driven copy; days-open and re-post tracking |
| 3 | GTM team expansion postings (multi-role) | Apollo job postings | 1 credit/company | Posting lifetime | M4 | Augment messaging |
| 4 | New GTM leader in seat <= 30 days | Apollo job-change filter | Free search | 30 days HARD | M5 (outranks 3/4) | Priority lane; 30/60/90 offer |
| 5 | Posting disappearance | Postings re-check on tracked accounts | 1 credit/company | Immediate | Hired -> M5; abandoned -> renewed-pain M3 | Scan follow-up |
| 6 | GTM persona presence/absence | Apollo people search by org_ids | Free | Re-check quarterly | The 2x2 routing axis | Structural gate, always on |
| 7 | Website visitor intent | Apollo tracking script (pages, recency, intent level) | Free (script installed) | 7-30 days | Any motion, warmth boost | Feeds Engagement score; future visitor motion |
| 8 | Commercial-maturity transition | CB Insights level change (1-5) | Free | Quarterly | CM 2 hints M2/M3, 3 hints M1/M4 | Scoring input + routing hint |
| 9 | Headcount growth spike | Apollo/CBI growth 6-12mo | Free | Quarterly | Scoring input | Fit score dimension |
| 10 | Social buying language | LinkedIn posts/comments (scrape-linkedin-posts skill, Apify), X (apidojo/tweet-scraper), Reddit (trudax/reddit-scraper-lite), Facebook groups | ~$0.002/post Apify | 30-90 days | Deepest-intent tier when present | Personalization fuel + intent gate (expansion) |
| 11 | Competitor review-site activity | G2/Capterra reviews of competitor products (scrape) | Scrape cost | 90 days | Switch-intent lane | Expansion gate |
| 12 | Champion job change into ICP company | Apollo job-change on past engaged contacts | Free search | 90 days | Warm-path priority | Expansion gate |

Active today: 1-6 (scan gates), 7-9 (passive scoring inputs). Expansion queue: 10-12.

Waterfall order when multiple gates run in one scan: deepest intent first (10 social language when active, then 4 new-leader, then 2/3 postings by age, then 1 funding, then lookalike fill). Tag every sourced account with its gate; the tag rides into the run-shape JSON and the account's scoring.

Catch-all rule (hard): T3 catch-all contacts are never enrolled in email sequences regardless of signal strength; LinkedIn/referral paths only.
