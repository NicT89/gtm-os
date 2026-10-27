---
name: pmf-five-gate-playbook
description: Run a product-fit exercise for any customer or project, including when the target audience is not yet known. Use when the user says "run the five gates", "product-market fit playbook", "find product fit", "reverse ICP", "validate the ICP", or is onboarding a customer and asking whether a product fits a segment. Scores segments on Pull, Prove, Pay, Use, Keep, builds the reverse ICP from the customer base, discovers buyer paths from evidence, and keeps an open-questions log.
---

# Product-fit playbook: five gates

Composable across customers and projects. Nothing in this skill names a buyer, a segment, a price or a product. Those are discovered per engagement and recorded in that engagement's own storage, never here.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## Inputs (gather what exists, log what does not)

Customer list, pricing and trial history, usage data, case studies, current stack, the customer's stated segments and their pivot-or-persist rule. Every missing input becomes a row in the engagement database (the `evidence-register` skill owns its schema). A gap is a question, not a reason to guess.

## Steps

1. **Reverse ICP first.** Pull the existing customer base: CRM first (`references/hubspot-reverse-icp.md` at the plugin root), then logos scraped from the customer's website if no CRM is reachable. Score each customer against the ICP card fields and find the highest-overlap cluster. Stated segments stay hypotheses until this runs. Split customers by any pricing or packaging change so price sensitivity is visible.
2. **Buyer discovery.** Find who actually buys, from customer records and interviews. For each won customer record four roles: the person who paid, the approver, the champion and the user. Define a buyer path only when two or more customers show the same pattern. Until then the path is `unknown`, and that is a valid output. Never import a buyer path from another engagement. A segment's absence of a role (no procurement team, no RevOps) is a fact to record, not a disqualifier, unless the customer's own win data says so.
3. **The gates, in order.** Thresholds are agreed with the customer; until agreed they read `TBD`, never a number from this skill.
   - Pull: the prospect replies and books.
   - Prove: a trial or proof works in their environment; capture feedback; test whether the features used support the price.
   - Pay: they buy at the offered price (conversion, cycle length, discounting).
   - Use: they reach the value actions (usage beyond logins when the product can show it).
   - Keep: they renew or expand.
4. **Interviews.** Within the first 30 days, 5 to 10 conversations with current paying customers, active users first. Ask who paid, who approved, at what spend and why. They confirm or kill the reverse-ICP hypotheses and fill ICP fields the data could not.
5. **Price-tier motion test.** Ask whether the buyer or approval path changes above a spend threshold. Treat it as a hypothesis, test it with the won-deal data, record the outcome.
6. **Messaging guardrail.** Any feature that only some tiers or segments can buy is only used in assets and outreach for the segments that can buy it. The engagement database records which feature maps to which segment.
7. **Score weekly** per segment on the five gates. Compare against the customer's stated pivot-or-persist rule; if none exists, propose one and log it as a question.
8. **Record.** Answers, sources and dates go in the engagement database; the report appendices are generated from it each version (`gtm-intelligence-report`).

## Output

Gate scorecard, reverse-ICP overlap report, updated ICP cards, buyer-path table (or `unknown`), open-questions list with answers and sources. The scorecard shape is in `references/gate-scorecard.md`.

## Rules

No number without a source, including thresholds. Estimates carry the word estimate and their basis. Person-neutral wording in anything the customer will read.
