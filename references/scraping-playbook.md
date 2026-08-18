# Scraping Playbook

Extraction rules for every skill that reads the web. Learned from live runs; the dated entries in `references/dependency-observations.md` record where each rule came from.

## Tool choice: Firecrawl is the default

Firecrawl (scrape with markdown format, onlyMainContent true) is the default extractor for ALL web content in this engine. Plain fetch tools are permitted only for static assets you have already confirmed render server-side. Reasons, observed in production:

- ATS job pages (Gem, Ashby, Lever, Greenhouse embeds) are client-side rendered JavaScript apps. A plain fetch returns page metadata and zero content. Scrape them with waitFor 5000 and maxAge 0.
- Marketing sites vary; Firecrawl handles both static and JS-rendered pages uniformly, so standardizing removes a failure mode.

## Output format: markdown first, JSON for schema'd fields, HTML never

- **Markdown is the storage and reference format.** It preserves headings, lists, links, and emphasis (the structure that carries meaning in a JD or a pricing page), it diffs cleanly in git, it is the cheapest format in tokens when re-read later, and it pastes straight into reports. Save the raw markdown of any page a decision was based on.
- **JSON is for extraction against a known schema.** When the target fields are already defined (comp range, req ID, tool list, partner names), request Firecrawl's json format with a schema in the same call, and keep the markdown alongside as the audit trail. JSON without a schema invites the model to invent structure; markdown plus a later mapping step is more honest.
- **Raw HTML is for debugging only** (when extraction misses content and you need to see why). Never store it as the reference copy.

## Site reconnaissance order

1. Sitemap first (`sitemap_index.xml` and its children) to inventory pages before scraping.
2. Priority pages: platform/products, services (often the contract-level catalog), pricing, partners/integrations, careers, about, blog/newsroom for M&A and rebrand history.
3. The pricing page classifies the motion: a calculator or contact form means sales-led; card checkout means PLG; both means a hybrid with a self-serve wedge.
4. The partners/integrations page is a buyer-signal source: companies running those platforms are in-profile.

## Code footprint (GitHub and package registries)

A company's public code footprint is org intel: search github.com for the company's current AND former names (orgs, not just repos; check `site:github.com <name>` and `github.com/orgs/<name>/repositories`), plus npm/Composer/PyPI for published SDKs. What it reveals: integration modules show which platforms they invest in natively; infra repos (Terraform, Helm) reveal the cloud stack; employee accounts using a company-branded naming pattern (`firstname-companyname`) identify engineers; repo update recency shows what is actively maintained. Also check the company's developer docs subdomain (`developers.<domain>` or `docs.<domain>`). Product code is usually private; the public shell still maps the engineering surface. A representative live result: a mid-market commerce vendor's public org exposed its e-commerce platform integration modules plus Terraform and Helm cloud infrastructure while the product itself stayed private, which named both the platform partnerships and the cloud provider before a single call.

## Job boards as a secondary source

Cross-posting boards (Built In, Ladders, BeBee, Jobright) often publish structured tool tags and salary data the ATS hides. Use them to cross-check an extraction. Caution, learned the hard way: on category/listing pages the tags of ADJACENT listings sit next to the wrong company logo; only trust tags read from the listing's own detail page.

## Research cautions (instructions, not skills)

- **M&A merge artifacts:** enrichment-vendor org records (Apollo and peers) for recently merged or acquired companies are frequently merged entities: funding histories, social links, and founding dates can mix both companies. Verify funding and identity claims against primary press releases before citing them.
- **Unverifiable titles:** a JD or website can name a role that no public source confirms. Treat it as a question for the company, not a fact.
- **Absolute dates only** in anything saved or composed (rule inherited from `skills/gtm-blueprint/references/motion-templates.md`): "in July 2026", never "recently".
