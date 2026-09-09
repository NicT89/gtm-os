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

Opener: three to four sentences in four named beats (see below), at least one hard number or date, anchored to the recipient's strongest signal (hiring: role + posting age + JD detail; funding: raise + sales-team size + growth), their own words preferred when posts exist, no flattery, no adjectives about the company, no exclamation marks. Blueprint: 3-4 sentences structured Week 1 / Week 2 / Weeks 3-4, naming their ICP and at least one real tool or vertical, ending "documented for the hire" (hiring motion) or "proof before headcount" (funding motion).

**The opener has four beats, and the first one is where openers usually fail.**

1. **The arc, and what it means.** Where this person came from, what changed, and what they
   consequently own now. The consequence clause is the beat, not the history: "came into the
   company in September 2025 after five years running revenue operations elsewhere, **and has
   been rebuilding the function since**" is an arc, while "moved into the Director seat in
   April 2026, coming from digital product and revenue operations before that" is a CV
   extract wearing an arc's clothes. Test it by deleting the consequence clause: if the
   sentence still tells you something about their situation today, the consequence was doing
   no work and the beat has not been written yet.
2. **The reference, named.** The specific artifact you read, named so they can go and check
   it: "reading the GTM Engineer posting your team has open". A reference the reader cannot
   locate is indistinguishable from a guess.
3. **The observation.** What that reference shows that is not obvious from it. A tension, a
   shape, an implication. "That reads as a build seat rather than a support seat."
4. **The question.** Answerable in one line, about how the thing works for them today.

**Every beat traces to a source you could name inside the sentence.** Their own posts,
their own job posting, their own filing, their own public career history. Enrichment
estimates and vendor summaries are orientation, never quotable.

**Never assert a relationship, a motive, or a causation you inferred.** Two people
overlapping at a prior employer is a fact; one of them hiring the other is a story you made
up. State the facts that are checkable and let the question carry the implication.

**The falsifiability test has a second half for openers.** The blueprint's version is
whether it could be sent to a different COMPANY unchanged. An opener must also survive being
sent to a different PERSON at the same company: swap the recipient for their colleague one
seat over, and if it still reads correctly, beat 1 is missing and what you have is a company
fact with a name on top.

**The opener ends in a question, and the question is the point.** A first touch is discovery, not a pitch: the goal is to learn enough to build a proposal that fits, not to assert one before you know what they need. So the opener earns its place with a hard fact and then spends it on a genuine question about how the thing works *for them today* — what their scoring actually keys on, where their attribution stops being trustworthy, which part of the cleanup is blocked. A closing line that states a conclusion instead ("that is a build, and it sits in the queue until someone starts") tells the reader something they already know, gives them nothing to correct, and leaves no opening to reply into. **If the last sentence could be true without the recipient existing, it is the wrong last sentence.**

Two rules that follow:

- **Ask about the present, not the future.** "How does X work today" invites an answer; "here is what X should be" invites a decision they are not ready to make. Questions about current state are cheap for them to answer and are the only way to find out whether the proposal you would have pitched was right.
- **The blueprint is a hypothesis offered for correction, not a plan delivered.** It is written from outside their company and parts of it are wrong by construction. Say so, and close it by asking which part is wrong — a reader who reorders your weeks has told you more than one who agrees.

**The standard the whole message is judged against: it must read as relevant, evidently researched, and offering help.** Those three, in that order, and they are not style notes — they are what separates a message someone answers from one that looks like every other one in the inbox.

- **Relevant** means it is about something true of them this month, not this year. A fact from their own last two weeks beats a better fact from six months ago.
- **Evidently researched** means the reader can tell work happened without being told it did. Quote what they wrote, name the tool their posting names, cite the number they published. Never *claim* to have researched them; the evidence does that or nothing does.
- **Offering help** means the message costs them nothing to answer. Ask about their situation, offer the plan for correction, and do not ask for time in a first touch. A message that asks for a meeting before it has earned one converts the research into a transaction, which is exactly what the reader is filtering for.

The falsifiability test still governs everything: **if the message could be sent to a different company unchanged, it fails.** And its sharper form for the closing line — if the last sentence could be true without the recipient existing, it is the wrong last sentence.

**Align to the person, not only to the company.** Persona decides which facts land, and the same fact means different things by seat. An open requisition for a lead-routing role is, to a **VP of Sales**, the reason his reps are working leads that were scored badly — he feels it downstream. To the **Marketing Director who owns the function and wrote the posting**, it is her own backlog and her own governance debt. To a **founder with no GTM leader**, it is a decision they funded and a function running thin. Before composing, name what this person is measured on and what breaks in their week, and write the question about that. A message aligned to the company and not the seat reads as researched-but-generic, which is worse than brief, because it proves the research happened and still missed them.

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
