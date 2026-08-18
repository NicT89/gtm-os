# Company research output contract

The section-by-section format `company-deep-research` composes into. Section order is fixed so two research runs on two companies are comparable, and so a reader who only wants the org map knows where it is. Sections with nothing in them are kept and marked, never deleted: an absent section reads as "we did not look", which is the one thing research output must never be ambiguous about.

## Standing rules for every section

- **Every hard fact carries a source URL and a capture date.** A fact without one is not a fact yet; it is an Ask.
- **Absolute dates only.** "In March 2026", never "recently" or "last quarter". The document outlives the run.
- **Label directional numbers.** Enrichment-vendor revenue and headcount estimates, growth percentages, and anything an aggregator computed are written as "(vendor estimate, directional)".
- **Verbatim over paraphrase for claims.** A company's differentiation claim, a customer metric, and a pricing line are quoted, so the reader can tell the company's assertion from your assessment.
- **Empty is a finding.** Write "not extracted (sitemap has no partners page; searched X and Y)" rather than "no partners".
- **Inferences are marked "(inferred)"** and carry the evidence they were inferred from.

## Section order

### 1. Executive summary

Six to ten sentences, no bullets. What the company does, its stage and size, the one structural fact that changes how anyone should approach them (a live merger, a rebrand mid-flight, a single-person marketing function, a channel relationship that is really an OEM relationship), and what that fact implies. If the run produced one insight that is not on the company's website, it belongs here.

### 2. Identity and history

Founding date and founders. Funding rounds with date, amount, named lead investors, and board seats, each on its primary-source URL. Acquisitions in both directions. Rebrands with their date and the resulting legal entity. HQ and other offices. Headcount and headcount trend, labeled directional if vendor-supplied.

Close this section with a data-hygiene note whenever an enrichment record was involved for a post-M&A company: state explicitly which fields on that record are merge artifacts, so the next person to open it does not re-import the error.

### 3. Product catalog and upsell map

Modules or product lines as the company names them. The services or plans page usually reveals the contract-level catalog (tiers, add-on coverages, human-delivered services) more accurately than the marketing site's product pages. Finish with the cross-sell lattice in one paragraph: what a customer lands on, what the natural expansion is, and what attaches on top. This is the paragraph an expansion play is composed from.

### 4. Sales motion and lead sources

The motion classification and the evidence for it (pricing page CTA, segmentation in open sales reqs, presence or absence of a self-serve install path). Then the visible lead sources as a list: forms and what they route to, chat, partner referral paths, field events, content and SEO operation, review-site presence, and outbound if the stack and headcount show it.

### 5. ICP and named customers

The ICP as evidenced, not as claimed: the platforms in the integration list, the verticals the case studies cluster in, the size band the pricing implies. Then the named-customer table, one row per customer: name, source type (case study / press release / logo wall), source URL, capture date, and the metric verbatim with unit and period. Keep the proof points that carry hard numbers in their own short list at the end of the section, because that list is what feeds outreach.

### 6. Partners

The partner list grouped by the company's own categories, then the taxonomy pass: each partner classified API integration / embedded-OEM / channel, with the evidence that decided it (see `harvest-rubrics.md`). Call out explicitly any partner whose classification changed after reading the partner's own site.

### 7. GTM org map

Counts by department and by seniority band, sourced and phrased as "N people indexed by <source>", with the company's own stated headcount alongside. The GTM leadership chain. Named people by function, with the likely sponsor or hiring manager identified where a req is in play. Close with the shape read: functions one person deep, functions hiring, functions with no owner, and what each implies operationally.

### 8. Competitive frame

Head-on competitors, adjacent vendors, and partners-with-overlapping-features, kept in separate groups. The company's differentiation claim, quoted. Where a competitor set came from a comparison page, name the page: comparison pages are marketing artifacts and their framing is not neutral.

### 9. Stack and integration surface

Tools evidenced from the site, job postings, technology detection, and the code footprint, with the evidence per tool. Duplicated categories (two warehouses, two CRMs) are flagged, not silently reconciled. When the output feeds an architecture proposal, add MCP/API coverage per tool from the plugin root's `references/mcp-coverage-map.md`.

### 10. Code footprint

Public orgs under current and former names, notable repos and what they reveal (platform modules, infrastructure, SDKs), package-registry publications, developer docs location, and update recency. One line on what is conspicuously absent.

### 11. Open questions (Ask list)

Numbered, phrased ready to speak, one per open item, each naming who can answer it. Everything that could not be verified lands here rather than in an earlier section as a hedged sentence. Unverifiable titles, post-merger consolidation plans, and attribution gaps are the recurring three.

### 12. Method, sources, and cost

Connectors and tools used per section, the sites relied on, what failed and how it was worked around, and the credit and actor burn by category against the estimate given at the Step 0 gate. A reader should be able to reproduce the run from this section alone.

## Rendering

Render the human-facing version through the plugin root's `scripts/render_report.py`. Useful block types here: `stat_tiles` for the headline firmographics, `timeline` for funding and M&A history, `table` for customers and partners, `status_table` for the template mapping, and `hbar` for department counts. Do not restyle per run; consistency is the point.
