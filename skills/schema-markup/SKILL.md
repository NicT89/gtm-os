---
name: schema-markup
description: When the user wants to add, fix, or optimize schema markup and structured data on their site. Also use when the user mentions "schema markup," "structured data," "JSON-LD," "rich snippets," "schema.org," "FAQ schema," "product schema," "review schema," "breadcrumb schema," "Google rich results," "knowledge panel," "star ratings in search," or "add structured data." Use this whenever someone wants their pages to show enhanced results in Google. For broader SEO issues, see seo-audit. For AI search optimization, see ai-seo.
---

# Schema Markup

Adapted from the `schema` skill (formerly `schema-markup`) in [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), MIT
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

You are an expert in structured data and schema markup. Your goal is to implement schema.org markup that helps search engines understand content and enables rich results in search.

## Reference routing

The detailed playbook lives in `references/`. Read each file at the step named here, not up front.

| When | Read | Covers |
|---|---|---|
| When choosing which schema types to use | [references/schema-types.md](references/schema-types.md) | Core Principles; Common Schema Types; Quick Reference; Multiple Schema Types |
| When adding the markup to a site and validating it | [references/implementation.md](references/implementation.md) | Validation and Testing; Implementation |

## Initial Assessment

**Check for product context first:** if the Brand Kit OS connector is available, pull the product, ICP, persona and voice context from it before asking anything. Without it the skill degrades to asking the user; to wire it, use the `environment-setup` skill and the plugin root's references/environment-setup.md. Do not ask for anything that context already answers.

Before implementing schema, understand:

1. **Page Type** - What kind of page? What's the primary content? What rich results are possible?

2. **Current State** - Any existing schema? Errors in implementation? Which rich results already appearing?

3. **Goals** - Which rich results are you targeting? What's the business value?

---

## Output Format

### Schema Implementation
```json
// Full JSON-LD code block
{
  "@context": "https://schema.org",
  "@type": "...",
  // Complete markup
}
```

### Testing Checklist
- [ ] Requested Google appearance is currently supported, or a separate semantic consumer is identified
- [ ] Validates in Schema.org Validator; supported Google features also pass Rich Results Test
- [ ] Required-field errors resolved; recommended-field warnings reviewed
- [ ] Matches page content
- [ ] All required properties included

---

## Task-Specific Questions

1. What type of page is this?
2. What rich results are you hoping to achieve?
3. What data is available to populate the schema?
4. Is there existing schema on the page?
5. What's your tech stack?

---

## Related Skills

- **seo-audit**: For overall SEO including schema review
- **ai-seo**: For AI search optimization (schema helps AI understand content)
- **programmatic-seo**: For templated schema at scale
- **site-architecture**: For breadcrumb structure and navigation schema planning
