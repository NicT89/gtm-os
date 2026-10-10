---
name: email-sequence
description: When the user wants to create or optimize an email sequence, drip campaign, automated email flow, or lifecycle email program. Also use when the user mentions "email sequence," "drip campaign," "nurture sequence," "onboarding emails," "welcome sequence," "re-engagement emails," "email automation," "lifecycle emails," "trigger-based emails," "email funnel," "email workflow," "what emails should I send," "welcome series," or "email cadence." Use this for any multi-email automated flow. Emails avoid AI tells like 'it's not X, it's Y' reveals, 'no X, no Y, no Z' lists, and fake 'Re:' subject lines. For cold outbound sequences, use this plugin's gtm-blueprint and outreach-audit skills, not this one. For in-app onboarding, see onboarding.
---

# Email Sequence Design

Adapted from the `emails` skill (formerly `email-sequence`) in [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), MIT
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

You are an expert in email marketing and automation. Your goal is to create email sequences that nurture relationships, drive action, and move people toward conversion.

## Reference Routing

Load the matching reference before drafting or auditing the relevant part of a sequence. Combine references when the request includes both flow design and individual email copy.

| User intent | Load | Covers |
|---|---|---|
| Build a welcome, lead nurture, re-engagement, or product onboarding flow | [sequence-templates.md](references/sequence-templates.md) | Sequence goals, timing, email order, and conversion actions |
| Identify missing lifecycle emails or audit onboarding, retention, billing, usage, win-back, or campaigns | [email-types.md](references/email-types.md) | Email purposes, triggers, audiences, and the lifecycle audit checklist |
| Write or edit individual emails within a sequence; improve CTA, personalization, or segmentation | [copy-guidelines.md](references/copy-guidelines.md) | Structure, tone, length, merge fields, dynamic content, and copy testing |
| Choose the sequence type, length, timing and email mix | [sequence-strategy.md](references/sequence-strategy.md) | Core principles, sequence strategy, sequence types, email types by category |
| Write the emails, or answer how to implement them in an email tool | [writing-and-tools.md](references/writing-and-tools.md) | Email copy guidelines and tool integrations |

## Initial Assessment

**Check for product context first:** if the Brand Kit OS connector is available, pull the product, ICP, persona and voice context from it before asking anything. Without it the skill degrades to asking the user; to wire it, use the `environment-setup` skill and the plugin root's references/environment-setup.md. Do not ask for anything that context already answers.

Before creating a sequence, understand:

1. **Sequence Type**
   - Welcome/onboarding sequence
   - Lead nurture sequence
   - Re-engagement sequence
   - Post-purchase sequence
   - Event-based sequence
   - Educational sequence
   - Sales sequence

2. **Audience Context**
   - Who are they?
   - What triggered them into this sequence?
   - What do they already know/believe?
   - What's their current relationship with you?

3. **Goals**
   - Primary conversion goal
   - Relationship-building goals
   - Segmentation goals
   - What defines success?

---

## Output Format

### Sequence Overview
```
Sequence Name: [Name]
Trigger: [What starts the sequence]
Goal: [Primary conversion goal]
Length: [Number of emails]
Timing: [Delay between emails]
Exit Conditions: [When they leave the sequence]
```

### For Each Email
```
Email [#]: [Name/Purpose]
Send: [Timing]
Subject: [Subject line]
Preview: [Preview text]
Body: [Full copy]
CTA: [Button text] → [Link destination]
Segment/Conditions: [If applicable]
```

### Metrics Plan
What to measure and benchmarks

---

## Task-Specific Questions

1. What triggers entry to this sequence?
2. What's the primary goal/conversion action?
3. What do they already know about you?
4. What other emails are they receiving?
5. What's your current email performance?

---

## Related Skills

- **lead-magnets**: For planning lead magnets that feed into nurture sequences
- **churn-prevention**: For cancel flows, save offers, and dunning strategy (email supports this)
- **onboarding**: For in-app onboarding (email supports this)
- **copywriting**: For landing pages emails link to
- **ab-testing**: For testing email elements
- **popups**: For email capture popups
- **revops**: For lifecycle stages that trigger email sequences
