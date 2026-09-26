# Signals Doctrine
### The canonical buying-signal taxonomy for the GTM Engine. Every signal maps to a source, cost, decay window, typical play, and action. Apollo's native buying-intent settings cap at 6 options; this document is the richer definition the engine actually runs on.

## Two axes, two words: signal type and GTM motion

A third term, **play**, names our own route to an account (list, sequence, persona). It is
defined in `references/plays.md` and is neither of the two below.

The word "motion" named both of these until 1.9.4, and the collision wrote wrong copy.

**Signal type** is what pulled the account into a run: `hiring` or `funding`. It selects
the search filters, the account list, and which account fields the opener's hard number can
come from. `field_gate.py --signal-type` is the executable form. (The flag was `--motion`
through 1.9.3; that spelling still works and warns.)

**GTM motion** is the shape of the target company's own go-to-market: one of the five in
`skills/gtm-blueprint/references/motion-templates.md`, or a custom one. It decides the
blueprint's week lines and its closer, and it is classified in `gtm-blueprint` Step 3 —
later in the run, from different evidence.

They are independent. A company sourced on a hiring signal may run any of the five motions,
and the same company sourced on funding would run the same motion. **The closer comes from
the motion, never from the signal type.** `outreach-audit` said the opposite until 1.9.4 —
it keyed the closer on hiring-vs-funding and named a closer line ("documented for the
hire") that exists in no template — and `examples/blueprint-hiring.md`, the format anchor
everything is copied from, carried that closer under a blueprint classified
enterprise sales-led. It would have failed `gtm-blueprint`'s own quality gate, which checks
the closer against the recorded motion.

## Typical plays

The `Typical play` column below describes the kind of play a signal usually feeds, in
words, because plays belong to each deployment (`references/plays.md`) and their codes
differ from one to the next. It is orientation for writing plays, not a routing table.

Rule: a signal without an owner and an action is trivia. A signal is ACTIVE for a deployment only when its row is fully filled in and its gate is wired into the scan.

| # | Signal | Source (tool) | Cost | Decay | Typical play | Action |
|---|---|---|---|---|---|---|
| 1 | Funding event (stage, amount, recency) | Apollo system fields + CB Insights pre-filter | Free search; 1 credit org enrich | 6 months | No-GTM-team plays (founder-led, or first hire), by team state | Weekly scan gate |
| 2 | First GTM leadership posting | Apollo job postings + JD content | 1 credit/company | Posting lifetime | First-GTM-hire play | JD-driven copy; days-open and re-post tracking |
| 3 | GTM team expansion postings (multi-role) | Apollo job postings | 1 credit/company | Posting lifetime | Team-expansion play | Augment messaging |
| 4 | New GTM leader in seat <= 30 days | Apollo job-change filter | Free search | 30 days HARD | New-leader play (outranks first-hire and team-expansion) | Priority lane; 30/60/90 offer |
| 5 | Posting disappearance | Postings re-check on tracked accounts | 1 credit/company | Immediate | Hired -> new-leader play; abandoned -> renewed first-hire play | Scan follow-up |
| 6 | GTM persona presence/absence | Apollo people search by org_ids | Free | Re-check quarterly | The team-presence axis many plays are written on | Structural gate, always on |
| 7 | Website visitor intent | Apollo tracking script (pages, recency, intent level) | Free (script installed) | 7-30 days | Any play, warmth boost | Feeds Engagement score; future visitor play |
| 8 | Commercial-maturity transition | CB Insights level change (1-5) | Free | Quarterly | CM 2 hints no-team plays, 3 hints team plays | Scoring input + routing hint |
| 9 | Headcount growth spike | Apollo/CBI growth 6-12mo | Free | Quarterly | Scoring input | Fit score dimension |
| 10 | Social buying language | LinkedIn posts/comments (scrape-linkedin-posts skill, Apify), X (apidojo/tweet-scraper), Reddit (trudax/reddit-scraper-lite), Facebook groups | ~$0.002/post Apify | 30-90 days | Deepest-intent tier when present | Personalization fuel + intent gate (expansion) |
| 11 | Competitor review-site activity | G2/Capterra reviews of competitor products (scrape) | Scrape cost | 90 days | Switch-intent lane | Expansion gate |
| 12 | Champion job change into ICP company | Apollo job-change on past engaged contacts | Free search | 90 days | Warm-path priority | Expansion gate |

Active today: 1-6 (scan gates), 7-9 (passive scoring inputs). Expansion queue: 10-12.

Waterfall order when multiple gates run in one scan: deepest intent first (10 social language when active, then 4 new-leader, then 2/3 postings by age, then 1 funding, then lookalike fill). Tag every sourced account with its gate; the tag rides into the run-shape JSON and the account's scoring.

Catch-all rule: catch-all enrollment is one of the four NAMED HUMAN GATES, not a rule this document gets to settle. The operator chooses exclusion or enrollment once, on the record, with a bounce threshold armed; `skills/gtm-signal-scan/SKILL.md` Step 5 carries the two defensible positions and is authoritative. Exclusion is the conservative default and it is a default, not a ban. This line stated an absolute prohibition until 1.9.2, which would have had an agent automate past a registered gate.
