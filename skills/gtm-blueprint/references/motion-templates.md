# GTM Motion Templates

Select ONE motion per blueprint using the classification rules in SKILL.md — one of the five templates below, or a **custom motion** (see the Custom motion section) when the company fits none of them cleanly. Each template defines what Weeks 1, 2, and 3-4 emphasize and the closer line. The emphases exist because the plan must describe what a GTM engineer would actually build first at THAT kind of company; a PLG company's pipeline hides in usage data, an enterprise seller's pipeline hides in a finite account universe. Getting the emphasis wrong makes the plan feel templated, which defeats its purpose. The five are the common shapes, not a closed list: forcing the nearest preset onto a company it does not fit produces exactly the templated feel the skill exists to avoid.

## Output format (all motions)

The intro line ("I looked closely at what {Company} is building...") lives in the EMAIL TEMPLATE, not the field. The field contains only:

```
- Week 1: [one sentence, sourcing/signal emphasis]
- Week 2: [one sentence, outreach/conversion emphasis]
- Weeks 3-4: [one sentence, reporting/pipeline emphasis]

[Closer line]
```

Multi-line plain text with hyphen bullets. Verify the CRM's email renderer preserves line breaks with a single-contact preview before any batch write.

## PLG / dev-first

Signals: free trial or self-serve signup, open-source adoption, docs-heavy site, community channels (GitHub, Discord).
- Week 1: Surface the commercial intent hiding in usage: signups, GitHub activity, community, so buyers self-identify.
- Week 2: Convert adoption into qualified conversations without hiring a sales floor.
- Weeks 3-4: Usage-to-revenue reporting: who is deploying, who is scaling, who is ready to pay.
- Closer: "Proof before headcount: validate the motion first, then hire into a working system."

## Enterprise sales-led

Signals: book-a-call primary CTA, high ACV markers, compliance-sensitive buyers, named-logo customer pages.
- Week 1: Named-account sourcing and scoring across the defined buyer universe.
- Week 2: Multi-stakeholder outreach automation and speed-to-lead on inbound.
- Weeks 3-4: Pipeline stages and forecasting built for long cycles.
- Closer: "Documented for the team as it grows: the system outlives any one seller."

## Founder-led early

Signals: under ~20 employees, no sales function, founders visibly running deals.
- Week 1: Signal sourcing so founder time stops being the pipeline.
- Week 2: Outreach automation running off the founder's calendar, not on it.
- Weeks 3-4: Simple, trustworthy reporting sized for a seed-stage board.
- Closer: "Proof before headcount: validate the motion first, then hire into a working system."

## Channel / partner-led

Signals: reseller programs, integration marketplaces, "partners" in primary nav, delivery through firms.
- Week 1: Partner and end-customer signal mapping across the ecosystem.
- Week 2: Co-motion outreach with clean handoff data both directions.
- Weeks 3-4: Partner-sourced pipeline attribution so channel investment is measurable.
- Closer: "Documented for partner ops: repeatable beats relationship-dependent."

## Regulated vertical

Signals: buyers in healthcare, finance, defense, or government; procurement-shaped selling.
- Week 1: Finite-universe mapping: the systems, programs, or regions that can actually buy.
- Week 2: Compliance-aware, domain-literate outreach that respects how these buyers evaluate.
- Weeks 3-4: Program- or cycle-shaped pipeline reporting.
- Closer: "Systematic beats heroic: the whole buyer universe, worked methodically."

## Custom motion (when none of the five fit)

The five templates are the common shapes, not the whole space. Some companies do not map
cleanly onto any of them: a usage-based infrastructure company that also runs a top-down
enterprise motion, a community-led company whose pipeline is neither self-serve signups
nor named accounts, a services firm selling outcomes rather than seats, a marketplace with
supply and demand sides that source differently. Do NOT force one of the five onto a
company it does not fit — a preset worn by the wrong company reads templated to the one
reader who knows better, the recipient, which is the exact failure this skill exists to
prevent.

When no preset fits, compose a custom motion from the same framework the five are built
on. The framework, not the labels, is what makes a motion trustworthy. Answer these four
questions from the company's real business, and the answers ARE the Week 1 / Week 2 /
Weeks 3-4 / closer lines:

1. **Where does THIS company's pipeline actually hide?** That is Week 1. PLG's hides in
   usage; enterprise's in a finite account list. A custom motion's hides somewhere you
   name from their reality — a partner ecosystem, a specific data signal, a regulatory or
   procurement calendar, an existing install base, a community. Name the specific source,
   not a generic one.
2. **What is the shortest honest path from that signal to a qualified conversation?** That
   is Week 2. It has to fit how this buyer actually evaluates and buys, not how it would
   be convenient for them to.
3. **What does trustworthy reporting look like at their stage and for their buyer?** That
   is Weeks 3-4 — the pipeline view a person inside THIS company would actually trust to
   make a decision, sized for their stage.
4. **What is the closer** — the one-line reason the motion is right for them now? Write it
   from their situation, in the register of the five closers above (proof before headcount;
   documented for the team; systematic beats heroic), not as a slogan.

The output shape is identical to the presets: hyphen-bullet Week 1 / Week 2 / Weeks 3-4
lines plus a closer, in the format above. Every rule that binds the presets binds a custom
motion too — cite at least one real stack tool and one hard number, name the actual buyer,
no flattery, no fabrication, and the falsifiability test: if the plan could be sent to a
different company unchanged, it has failed. A custom motion is a different emphasis, never
a lower standard.

The composed field keeps the exact shape above — the three week lines and the closer,
nothing else — so a custom motion never writes a label into it. Surface the choice to the
human instead: when presenting the recommendation (SKILL.md Step 3), name the custom
motion (`Custom motion: <one phrase>`) and its reasoning, and compose only on the
operator's selection. Custom is the escape hatch for genuine misfits, chosen deliberately,
not the default. If, while composing, the company turns out to fit a preset after all, do
not switch silently — surface the better-fitting preset with its evidence and switch only
on the operator's confirmation.

## Modifiers

- B2C: do not produce a cold-outbound blueprint. Propose partnership, retail, or creator-channel framings, or flag the fit question to the human.
- Multi-model companies (primary product for one persona plus a widget/API/marketplace channel for another): one blueprint per distribution model; each contact receives the model matching their role.
- Every blueprint must cite at least one real tool from the target's stack and at least one hard number or named fact from the gathered context. If it could be sent to a different company unchanged, it fails.
- ABSOLUTE DATES ONLY (rule from a caught defect, 2026-08-06): never write relative time references ("this month", "recently", "last week") into any composed field. Sends happen days or weeks after composition, so relative phrasing goes stale or wrong. Write "in July", "their April raise". Always compute posting and funding ages relative to the SEND date, not the composition date.
- INVESTOR DATA IS OFTEN INCOMPLETE (caught 2026-08-06): CBI and Apollo investor lists can miss round participants, especially angels; seed rounds routinely include many firms plus named angels. Before flagging a composed investor mention as an error, check primary sources (the founder's own funding announcement post). Conversely, only assert lead-investor status when the data explicitly says so.
