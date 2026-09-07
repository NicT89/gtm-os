---
name: outreach-audit
description: Audit outreach sequences and personalization assets against the GTM OS quality bar. Use when the user says "audit the sequence", "run outreach-audit", "review my emails", "is this sequence ready", "check personalization quality", or before any cohort enrollment. Checks personalization depth, merge tokens, honesty rules, A/B discipline, and sequence configuration defects.
---

# Outreach Audit

Quality gate before any enrollment. Standard: show, don't tell. Every claim must be true for the specific recipient and grounded in captured research.

## Version check (run first, never block)

Fetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION, compare to the plugin root VERSION file, notify on mismatch, continue.

## The five-point email checklist

Every email in a sequence must contain: (1) one specific signal reference (exact role title and days open, or raise amount and month); (2) one research artifact (a JD tool, growth number, funding detail, or stack element); (3) one mirror line using the recipient's own words where posts exist; (4) the honest engine reveal where it fits the angle; (5) a soft CTA, with hard meeting asks reserved for the final touches or engaged contacts. Falsifiability test: if the email could be sent to a different company unchanged, it fails.

## Merge token rules

Contact custom fields merge as {{contact.Field Name}} with the object prefix; account fields as {{account.Field Name}}. Bare {{Field Name}} tokens will render as literal text: flag them. Verify tokens render by previewing against a fully-enriched contact before first send. The two standard personalization fields are {{contact.<prefix> Opener}} (email 1) and {{contact.<prefix> Blueprint}} (blueprint email), both multi-line text contact fields populated by the pipeline, where `<prefix>` is the deployment's `{INSTANCE_FIELD_PREFIX}`.

## Composition spec (what goes in those fields)

Opener: 1-2 sentences, at least one hard number or date, anchored to the recipient's strongest signal (hiring: role + posting age + JD detail; funding: raise + sales-team size + growth), their own words preferred when posts exist, no flattery, no adjectives about the company, no exclamation marks. Blueprint: 3-4 sentences structured Week 1 / Week 2 / Weeks 3-4, naming their ICP and at least one real tool or vertical, ending "documented for the hire" (hiring motion) or "proof before headcount" (funding motion).

**Anchor on persona, not on signal alone.** The signal says which facts exist; the persona says which of them the recipient actually owns. One open req is two different sentences: to the operating owner it is a role that has been open N days and a backlog that is already theirs, and to a founder it is a decision they funded and a function that is one person deep. Compose from the signal alone and you get copy that is factually perfect and addressed to the wrong job — which reads as a mail merge to the one reader who can tell. So resolve the persona before composing, and let the closer follow the motion the contact is enrolled in rather than the company's loudest signal. One account may legitimately carry more than one motion when it holds more than one persona; the invariant is one contact in one motion, never one motion per company.

**When posts are thin, borrow the company's voice before improvising.** "Their own words preferred" quietly assumes there are words. A contact with two posts, one of which is a four-word greeting, gives you nothing to mirror, and the failure mode is inventing a voice on their behalf. Fall back in order: the person's own posts; then the company's public voice as captured in the account research — how they name their users, the phrases they repeat, what they position themselves against; then plain and thin, with no mirror line at all. A thin opener built on real facts beats a fluent one built on a voice nobody used. Record which rung was used, so a later reader can tell a deliberate thin opener from a lazy one.

## Honesty rules

Never claim a canned video is custom. If the video is general, the personalization must live in the email text and the video framed as "why I work this way." Never fabricate post references; inactive posters get a recorded alternate angle instead. Never state retainer pricing in cold outreach; anchor against the loaded cost of the unfilled role.

## A/B discipline

One variable per test, angles before cosmetics. Variants live as multiple touches on the same step (max 3). Judge on positive reply rate and meetings, not opens (Apple Mail Privacy Protection inflates opens by prefetching tracking pixels; corporate link scanners can inflate clicks). Minimum ~100 sends per variant before calling a winner. Motions are segments, never cross-compared: hiring and funding cohorts each get their own A/B pairs. Log every test's hypothesis and result in the changelog.

## Sequence configuration checks (defects found in production, check every new sequence)

1. Product profiles: verify the correct Context Center product is attached (API-created sequences may auto-attach the wrong one).
2. Exclusion stages: verify excluded account and contact stages are set (API-created sequences start empty, which lets replied or do-not-contact stages re-enroll).
3. Naming: Claude-created sequences carry "[Claude]" in the name; human-managed sequences are never edited by Claude.
4. Sender: confirm the sending mailbox matches the pitch domain, and the signature carries a physical address with opt-out enabled on auto emails.
5. Segment fit: contacts must match the sequence's signal (never enroll a no-jobs company in a hiring-signal sequence or a founder in hiring-anchored copy).
6. Manual steps: LinkedIn and blueprint-email steps carry rep notes with the required prep, and the human can service the resulting task volume same-day (cap cohort sizes accordingly).

## Output format

Deliver a verdict per sequence: SHIP / SHIP AFTER FIXES / BLOCKED, with each finding tagged by severity, the specific fix, and which checklist item it violates. Append findings to the local audit log.
