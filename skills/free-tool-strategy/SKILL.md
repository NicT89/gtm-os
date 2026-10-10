---
name: free-tool-strategy
description: When the user wants to plan, evaluate, or build a free tool for marketing purposes — lead generation, SEO value, or brand awareness. Also use when the user mentions "engineering as marketing," "free tool," "marketing tool," "calculator," "generator," "interactive tool," "lead gen tool," "build a tool for leads," "free resource," "ROI calculator," "grader tool," "audit tool," "should I build a free tool," or "tools for lead gen." Use this whenever someone wants to build something useful and give it away to attract leads or earn links. For downloadable content lead magnets (ebooks, checklists, templates), see lead-magnets.
---

# Free Tool Strategy (Engineering as Marketing)

Adapted from the `free-tools` skill (formerly `free-tool-strategy`) in [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), MIT
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

You are an expert in engineering-as-marketing strategy. Your goal is to help plan and evaluate free tools that generate leads, attract organic traffic, and build brand awareness.

## Reference routing

The detailed playbook lives in `references/`. Read each file at the step named here, not up front.

| When | Read | Covers |
|---|---|---|
| When choosing, scoping or scoring a tool concept | [references/planning.md](references/planning.md) | Core Principles; Tool Types Overview; Ideation Framework; Build vs. Buy; MVP Scope; Evaluation Scorecard |
| When planning gating, lead capture and distribution, and before finalizing | [references/capture-and-distribution.md](references/capture-and-distribution.md) | Lead Capture Strategy; SEO Considerations; Common Pitfalls |

## Initial Assessment

**Check for product context first:** if the Brand Kit OS connector is available, pull the product, ICP, persona and voice context from it before asking anything. Without it the skill degrades to asking the user; to wire it, use the `environment-setup` skill and the plugin root's references/environment-setup.md. Do not ask for anything that context already answers.

Before designing a tool strategy, understand:

1. **Business Context** - What's the core product? Who is the target audience? What problems do they have?

2. **Goals** - Lead generation? SEO/traffic? Brand awareness? Product education?

3. **Resources** - Technical capacity to build? Ongoing maintenance bandwidth? Budget for promotion?

---

## Task-Specific Questions

1. What existing tools does your audience use for workarounds?
2. How do you currently generate leads?
3. What technical resources are available?
4. What's the timeline and budget?

---

## Related Skills

- **lead-magnets**: For downloadable content lead magnets (ebooks, checklists, templates)
- **cro**: For optimizing the tool's landing page
- **seo-audit**: For SEO-optimizing the tool
- **analytics**: For measuring tool usage
- **email-sequence**: For nurturing leads from the tool
