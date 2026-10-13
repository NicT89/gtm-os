---
name: competitor-alternatives
description: "When the user wants to create competitor comparison or alternative pages for SEO and buyer-facing use. Also use when the user mentions 'alternative page,' 'vs page,' 'competitor comparison,' 'comparison page,' '[Product] vs [Product],' '[Product] alternative,' 'competitive landing pages,' 'how do we compare to X,' 'competitor teardown,' 'audit our competitor pages,' 'are our comparison pages out of date,' or 'competitive asset audit.' Use this for any content that positions your product against competitors. Covers four formats: singular alternative, plural alternatives, you vs competitor, and competitor vs competitor. For auditing existing claims (not researching competitors from scratch, which is this plugin's company-deep-research; not technical SEO on these pages, which is seo-audit), use the asset audit here. For internal battle cards and sales-specific competitor docs, see sales-enablement."
---

# Competitor & Alternative Pages

Adapted from the `competitors` skill (formerly `competitor-alternatives`) in [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), MIT
licensed, at commit `1efedbc`. The upstream license is kept in this folder's `LICENSE`.
Sibling skills it names that this plugin does not ship live in that repo.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin
root VERSION file, notify on mismatch, continue.

## Numbers in what you produce

This plugin's no-invented-numbers rule applies in full. Every figure in a deliverable (a
conversion rate, a benchmark, a lift, a price point) comes from the user's own data or a
specific source you can name and link. Figures in this skill's examples and templates are
illustrations or placeholders, never benchmarks: do not carry them into output. With no
source, write the qualitative claim instead.

You are an expert in creating competitor comparison and alternative pages. Your goal is to build pages that rank for competitive search terms, provide genuine value to evaluators, and position your product effectively.

## Reference routing

The detailed playbook lives in `references/`. Read each file at the step named here, not up front.

| When | Read | Covers |
|---|---|---|
| Before drafting any page | [references/page-formats.md](references/page-formats.md) | Core Principles; Page Formats; Essential Sections |
| When researching competitors, structuring their data, or planning URLs and keywords | [references/research-and-seo.md](references/research-and-seo.md) | Content Architecture; Research Process; SEO Considerations |

## Initial Assessment

**Check for product context first:** if the Brand Kit OS connector is available, pull the product, ICP, persona and voice context from it before asking anything. Without it the skill degrades to asking the user; to wire it, use the `environment-setup` skill and the plugin root's references/environment-setup.md. Do not ask for anything that context already answers.

**Never guess the competitor.** If the request doesn't name one and the context file doesn't identify it, ask, and stop there. Don't draft a polished page around the most likely candidate.

Before creating competitor pages, understand:

1. **Your Product**
   - Core value proposition
   - Key differentiators
   - Ideal customer profile
   - Pricing model
   - Strengths and honest weaknesses

2. **Competitive Landscape**
   - Direct competitors
   - Indirect/adjacent competitors
   - Market positioning of each
   - Search volume for competitor terms

3. **Goals**
   - SEO traffic capture
   - Sales enablement
   - Conversion from competitor users
   - Brand positioning

---

## Output Format

### Competitor Data File
Complete competitor profile in YAML format for use across all comparison pages.

### Page Content
For each page: URL, meta tags, full page copy organized by section, comparison tables, CTAs.

### Page Set Plan
Recommended pages to create with priority order based on search volume.

### Asset Audit Report
Claims checked per asset, status counts (current / changed / unverifiable / overclaimed), and a prioritized fix list with replacement wording.

---

## Task-Specific Questions

1. What are common reasons people switch to you?
2. Do you have customer quotes about switching?
3. What's your pricing vs. competitors?
4. Do you offer migration support?

---

## Related Skills

- **programmatic-seo**: For building competitor pages at scale
- **copywriting**: For writing compelling comparison copy
- **seo-audit**: For optimizing competitor pages
- **schema-markup**: For FAQ and comparison schema
- **sales-enablement**: For battle cards and internal sales collateral, decks, and objection docs
