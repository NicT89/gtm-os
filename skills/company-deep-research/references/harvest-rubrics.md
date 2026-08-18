# Harvest rubrics

The classification tests `company-deep-research` applies at four steps. They live here rather than in the SKILL.md because they are consulted at one step each, and because each one exists to stop a specific misread that a live run produced.

## Motion classification (Step 2)

Read the pricing page's primary CTA first, then check it against the open sales reqs.

| Evidence | Reads as |
|---|---|
| Card checkout, self-serve signup, published per-seat price | PLG |
| Quote calculator, "book a demo", "contact sales", no price | Sales-led |
| Both present | Hybrid with a self-serve wedge; state where the boundary sits |
| Open AE reqs segmented (mid-market vs enterprise, by years of experience) | Sales-led, and the segmentation names the ACV bands |
| Fast-install path ("live in 5 minutes", app-store listing) alongside enterprise contact forms | Small accounts land nearly self-serve, large accounts go through sales. Say so explicitly; it is the wedge |

A quote calculator hosted on a different domain or a rapid-deploy host is worth a sentence of its own: a company shipping its own GTM micro apps has an internal build culture, which changes what an architecture proposal should assume.

## Named-customer proof-point tiers (Step 5)

| Source | Strength | Record as |
|---|---|---|
| Case study with named customer AND a metric | Proof point | Name, metric verbatim with unit and period, URL, capture date |
| Press release naming customers | Named customer, no metric | Name, URL, capture date; metric Unknown |
| Logo wall or "trusted by" strip | Claimed adoption | Name only, marked logo-wall |
| Enrichment-vendor description mentioning customers | Weakest | Only if nothing else names them, and labeled as vendor-sourced |
| Aggregate claim ("trusted by 10,000+ teams") | Company claim | Quote it, attribute it, never restate it as your own count |

A metric with no named customer, or a named customer with no metric, is half a proof point. Record the half you have. These land in outreach copy where a wrong number costs more than a missing one.

## Partner taxonomy (Step 6)

Three classes, and the tests that separate them:

**API integration.** Both sides publish the integration, both sides' docs describe it, and a customer configures it themselves. Usually listed in both companies' integration directories. The relationship is discoverable from either side.

**Embedded / OEM / white-label.** One company's engine runs inside the other's product. The partner's marketing page presents the capability as the partner's own; the vendor is credited in an FAQ answer, a legal or subprocessor page, a security page, or a co-published report, if at all. The end customer often does not know the vendor exists. Tells: the partner's feature page describes a capability the partner has no obvious engineering reason to have built; the vendor's press release uses the phrase "powers" or "provides X for platforms such as Y"; a co-branded report or whitepaper exists with no corresponding integration listing.

**Channel / referral / co-sell.** A referral form, a partner program page with tiers, a marketplace listing, or revenue-share language. Money moves for introductions, not for embedded technology.

**The test that matters: scrape the PARTNER's pages, not just the target's.** This is where the classification is actually decided, and it is the step that gets skipped. A live run classified a relationship as competitive based on the target's site alone; the partner's own FAQ disclosed that the target's engine was running inside the partner's workflow. Same two companies, opposite go-to-market conclusion: not a competing option a customer toggles, but a distribution surface and a reference-able install base.

A partner can hold two classes at once (embedded technology plus a co-marketing channel). Record both rather than picking one.

## Competitor set construction (Step 7)

Sources, in order: the company's own comparison or alternatives pages, analyst and database comparison pages, review-site category placement, and the competitors an enrichment record lists. Then split the set:

- **Head-on**: same job, same buyer, displaced in the same deal.
- **Adjacent**: overlaps on one feature, sells a different job to a different buyer or budget.
- **Partner with an overlapping feature**: ships a native version of one capability but appears on the partner page. Not a competitor by default. Misfiling one of these as a competitor produces outreach that insults a partnership the buyer values.

Record the company's stated differentiation claim verbatim and attributed. It is their positioning, not your assessment, and the report should never blur the two.

## Org-map reading (Step 4)

Seniority bands: C-suite, VP, Director, Manager, IC. Department cuts worth pulling separately: sales, marketing, customer success/support, operations, finance, business development, engineering, data.

Interpretation rules, which is the part that makes the counts useful:

- A one-person marketing function means the role is growth engineering, not campaign management.
- A support or CS count that is small against a large stated customer base means scaled-CS automation and health scoring are structural needs, not upgrades.
- Open reqs in two sales segments at once signal pipeline coverage pressure and near-term onboarding and hygiene work.
- A large engineering and data population with no GTM-engineering title anywhere means the systems surface is currently unowned; that is a real gap, and also an Ask before it is a claim.
- Offshore or specialist reqs (analyst pods, regional support) reveal delivery structure the org chart does not.

Counts are always "N people indexed by <source>", never "headcount N". Index coverage is partial and a gap against the company's own number is coverage, not shrinkage.
