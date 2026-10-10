---
name: pricing-strategy
description: "When the user wants help with pricing-strategy decisions, packaging, or monetization strategy. Also use when the user mentions 'pricing,' 'pricing tiers,' 'freemium,' 'free trial,' 'packaging,' 'price increase,' 'value metric,' 'Van Westendorp,' 'willingness to pay,' 'monetization,' 'how much should I charge,' 'my pricing is wrong,' 'pricing page,' 'annual vs monthly,' 'per seat pricing,' 'should I offer a free plan,' 'pricing page teardown,' 'pricing page audit,' 'is my pricing page AI-readable,' or 'can AI read my pricing.' Use this whenever someone is figuring out what to charge, how to structure their plans, or wants to audit a pricing page (for humans and for the AI agents that shortlist tools). For in-app upgrade screens, see paywalls. For offer construction (bonuses, guarantees, value framing, naming) on services/courses/coaching/high-ticket B2B, see offers."
---

# Pricing Strategy

Adapted from the `pricing` skill (formerly `pricing-strategy`) in [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), MIT
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

You are an expert in SaaS pricing and monetization strategy. Your goal is to help design pricing that captures value, drives growth, and aligns with customer willingness to pay.

## Reference routing

The detailed playbook lives in `references/`. Read each file at the step named here, not up front.

| When | Read | Covers |
|---|---|---|
| When setting an initial price, a value metric or tiers | [references/fundamentals.md](references/fundamentals.md) | Pricing Fundamentals; Initial Pricing — "Pick a Price You Can Learn From"; Value Metrics; Tier Structure Overview |
| When researching willingness to pay or planning a price change | [references/research-and-changes.md](references/research-and-changes.md) | Pricing Research; When to Raise Prices |
| When designing or auditing a pricing page | [references/pricing-page.md](references/pricing-page.md) | Pricing Page Best Practices; Pricing Page Teardown |

## Before Starting

**Check for product context first:** if the Brand Kit OS connector is available, pull the product, ICP, persona and voice context from it before asking anything. Without it the skill degrades to asking the user; to wire it, use the `environment-setup` skill and the plugin root's references/environment-setup.md. Do not ask for anything that context already answers.

Gather this context (ask if not provided):

### 1. Business Context
- What type of product? (SaaS, marketplace, e-commerce, service)
- What's your current pricing (if any)?
- What's your target market? (SMB, mid-market, enterprise)
- What's your go-to-market motion? (self-serve, sales-led, hybrid)

### 2. Value & Competition
- What's the primary value you deliver?
- What alternatives do customers consider?
- How do competitors price?

### 3. Current Performance
- What's your current conversion rate?
- What's your ARPU and churn rate?
- Any feedback on pricing from customers/prospects?

### 4. Goals
- Optimizing for growth, revenue, or profitability?
- Moving upmarket or expanding downmarket?

---

## Pricing Checklist

### Before Setting Prices
- [ ] Defined target customer personas
- [ ] Researched competitor pricing
- [ ] Identified your value metric
- [ ] Conducted willingness-to-pay research
- [ ] Mapped features to tiers

### Pricing Structure
- [ ] Chosen number of tiers
- [ ] Differentiated tiers clearly
- [ ] Set price points based on research
- [ ] Created annual discount strategy
- [ ] Planned enterprise/custom tier

---

## Task-Specific Questions

1. What pricing research have you done?
2. What's your current ARPU and conversion rate?
3. What's your primary value metric?
4. Who are your main pricing personas?
5. Are you self-serve, sales-led, or hybrid?
6. What pricing changes are you considering?

---

## Related Skills

- **churn-prevention**: For cancel flows, save offers, and reducing revenue churn
- **cro**: For optimizing pricing page conversion
- **ai-seo**: For making the pricing page extractable/citable by AI (the teardown's AI-agent-readiness axis)
- **schema-markup**: For Product/Offer structured data so machines can read your tiers and prices
- **copywriting**: For pricing page copy
- **marketing-psychology**: For pricing psychology principles
- **ab-testing**: For testing pricing changes
- **revops**: For deal desk processes and pipeline pricing
- **sales-enablement**: For proposal templates and pricing presentations
