# Changelog

All notable changes to the GTM OS plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version recorded here must always match the `VERSION` file and the `version`
field in `.claude-plugin/plugin.json`. See [MAINTAINING.md](MAINTAINING.md) for the
release process. Release notes are sourced verbatim from the matching `## [x.y.z]`
section of this file — see MAINTAINING.md for how that extraction works.

## [Unreleased]

## [1.9.4] - 2026-09-10

The rest of the 1.9.2 contract audit, as one release. Every finding here is the same defect
wearing different clothes: a document carried a COPY of something another document owns, the
copy drifted, and following the copy did the wrong thing. The fix in nearly every case is to
delete the copy and point at the source.

### Fixed

- **`field_gate.py` accepted a `--motion` argument it never read.** It was echoed into the
  verdict and nothing branched on it, so a hiring record with no `GTM Jobs w/ URL`, no
  `JD Summary` and no `Role Archetypes` — all three required by SKILL.md — exited 0 = PASS.
  The argument being MANDATORY is what hid this: a required flag reads as a required check.
  The gate now checks the account fields the signal type calls for, and `--signal-type` is
  the flag's name (`--motion` still works, with a notice).
- **`min_hard_facts` sat in the gate config with no reader**, so "never compose from fewer
  than three hard facts" was enforced by nothing. The gate now counts populated
  FACT-BEARING SOURCES and names them in the verdict. Stated plainly in the docstring and
  the verdict's own note: a source count is a necessary condition for three hard facts and
  never a sufficient one, because no script can tell whether a populated field yields a
  quotable number. Pre-send review is still where a human reads the facts.
- **A malformed `--config` raised a traceback instead of exiting 2**, so a typo in the path
  read as a crash inside the gate.
- **The word "motion" named two different things**, and the collision wrote wrong copy. The
  two axes are now defined once, in `references/signals-doctrine.md`: **signal type**
  (`hiring`/`funding`) is what sourced the account and anchors the OPENER; **GTM motion** is
  the target's own go-to-market shape, one of the five templates, and it decides the plan and
  the CLOSER. They are independent.
- **`outreach-audit` keyed the blueprint's closer on the signal type**, offering
  "documented for the hire" (a string that exists in no motion template) or "proof before
  headcount" (a real closer, but PLG's and founder-led's). `gtm-blueprint`'s quality gate
  checks the closer against the recorded MOTION, so following the authoritative composition
  spec produced blueprints that failed the gate. It now points at `motion-templates.md`,
  which is the only place closers are defined.
- **`examples/blueprint-hiring.md` — the format anchor step 4 output is copied from — was
  filed under the enterprise sales-led motion and ended "Documented for the hire."** It
  would have failed the quality gate, and everything copied from it inherited that.
- **`gtm-signal-scan` restated the signal taxonomy and had lost four of the twelve rows**,
  including signal 6, GTM persona presence/absence, which the doctrine marks ALWAYS ON. A
  partial copy of a taxonomy is worse than a pointer, because it reads complete.
- **The same skill restated the reachability tiers and had lost two flags**: `likely` from
  T3 and `unverified` from T4. Dropping `unverified` from T4 is the expensive one — it reads
  as spendable, so every `unverified` candidate bought a match credit to learn the address
  was never sendable, which is the one spend that step exists to prevent.
- **`scrape-linkedin-posts` Step 6 read as pushing raw JSON into the Apollo posts field**,
  while the field dictionary specifies a pipe-delimited digest, one post per line, with an
  excerpt cap and a window. Both the Apollo-side summarize step and the blueprint composer
  parse lines, so they would get one unparseable blob. The JSON is now labeled as the
  Airtable intermediate, and the field format is read from the dictionary rather than
  restated.
- **The same step had no zero-post sentinel.** `has_content: false` describes the
  intermediate and was never something the field could carry, so a silent-empty scrape wrote
  an empty field — which means "not scraped" downstream. That is the failure that
  permanently deprecated the "View professional posts" field, inherited back by omission.
  Retry once, then write the dictionary's sentinel.
- **`JD Summary` and `GTM Jobs w/ URL` have TWO populators and the dictionary named one.**
  `jd-intake` writes both when the CRM-side AI field runs have not, and must reconcile
  rather than overwrite when they have. A second writer to a field the engine reads was
  invisible in the dictionary — exactly what `CLAUDE.md` says to audit separately.
- **`gap-closer` said it needs "three" keys and then listed four**, with the fourth in
  parentheses. `{AIRTABLE_TBL_VAULT_ENTITIES}` is not optional: an unlinked fact is not
  retrievable by entity, which is the only way anything reads it.
- **`CBI Mosaic Score` was documented as both 0-1000 and 1-1000**, and the file separately
  reserves 0 as the attempted-but-empty sentinel. The 0-1000 spelling made a real score of
  zero indistinguishable from a failed retrieval.
- **Three paragraphs of prose had accumulated between rows of the Vault's Facts table**,
  which in markdown ends the table and re-opens a header-less one. The rendered schema was
  missing `Entity`, `Run` and `Supersedes` — the two links that make a fact retrievable and
  the one that makes the supersede protocol possible. Every row was present in the source,
  which is why nobody caught it; the render is what a person building the base reads.
- **The exclusion-list rule read as though the engine kept the list.** It does not and must
  never start one: the operator's CRM already holds it, and a second list is a second thing
  to be out of date.

### Added

- **`tests/test_closer_contract.py`** parses the closers out of `motion-templates.md` and
  asserts the example's closer is the one its RECORDED MOTION has. Falsified by restoring
  the old closer.
- **`tests/test_markdown_tables_intact.py`** asserts no table in the repo is split by prose,
  by requiring a separator line as the second line of every run of table rows. It carries
  its own positive and negative cases so a broken detector cannot pass silently. Zero
  suspect blocks repo-wide after the Facts-table repair.
- **Eleven new `field_gate.py` tests**, covering the account fields per signal type and the
  fact floor. Falsified by reverting both checks: five of twenty fail.

### Open, and NOT fixed here

- **The `M1`-`M5` routing codes in `signals-doctrine.md` have no legend anywhere in this
  repo.** Deliberately not invented: a plausible-reading mapping is precisely what
  `CLAUDE.md` prohibits, and a wrong routing legend would send whole cohorts into the wrong
  motion while looking authoritative. The table now says so and directs readers to the
  `Action` column, which is safe to act on. Closing it needs the five codes written out, or
  replaced by the motion names if that is what they were shorthand for.
- **`gtm-signal-scan`'s scoring line still reads "archetype/motion fit 25".** At scan time
  the target's GTM motion has not been classified yet — that happens in `gtm-blueprint`
  Step 3 — so this cannot mean the five templates, and it is left alone rather than guessed
  at.

## [1.9.3] - 2026-09-10

One ordering bug, fixed with the check that could have caught it. It was the only finding
in the 1.9.2 audit that silently produced wrong data rather than confusing a reader.

### Fixed

- **`gtm-signal-scan` scraped LinkedIn posts one step too late, so the posts summary was
  written from an empty field and reported success.** `field-provenance.md` requires the
  posts field to be filled by `scrape-linkedin-posts` BEFORE the contact joins the
  enrichment trigger list, because Apollo's summarize-posts step fires on list membership
  and reads that field. The skill added contacts to the list in Step 5 and scraped in
  Step 6. Every required thing was done, and two of them in the wrong order. The scrape is
  now sub-step 2 of Step 5, between the create and the list-add; Step 6 verifies the
  digests it used to fetch, and says what to do when a summary is empty but the digest is
  not. Nothing about the failure was visible downstream: a contact who posts weekly and one
  who has never posted produced byte-identical fields.

### Added

- **`tests/test_posts_before_list_add.py` asserts the order, not the presence.** Every
  other check in this repo validates that something exists; this one compares positions
  within Step 5 and re-reads the rule at its source in `field-provenance.md`, so it fails
  if either the procedure or the rule moves. Falsified by swapping the two sub-steps back:
  two of its four assertions fail.
- **A fifth defect class in `CLAUDE.md`:** a check that only sees presence cannot see
  order. Named because the repo's existing doctrine covers checks that cannot fail, and
  this was a check that could fail and had nothing to look at.

## [1.9.2] - 2026-09-09

Contract mismatches found by an audit that read every document against every other. Six of
the eighteen findings are fixed here, chosen because following the wrong copy causes harm
rather than confusion. The rest are listed in the PR and scheduled.

### Fixed

- **The `Confidence` vocabulary existed in three incompatible versions, one of them
  executable.** The live Vault select carries `verified, high, medium, low, inferred`.
  `research-vault.md` documented `high, medium, low`. `scripts/gap_ledger.py` enforced
  `verified, medium, inferred` and **rejected the other two**, so it exited 2 on most facts
  in a populated Vault. All three now agree on the live five, with the strengths stated:
  `verified` and `high` both mean a primary source says it and are the only two quotable or
  writable without asking; `medium` is a vendor estimate for sizing and routing; `low` is a
  weak or self-reported claim; `inferred` is reasoned rather than sourced.
- **`signals-doctrine.md` banned catch-all enrollment outright**, while the skill, CLAUDE.md,
  the README and the PR template all treat it as one of the four named human gates. An agent
  following the doctrine automates past a registered gate, which CLAUDE.md forbids in the
  same breath. The doctrine now defers to `gtm-signal-scan` Step 5 and says exclusion is a
  default rather than a ban.
- **The version-bump procedure contradicted itself in four places.** `MAINTAINING.md` said
  both "auto-synced, do not hand-edit" and "the PR bumps both"; the PR template's prose said
  bump VERSION alone while its own checklist ran `check_version_sync.py`. Anyone following
  the stale copies shipped a PR that fails CI every time. All copies now say: bump both, in
  the same commit.
- **"Diagnosis is free" was wrong, and it was in five places including the pinned Get Started
  block.** The per-connector reference says plainly that the Firecrawl probe performs a scrape
  and spends a credit, and that it must not be described as free. Every other copy asserted
  the whole diagnosis was free, so the skill spent unannounced in the one place a new user
  meets the engine first, which is the credit gate failing at first contact.
- **`CLAUDE.md` called Airtable and Apify optional and omitted Firecrawl entirely**, while
  three other documents call all four required, conditionally.
- **`Tech Stack Details` was the gap ledger's flagship example and existed nowhere.** No row
  in the field dictionary, no config key, so an agent told to fill it had no field ID and is
  forbidden from guessing one. It now has both.

## [1.9.1] - 2026-09-09

One release of corrections, not four. Everything here is a patch: an operator who upgrades
runs the same commands and asks for the same things, and gets a better answer. **One action
on upgrade**, called out below.

### Fixed

- **The versioning rule was producing version inflation, so it is rewritten.** It said any
  additive release was a minor, which took this repo from 1.7 to 1.11 in two days for what
  was one release of corrections. The test is now whether the OPERATOR'S CAPABILITY changed,
  not whether a file was added: a reference, a rule, a validator, or a script the engine
  calls on its own is a **patch**, and minor is reserved for a new skill or something an
  operator can newly ask for. A required upgrade action no longer forces a minor either; it
  is a communication problem, solved by saying so loudly.

  `MAINTAINING.md` also now says to group related work into ONE release. One PR per concern
  is about keeping a diff reviewable, not about splitting a coherent release into fragments
  that must merge in a fixed order.
- **"Do not invent numbers" is stated as a rule with no exceptions, and extended.** A
  derived number is invented unless its inputs are sourced. Observed 2026-09-09 in a live
  workspace: a draft asserted a role was "a $130K-$180K hire" costing "$13K-$19K per month",
  from a posting that publishes no compensation at all. The range was plausible, the
  arithmetic on it was sound, and the whole thing was fabricated. Plausibility is what makes
  this class dangerous. The rule now also binds anything that writes into a field the engine
  reads, including plays configured outside this repo, because a composed field is only as
  trustworthy as the least careful thing with write access to it.
- **The opener length contract existed in two places and drifted.**
  `skills/outreach-audit/SKILL.md` is now declared the authoritative composition spec and
  owns length, structure and the falsifiability tests; `field-provenance.md` points at it
  and deliberately states neither, because when it did the two disagreed for a release.
- **The review loop claimed a review that often does not happen.** CodeRabbit runs on the
  free tier here and is not being upgraded. When its limit is reached it leaves zero findings
  and the status check still reports SUCCESS, which is indistinguishable from a clean review.
  The docs now say how to tell the difference (check for the completion signal, never infer
  from absent findings) and to state plainly when no review happened.
- **Catch-all enrollment was a gate no list of gates included.** `gtm-signal-scan` Step 5
  already required the operator to choose exclusion or enrollment, record it, and arm a
  bounce threshold, but it was prose and was never registered. The named set is now four:
  ICP sign-off, credit spend, catch-all enrollment policy, pre-send review.
- **The propose queue had no home.** The write/propose/skip split said to "surface the
  propose queue once" and never said where it persists, so it lived in a chat transcript and
  died with it. Proposals are now ordinary Vault facts at their real confidence.

### Added

- **`scripts/run_cost.py`.** The Vault's `Cost Summary` has had a fixed format since the
  Vault existed and nothing produced it, so "state the total before spending" and "a run
  projected to exceed its cap STOPS and asks" both depended on someone doing arithmetic in
  their head. Returns the tally, the summary line, and a non-zero exit the moment a meter is
  over cap. Units are per-meter and never summed; `Status` is `final` only for a completed
  run.
- **Every Vault fact is four things: title, description, content, reference.** The Facts
  table gains a **`Description`** field. A reference is required for anything sourced from
  the internet, which is what makes the composition rules work: only a fact the recipient
  could check may be quoted.

  **On upgrade:** add a long-text field named `Description` to your Vault's Facts table.
  Existing facts stay valid without it.
- **The opener has four named beats**, and the first is where openers fail: the arc (where
  they came from, what changed, **what they consequently own now**), the reference named so
  they can check it, the observation it makes possible, and the question. Beat 1 is tested by
  deleting its consequence clause; if the sentence still says something about their situation,
  the clause was decorative.

  **The falsifiability test gains a second half for openers.** The blueprint asks whether it
  could go to a different COMPANY unchanged. An opener must also survive going to a different
  PERSON at the same company. Observed 2026-09-09: three openers for one account all passed
  the old test and only one passed the new one.
- **Never assert a relationship, motive, or causation you inferred.** Two people overlapping
  at a prior employer is a fact; one hiring the other is a story.

## [1.9.0] - 2026-09-08

Additive. Nothing changes for an install that does not use the new step, and there is no
configuration to add. This release changes the engine's posture: runs now repair the
workspace they read from instead of only consuming it.

### Added

- **The gap ledger, and a gate on writing back.** The engine reads far more than it writes.
  A run learns a company's tool stack, spends one fact from it, and lets the rest evaporate;
  the next run pays for the same research again. Observed 2026-09-07: a run held eleven
  verified tools, used one, and dropped ten, into a field that already existed and was empty.

  Gaps are now work to do rather than findings to report. The timing is the whole argument:
  **during a run the data is already in hand and writing it costs nothing**, while a week
  later the same field costs a full re-research.

  What makes that safe is `scripts/gap_ledger.py`. A bad blueprint gets caught because a
  person reads it before it sends; a bad field write is caught by nothing and propagates
  into every later run, with no way to tell a written fact from a researched one. So every
  write is gated on how well the fact is known and on who put the current value there:

  | field state \ confidence | verified | estimate | inferred |
  |---|---|---|---|
  | empty | write | write only if the field accepts estimates | propose |
  | stale (machine) | write | propose | propose |
  | human-entered | propose | propose | propose |
  | filled and fresh | skip | skip | skip |

  Two rules carry it. **A human's value is never overwritten** whatever the confidence and
  however old it is, because age does not demote a person's decision to a machine's, though
  a blank a person left is a gap rather than a choice. **An inferred fact is never written**,
  which is the `organization_revenue: 0.0` defect: written once, an absent value becomes
  indistinguishable from a researched zero forever, and the falsifiability test cannot catch
  it because the number came from a tool.

  `0`, `0.0` and `false` are values, not gaps. Only null, empty strings, and empty
  collections are absence.

  **Unknown provenance is not machine provenance.** A value whose author was never recorded
  might be hand-typed, so it is protected exactly as a human's is; only an explicitly
  machine-written value may be refreshed on age. Caught in review before release: without
  this, the never-overwrite-a-human rule was defeated by an ABSENT attribution rather than a
  wrong one, which is the harder failure to notice. An empty field needs no such protection.

  **Only CRM-backed modes have a write queue.** `gtm-blueprint`'s ad hoc proposal mode has no
  record to write to, so it produces a propose list and nothing else.
- **`references/gap-ledger.md`**, the doctrine: why during the run, what the gate protects,
  what a skill does with each queue, and where the gaps usually are (the CRM first, then the
  seller's own brand kit, then the Vault).
- **`gtm-blueprint` Step 5 now writes back what the run learned**, not only what it composed.
  It writes the write queue without asking and surfaces the propose queue once, at the end,
  as a list rather than as a series of interruptions, then records what was filled and what
  was declined in the run's Notes.

### Changed

- **`tests/test_gap_ledger.py` asserts the decision table cell by cell** rather than spot
  checking it, and carries a `MutationCoverage` class that reintroduces each of the four
  protections as a defect in an in-memory copy and asserts the guarantee breaks. Per the
  convention added in 1.7.1, a new check earns trust by being broken on purpose and observed
  failing, and the claim now has an artifact in the repo rather than a number in a changelog.
- **`.coderabbit.yaml` corrected on two counts**, both raised by a review working from
  outdated repo context: the script convention is prose-by-default with a `--json` flag,
  which is what every script here actually does, and since 1.7.1 a release PR bumps both
  `VERSION` and the plugin manifest rather than leaving the manifest to the workflow.

### Changed

- **The opener now ends in a question, because the first touch is discovery and not a
  pitch.** The spec produced openers that stated a conclusion and stopped — one live example
  closed "that is a build, and it sits in the queue until someone starts", which tells the
  reader something they already know, gives them nothing to correct, and leaves nowhere to
  reply. The rule added: spend the hard fact, then ask how the thing actually works for them
  today, and if the last sentence could be true without the recipient existing, it is the
  wrong last sentence. The blueprint follows the same turn — it is written from outside the
  company, parts of it are wrong by construction, so it says so and asks which part, since a
  reader who reorders the weeks has told you more than one who agrees.
- **Composition aligns to the seat, not only to the company.** The same open requisition
  means three different things: to a VP of Sales it is reps working badly scored leads, to
  the Marketing Director who wrote the posting it is her own governance debt, to a founder
  with no GTM leader it is a decision they funded. The spec now requires naming what the
  person is measured on and what breaks in their week before composing, because a message
  aligned to the company and not the seat reads as researched-but-generic — worse than
  brief, since it proves the research happened and still missed them.

## [1.8.0] - 2026-09-08

Additive, with **one action on upgrade** (see the Field Key note below). Everything here came
out of running the engine against live companies, where a single job description returned
more usable fact than every inferred data source combined.

### Added

- **A11: the target's internal tool stack.** Every blueprint must cite one real tool the
  target runs, and the taxonomy had nowhere to put one. `A6` is the *product's* integration
  ecosystem, which is a different thing, so a verified stack had to be filed under `other`
  and stopped being retrievable by key. A11 is now that home.

  **On upgrade:** add `A11` as an option on the Field Key select in your Vault's Facts and
  Questions tables. Without it, A11 facts fall to `other`.
- **A source waterfall for finding that stack**, in `references/scraping-playbook.md`,
  ranked by whether a result may be QUOTED to the prospect rather than by convenience: the
  company's own job descriptions first, then Clay, then ZoomInfo, and inferred
  technographics last and never citable. Job descriptions are the best source by a wide
  margin. One GTM Engineer posting returned eleven named tools, the role's reporting line,
  its KPI, and the fact that the company was hiring the exact capability being sold. Read
  every open role, not only the GTM ones. **Absence is a finding too**: zero postings closes
  the route and, alongside a negative headcount trend, usually means a freeze, which changes
  who the buyer is.
- **`gtm-blueprint` now pulls job postings on every account, whatever the motion.** They
  were treated as a hiring-motion input. They are the highest-yield single source in the
  engine.

### Changed

- **Only a `verified` fact may be quoted to a prospect.** The Vault's Confidence field
  already carried the vocabulary and nothing depended on it, so a `low`-confidence estimate
  could be composed into outreach as a hard number. `verified` now means a primary source
  states it. An enrichment vendor's estimate sizes and routes an account; it does not go in
  the field. The test is one question: if the recipient asked "where did you get that?",
  is the answer a link to something they wrote?

  This closes a gap the falsifiability test cannot: a number that came from a tool reads
  exactly like a number that came from research. Observed 2026-09-07 — inferred
  technographics named two tools for one company, one right and one absent from that
  company's own job description, which named eleven.
- **`gtm-blueprint` Step 2 preflights the seller source before reading the target.** A
  stale or self-contradicting brand kit is worse than a bad target fact, because it goes
  into every blueprint rather than one. On a mismatch the skill stops and asks which is
  current instead of picking. Observed 2026-09-07: a brand kit's description said web
  development agency while its own product list described an AI implementation retainer.

### Added

- **People search is run twice, by title and by seniority, and read together.** Each misses
  the other's blind spot and they fail in opposite directions. A title search does not match
  `Founding <function>` staff at all: on a live run it returned zero people at two companies
  that both have go-to-market staff, titled "Founding Technical Account Executive",
  "Founding Growth" and "Founding Account Executive", and one of those companies was marked
  as having no GTM employee on that evidence. A seniority search over-reports the same
  people, because the provider reads "Founding" as founder-level: five founder-seniority
  results at one company, every one an individual contributor. The rule is now explicit —
  treat `Founding <anything commercial>` as an IC, never conclude "no GTM staff" from titles
  alone, and generally **not found is not the same as absent**: vary the query shape before
  deciding a value does not exist.

### Fixed

- **The documented contact-creation step told you to set `label_names`, and that silently
  does nothing.** On a live run the bulk-create call reported success while every created
  contact came back with an empty label set, so the enrollment queue it was supposed to fill
  stayed empty and nothing downstream noticed. The step now says to add list membership in a
  separate call and verify the count moved. A queue that looks filled and is not is exactly
  the class of defect this repo treats as worse than no check at all.

## [1.7.2] - 2026-09-07

Three corrections, all found by running the engine against live companies rather than by
reading it. Nothing to do on upgrade; no configuration changes.

### Fixed

- **A scraped URL may never be constructed from convention.** `references/scraping-playbook.md`
  already said "sitemap first", and a run scraped `<domain>/pricing/` anyway because that is
  where pricing usually lives. The page did not exist, the 404 **still cost 5 Firecrawl
  credits**, and the information was on the homepage — which one `firecrawl_map` call would
  have shown. The rule is now stated as a prohibition rather than an ordering preference, it
  names the tool, and it records that a miss is not free. The soft version of this rule had
  already been read by the agent that broke it.
- **Apollo's `organization_revenue` returns `0.0` when revenue is unknown, not zero.**
  `field-provenance.md` made the 0-vs-blank distinction for CB Insights fields and never made
  it for Apollo's own. One enrichment call returned real estimates for two companies and
  `0.0` for a third that is privately held, so the absent value sits in the same column as
  the good ones. The rule is now explicit: write `N/A`, never `$0`, never cite it. A
  blueprint quoting "$0 revenue" to a prospect is a fabricated hard number that the
  falsifiability test cannot catch, because the number came from a tool.
- **A single source can contradict itself, and the Vault had no rule for it.**
  `references/research-vault.md` covered supersede-on-contradiction and coexist-on-complement
  across sources. It said nothing about one record whose structured `founded_year` said 2009
  while its own description said 2008 — no older fact to supersede, and not complements
  either. The Vault now takes one fact naming both values at `low` confidence, so whichever
  field the agent read first cannot silently become the hard number.

## [1.7.1] - 2026-09-07

Corrections to the feedback reporter and to two checks that shipped in 1.7.0 without
doing their job. Nothing to do on upgrade; no configuration changes.

### Changed

- **Sensitive values in a feedback note are now stripped, not rejected.** 1.7.0 refused
  any note containing a credential, workspace ID, email address, or private link, on the
  reasoning that a stripped note is one the approving person never actually read. That was
  right about the risk and wrong about the fix: rejection sends the tester back to rewrite
  from memory, which loses the detail that made the note worth having, and it makes the
  most forthcoming reporters do the most work. Each value is now replaced in place with a
  visible `[redacted: <kind>]` marker and the body states how many were removed.

  What makes that safe is the new **two-step approval**. Rendering the report sends nothing
  and prints a token derived from the exact body displayed; submitting requires that token,
  so a body edited after it was shown is refused. The text a human approves is provably the
  text that gets filed, and the host's own tool-approval prompt carries the decision rather
  than a question the agent asks itself. Blanket permission to run the script still cannot
  file anything that was never rendered.

### Added

- **`scripts/check_version_sync.py`, and with it a protectable `main`.** `release.yml`
  used to fix version drift itself: on a push to `main` it rewrote
  `.claude-plugin/plugin.json` and committed the result back as `github-actions[bot]`.
  That bot push was the single thing preventing branch protection from requiring a pull
  request — the load-bearing rule, since the safety checklist (no resolved instance IDs,
  no credentials, no client data) is a human gate a direct push skips entirely — and
  GitHub does not offer Actions in a personal repository's ruleset bypass list.

  Bumping both files in the PR removes the push. CI now fails when they disagree, the
  workflow's sync step exits early when they match and so never fires, and `main` can
  require a pull request with no bypass at all. This also closes the older trap the
  previous convention warned about: editing only the manifest used to do nothing, silently.

### Fixed

- **A URL could pass the allowlist while pointing somewhere else.** The check matched a
  host *prefix* and kept the rest of the string, so
  `https://docs.apify.com@wiki.internal.example/setup` read as vendor documentation when
  the trusted name was userinfo and the destination was the private host after the `@`.
  URLs are now parsed with `urlsplit` and denied by default: https only, no userinfo, no
  non-default port, exact hostname match. URL resolution also runs first, on untouched
  text, so a link is no longer half-rewritten by the email rule before it is judged.
- **`tests/test_platform_support.py` could not fail.** It scanned every markdown file in
  `skills/` and `references/` — including `platform-support.md`, the document whose claims
  it exists to check. Every needle was present in the claim itself, so deleting the actual
  evidence would have left it green. It now reads only the artifacts each row cites, which
  immediately surfaced that Apollo's evidence list omitted the file where
  `typed_custom_fields` actually lives.
- **A non-object report crashed instead of reporting.** `json.loads` accepts arrays and
  strings; every field read then raised `AttributeError` rather than returning a problem.
- **Generic and Not built were collapsed into one outcome.** "A platform that is not
  native still works" is true of Generic and false of Not built, and a reader on Salesforce
  would have taken it as a promise. The Get Started block, the README, and the tier table
  now separate them: Generic is a real option, Not built is genuinely unsupported.
- **The empty-scrape check no longer infers from runtime.** `scrape-linkedin-posts` now
  reads the run's own recorded input back and confirms `targetUrls` holds the intended
  profile URLs before a "No Content" row can be written. The timing tell is kept as a
  prompt to go look, labelled as one observation rather than a measurement.
- **The connector allowlist is pinned exactly** rather than by size, since connector names
  reach the rendered body unscanned and a size bound would accept one named after a client.

## [1.7.0] - 2026-09-06

Additive. Nothing changes how an existing install is invoked or configured, and an upgrade
needs no action. Three things arrive: the same Get Started steps in every entry point, an
honest statement of how well the engine speaks each platform, and a way for a setup run to
report itself instead of leaving the write-up as homework.

### Added

- **Get Started, in three places on purpose.** The install path was buried, and the most
  common way to get it wrong is to open the repo URL in a chat window — which installs
  nothing and runs nothing, while looking like it is working. The four steps now appear
  verbatim in `README.md`, `CLAUDE.md`, and a new `AGENTS.md`, so whichever file a person
  or an agent opens first, the correct start is already there. `references/get-started.md`
  is the source and `tests/test_get_started_consistent.py` fails the build if the copies
  drift or if the install commands stop matching the marketplace manifest — three copies
  are only safe while something pins them together.
- **`references/platform-support.md`: native, generic, or not built.** You choose your
  stack, and the engine now says plainly how well it speaks each part of it. **Native**
  (Apollo, Airtable, Apify, Firecrawl) means the skills are written against that
  platform's real MCP semantics and a deployment has run it end to end. **Generic**
  (HubSpot, Clay, CB Insights, Brand Kit OS, a file home, a warehouse) means the motion
  runs with the same gates, composition rules, and audits, but nobody built the
  platform-specific path: you map fields yourself and its failure modes are undocumented.
  **Not built** means there is no path here at all, whatever the vendor's own server can
  do — Salesforce is the worked example, with a first-rate official MCP server and no GTM
  OS integration. Tier is assigned on evidence in this repository, and
  `tests/test_platform_support.py` fails if a claim outruns it. `environment-setup` now
  states the tier and the specific cost once, at the ladder, and is told not to talk
  anyone out of their stack.
- **Setup runs can report themselves.** `scripts/setup_feedback.py` turns a run into a
  redacted report and, with the user's explicit approval, files it upstream through their
  own `gh`. The module's core claim — *not set up does not mean not owned* — can only fail
  on somebody else's half-configured accounts, and a tester who has to remember to write
  it up mostly does not. The report carries connector names, S0-S4 states, the checkpoint,
  the outcome, and short notes; notes are **rejected rather than stripped** when they
  contain a credential, a workspace ID, an email address, or a link outside vendor
  documentation, because a stripped note is one the approving person never actually read.
  `environment-setup` offers it at three moments, including when a run is abandoned — the
  finding that otherwise never gets reported. Consent is explicit and a no ends it.
- **Motion validation is a sweep, not a first-match test.** A contact who failed the motion
  they were checked against was being set aside, when the failure often belonged to a
  different motion's gate entirely. Step 3 now says to check a contact against every
  remaining motion before dismissing them, to separate an ACCOUNT-gate failure (the company
  does not qualify, so fixing the contact cannot help) from a PERSONA failure (the company
  qualifies and the right person may already be in the CRM), and to record which motions
  were checked and what blocked each. "Not a fit" is not a reusable answer; "checked against
  all of them, here is the closest and what blocks it" is.
- **An available job description is always audited, and always persisted.** The JD carries
  the role, the seniority, the tools, and often the reporting line — which is what says
  which persona owns the req and therefore which motion the contact belongs in. Running
  persona validation without reading a JD that exists is guessing with the answer on the
  page. The skill now requires scraping it whenever one is on file, auditing the role and
  reporting line against the persona under consideration, and storing the full text as a
  dated reference document rather than only a summary field. Summaries drop the reporting
  line, the seniority signals, and the tool list first, and those are the three things a
  re-check needs.
- **Targets with no posts come off the cadence.** A first scrape returning zero authored
  posts now sets that target's Tracking to `paused` with the reason recorded, instead of
  buying the same empty answer every cycle forever. Two interlocks bind it, and both matter
  more than the rule: it fires only on a VERIFIED empty run, because an unverified empty is
  indistinguishable from the silent input-key failure and auto-pausing on one turns a
  five-minute bug into a permanent wrong answer about a real person; and only on a FIRST
  scrape, because someone with existing rows who is quiet this cycle is a poster having a
  quiet quarter. Every auto-pause is named in the run report — a cadence that quietly
  shrinks itself is worse than one that costs too much.

### Changed

- **The field provenance map now documents what each field is FOR.** It recorded where every
  field came from and which gate it served, but not what it means, so the one thing a reader
  actually needed at the call site was the one thing missing: an empty `LinkedIn Posts` means
  "verified not a poster" in one reading and "not researched yet" in the other, and that
  difference decides whether a run re-scrapes. Both field tables gain a Purpose column
  covering what the field holds and what consumes it. A CRM field's label is not its
  contract, and Apollo offers nowhere to store the contract beside the field, so this file
  is the field documentation.

- **The composition spec now anchors on persona, not on signal alone.** The opener rule
  keyed only on the company's signal, so a founder and the operating owner sitting beside
  the open req received the same anchoring from the same facts. That is correct data
  addressed to the wrong job, and it reads as a mail merge to the one recipient who knows
  which of those two people they are. The spec now says to resolve the persona first, lets
  the closer follow the motion the contact is enrolled in rather than the company's loudest
  signal, and states the invariant that was previously only implied: one contact in one
  motion, never one motion per company. An account holding two personas may legitimately
  run two motions at once.
- **A voice fallback ladder for contacts with thin posting histories.** "Their own words
  preferred when posts exist" assumed the words would be usable, and said nothing about the
  common case where a contact has posted twice in three months and one of them is a
  greeting. The gap was filled by improvisation, which invents a voice for a real person.
  The ladder is now explicit — the person's own posts, then the company's public voice from
  the account research, then plain and thin with no mirror line — along with the reason to
  prefer thin over fluent, and the instruction to record which rung was used so a later
  reader can tell a deliberate thin opener from a lazy one.

  _(These three shipped in 1.7.0 but were still recorded as Unreleased when the
  release fired, so the published notes omitted them. Moved here after the fact;
  the GitHub release body was amended to match.)_

### Changed

- **`references/mcp-coverage-map.md` now says which question it answers.** Whether a
  vendor publishes an MCP server and whether GTM OS has been built against it are
  different facts, and conflating them is how someone ends up expecting Apollo-grade
  behavior from a platform nobody here has ever written a line for.

## [1.6.1] - 2026-09-06

A correction to `scrape-linkedin-posts`, found by running it rather than by reading it.
Nothing to do on upgrade; no configuration changes.

### Fixed

- **`scrape-linkedin-posts` now names the actor's input key.** A live run passed the
  profile list as `profiles`. The actor does not reject an unrecognized input key: it ran
  against zero targets and returned a **SUCCEEDED run with an empty dataset**, which is
  indistinguishable from a target who genuinely has not posted inside the window. Nothing
  in the skill said which key to use, so the next person had no way to catch it either.
  The skill now states that the profile list goes in `targetUrls`, records the silent
  failure mode, and gives the tell that separates the two cases — a real two-profile
  scrape takes ~40 seconds, the empty run finishes in under 4. It also forbids writing a
  "No Content" row off an empty run that has not been checked this way, which is how the
  defect would otherwise become permanent data.

## [1.6.0] - 2026-09-06

Additive: no existing skill changes how it is invoked, and an install that upgrades and
changes nothing in its config keeps the same invocation and configuration contract. One
behavior change is deliberate and confined to `gtm-blueprint`'s motion step — motion
selection is now an operator choice, and a company that matched no preset
(previously forced onto the nearest one) can take the custom path. In the batch
field-pipeline mode the selection gate fires selectively — clean single-preset matches
still compose unattended, and only the ambiguous and no-fit companies are held out for
the operator — so an existing batch run does not start stalling on every contact.

### Added

- **Custom-motion builder in `gtm-blueprint`.** The five motion presets (PLG,
  enterprise, founder-led, channel, regulated) were the only options; a company that
  fit none of them got the nearest preset forced onto it, which reads templated to the
  one reader who knows better — the recipient. `skills/gtm-blueprint/references/motion-templates.md`
  now carries a **Custom motion** section: when no preset fits, compose one from the same
  four-part framework the presets are built on (where the company's pipeline actually
  hides → Week 1; the shortest honest path to a conversation → Week 2; trustworthy
  reporting for their stage and buyer → Weeks 3-4; the closer). Same output format, same
  falsifiability standard, same no-fabrication rules — a different emphasis, never a lower
  bar. `gtm-blueprint` Step 3 adds it as classification option (7) and now frames motion
  selection as a named human choice: the classification is a recommendation the operator
  can accept, swap for another preset, or send to the custom path, rather than an
  automated verdict.

### Changed

- **`docs/ROADMAP.md` refreshed.** It still described v1.3.0 as "this release" while the
  repo was at 1.5.2. It now records the instance/playbook separation, setup module,
  research spine, and front door as shipped, notes the custom-motion builder, and lists
  the genuinely remaining work (provisioning defaults, `commands/` surface, `PLAYBOOK.md`,
  per-tool docs).
- **Template-use guardrails, aimed at operators.** The README gains a "Your instance vs.
  this repo" section stating plainly that this is a template you run, not a service, and
  that you never need to push anything back to it to use the engine — `main` is read-only
  upstream. `SETUP.md` adds Step 7: create a project `CLAUDE.md` in *your own* workspace
  (motion default, disclosure stance, field prefix, cadence, connector quirks — never
  secrets), separate from this repo's maintainer-facing `CLAUDE.md`, which the front-door
  section of `CLAUDE.md` now points to.
- **`MAINTAINING.md` documents recommended `main` branch protection** — require a PR,
  require CI, restrict direct pushes, block force-push — since the tokenization and safety
  review that keep resolved IDs out of a public template are defeated by a direct push.
  This is a one-time GitHub setting, not a file, so it is documented rather than enforced
  by CI.

## [1.5.2] - 2026-09-01

### Added

- `tests/test_fanout_workflow.py` — adversarial and wiring tests for
  `scripts/fanout_workflow.js`, which had none because it executes only inside
  the host Workflow tool. It turns out not to need the real harness: the five
  injected globals (`args`, `log`, `phase`, `agent`, `pipeline`) are stubbed, the
  real script runs, and every prompt each stage would have sent is captured and
  asserted against. 19 tests covering the wiring (does the writer actually
  receive the researcher's questions?), the Vault contract (does the supersede
  instruction still distinguish complement from contradiction?), truncation
  (does an oversized payload stay valid JSON?), and the injection defenses.

  The suite proves it can fail rather than asserting it: `MutationCoverage`
  reintroduces five defects into an in-memory copy of the script (the dropped
  researcher questions, a removed fence token, a reused token, a lost COMPLEMENT
  branch, and naive character-slicing) and asserts each one is detected. The file
  on disk is never modified.

### Fixed

- **A second prompt-injection hole, found by review of the first fix.** The
  critic is shown the fence token so it can read its own input, and its output
  was then fenced with that same token in the writer prompt. A hostile page could
  ask the critic to echo the token into a free-text field, planting a delimiter
  the writer could not tell from a real one. Researcher output and critic
  verdicts now carry separate tokens, and the critic-verdict token is minted
  where no upstream agent ever sees it.
- **Prompt-injection hardening in the fan-out writer.** The untrusted-content
  fences used fixed markers, and `JSON.stringify` escapes newlines but passes the
  literal text `=== END RESEARCHER OUTPUT ===` through verbatim — so a scraped
  page could plant a closing marker and address the writer as though it were the
  orchestrator. Markers now carry a per-run token the content has never seen, and
  the writer is told that a BEGIN/END line without that exact token is planted
  content rather than a delimiter.
- `.gitignore` now ignores `instance/`. An earlier convention kept the config at
  `instance/instance-config.json`, and Cowork-era notes still describe that path,
  so anyone following them would create a folder of resolved workspace IDs that
  nothing was ignoring.

## [1.5.1] - 2026-09-01

Process only. No skill, script, or config behavior changes, so nothing to do on
upgrade.

### Added

- The CodeRabbit review loop, written down in `MAINTAINING.md` (for maintainers)
  and `CLAUDE.md` (for an agent working in this repo), with the PR template
  updated to match. Reviews are treated as a second reviewer rather than a linter
  to clear: on the v1.5.0 PR, fifteen findings were raised, all fifteen were
  valid, and two were defects that re-reading would not have surfaced.

  Four rules carry most of the value, each one learned the expensive way on that
  PR: verify a finding against the code before **accepting** it and not only
  before rejecting it; answer every finding in its own thread, declines included;
  never exclude a file from review to silence a false positive, because doing so
  on `fanout_workflow.js` would have hidden the prompt-injection finding that
  file's review produced; and treat a finding about a broken check as the
  highest-value kind, since two of the fifteen exposed audits that could not fail.

  Local pre-push review is documented as optional
  (`coderabbit review --base main`, or `--agent` for structured JSON), since the
  GitHub review runs regardless.

- `tests/test_docs_match_ci.py` — asserts the check lists in `CLAUDE.md` and the
  PR template match what `ci.yml` actually runs, in both directions, and that
  every documented script exists.

### Fixed

- The PR template's check list omitted `scan_secrets.py` and
  `check_workflow_script.py`, both added to CI in 1.5.0. Anyone working that
  checklist would have ticked four boxes believing they had run everything CI
  runs, while skipping the credential scan. Found by the first local
  `coderabbit review` run on this branch, which is a fair advertisement for the
  loop this release documents. The new test above is why it cannot recur.

## [1.5.0] - 2026-09-01

The research spine and the setup module. Everything here is additive: no existing
skill changes how it is invoked, and an install that upgrades and changes nothing in
its config keeps working exactly as before.

Two capabilities land together. The **Research Vault** makes captured research
durable and diffable, so a second run on a company tells you what changed rather
than reading everything again. The **environment setup module** makes wiring the
engine a diagnosis rather than a questionnaire, on the premise that a user who has
not set a tool up has almost always still got the tool.

### Added

- `environment-setup` skill and `references/environment-setup.md` — the single
  canonical setup procedure, replacing per-skill setup prose. It places each
  connector on a five-state ladder (absent / owned but unreachable / reachable but
  unshaped / shaped but unrecorded / wired) and probes before it asks, because
  **not set up does not mean not owned**: the usual gap is a tool the user already
  pays for that has never been shaped for this engine. Only the first state needs a
  signup. Every skill now routes here when a connector it needs is missing.
- `scripts/setup_status.py` — answers "what is left for me to fill in, and what does
  each gap block?", grouped by connector. It classifies keys three ways rather than
  two: **set** (chosen), **unset** (empty), and **default** — non-empty but still
  byte-identical to what `instance-config.example.json` ships. That third state is
  the point. A plain `cp` of the example inherits every shipped default silently,
  they work, nothing fails, and nobody ever decides whether they are right for this
  workspace. Verdicts are `INCOMPLETE`, `READY_WITH_DEFAULTS`, and `READY`; the
  middle one is runnable but means values were inherited rather than chosen. `--json`
  for the audit trail.
- `references/research-vault.md` — the persistent research data spine (schema v1.1):
  Entities, Facts, Runs, Questions, plus a Field Keys reference table. Facts are
  append-only with mandatory provenance (source URL or inference tag, source type,
  method, capture date, agent, confidence) and are superseded rather than edited, so
  the set of facts a run superseded *is* its change report. Includes the
  supersede-versus-coexist rule, one-question-per-row and `partial` question status,
  and external-ID columns instead of IDs packed into notes.
- `references/run-manifest.md` — the resumability and cost-budgeting convention. One
  write-ahead JSON manifest per run, updated on every completed step, so a dropped
  connector is a resume rather than a restart. Costs are stated before spend across
  every meter, and a run projected to exceed its cap stops and asks.
- `references/fanout-harness.md` and `scripts/fanout_workflow.js` — parallel research
  across N companies with attribution intact. The orchestrator pre-creates Entity and
  Run rows (entity resolution is the one operation unsafe under concurrency);
  researchers only append; a separate writer stage validates provenance and runs the
  supersede protocol, so the write rules live in one place instead of N prompts.
  Human opt-in and a stated cost statement are required.
- `gtm-architecture-composer` skill — composes the five-layer GTM OS architecture
  (data spine, integration layer, agent workflows, micro apps, observability) and its
  60-day / 6-month / 12-month sequence from a completed intake. Refuses to compose
  from an empty one.
- `gap-closer` skill — works the open-question list: persona-routed batches, a hard
  three-question cap on outreach to a real person, drafts for human sending on
  LinkedIn and email (agents never hold credentials for a person's identity), and
  answers written back as sourced Facts.
- `event-attribution` skill — reconciles an event attendee list against the CRM and
  tags every match, additively, so an account sourced by outbound that later attends
  an event keeps both touches. Turns field spend into something queryable.
- `Tracking` field (`active` / `paused` / `archived`) on the posts base's Contacts and
  Company tables. Scheduled scrape runs touch only `active` rows; manual runs against
  a named target ignore it and report the override. Optional: an existing base with no
  such field behaves exactly as before.

### Changed

- `company-deep-research` now writes to the Research Vault as well as producing its
  report: Vault entity resolution and a Run row before harvesting (Step 1), full
  provenance and the supersede protocol after the verification pass (Step 10), and a
  run manifest opened before the first paid call (Step 0). With the Vault keys empty
  it degrades to report-only and says so.
- `scrape-linkedin-posts` gains two scrape-governance rules: recurring runs honor the
  `Tracking` field, and **every** run — scheduled or manual — ends by rebuilding the
  scrape roster from the live tables rather than patching it incrementally, so the
  roster cannot silently drift away from what a cadence will actually spend on.
- `scrape-linkedin-posts` now carries the version-check preamble every other skill
  already had.
- `SETUP.md` Step 1 is a diagnosis rather than a checklist, and routes through the
  setup module. New optional Step 2b builds the Research Vault base.
- `instance-config.example.json` gains six optional Research Vault keys, two optional
  `Tracking` field keys, and `SCRAPE_ROSTER_ARTIFACT`. All are optional: leaving them
  empty is a supported configuration with documented degradation, not a broken one.
- `scripts/validate_instance_config.py` checks any `AIRTABLE_*_BASE_ID` key for the
  `app` prefix rather than only the posts base by name, so a second base cannot
  silently accept a table ID where a base ID belongs.
- `MAINTAINING.md` states explicitly that "additive" is the test for *not major*, not
  the test for patch: a release adding a skill, script, reference, or config key is a
  minor even though nothing breaks. Adding it because this release was itself
  proposed as a patch on the reasoning that it was additive.

- `.github/PULL_REQUEST_TEMPLATE.md` and a "Pull requests" section in
  `MAINTAINING.md`: the branch-to-merge flow, the checklist CI cannot run (no
  resolved instance values, credentials, client data, real client names, or invented
  numbers), and how to review an incoming delivery — check its proposed version, its
  conventions, and its examples for real identifiers, and state every deviation.
  `SETUP.md` referenced this checklist by name before it existed; now it does.

- `.coderabbit.yaml` — review configuration. Aims automated review at what can
  break an installed copy (a step automating past a human gate, a hardcoded
  deployment ID, a spend with no stated cost, a validator that cannot fail) and
  away from prose style on documentation. It also excludes
  `scripts/fanout_workflow.js` from JS linting: that file is a Workflow-tool script
  whose body the harness wraps in an async function, so a module parser reports its
  required top-level `return` as an illegal statement. The finding is right about
  the syntax and wrong about the file, and the only "fix" would delete the script's
  output. The file now carries a header saying so.
- Docstrings on every function and class in the repo's Python (79/79).

- `scripts/scan_secrets.py` — replaces the credential audit this repo documented
  inline (`git log --all -p | grep -iE 'APOLLO|APIFY|API_KEY'`), which matched
  vendor *names* and so returned 271 hits of ordinary prose and zero credentials.
  An audit that can never come back clean teaches everyone to ignore it. The
  replacement matches credential *shapes* (Airtable PATs, Apify tokens, secret-ish
  assignments of long opaque values), redacts anything it finds, and runs in CI.
- `scripts/check_workflow_script.py` — real syntax checking for
  `scripts/fanout_workflow.js`. `node --check` silently exits 0 on any `.js` file
  containing `export`, so that file had no syntax coverage at all; this neutralizes
  its one top-level `return` and parses the result as a real module. Runs in CI.

### Fixed

- `fanout_workflow.js`: the writer stage was instructed to write the researcher's
  questions but was never passed them, so every researcher-generated question was
  silently dropped. It also truncated prompt payloads by slicing JSON at a
  character count, which emits malformed JSON mid-token; it now drops whole items
  and reports what it dropped. Its supersede instruction flipped any differing
  value to `superseded`, contradicting the Vault's coexist-on-complement rule and
  destroying true facts. Untrusted scraped content interpolated into the writer
  prompt is now explicitly delimited as data with the write scope pinned, and
  `FACTS_SCHEMA` now matches the Vault contract (`fact`, `value_type`, and the
  select option sets).
- `setup_status.py` crashed with a TypeError on a config file that was valid JSON
  but not an object.
- `SCRAPE_ROSTER_ARTIFACT` was documented as optional but rejected when empty.
- `gap-closer`, `gtm-architecture-composer`, and `event-attribution` gated Vault
  access on the base ID alone, so a config with a base but no table IDs passed the
  check and failed partway through a run.
- `scrape-linkedin-posts` added the optional `Tracking` keys to the list that stops
  the run when empty, which would have broken the documented legacy-base fallback.
- `event-attribution` told the agent both to append a touch to existing records and
  never to edit them; the no-edit rule is now scoped to human-managed fields.
- README described Apify and Airtable as globally required, contradicting CLAUDE.md.
- Removed an unsourced concurrency figure from `fanout-harness.md` and an unsourced
  duration from these notes.
- Fixed a malformed table row in `research-vault.md`, and stopped describing the
  Firecrawl probe as free (a scrape spends a credit).

### Upgrading

Nothing is required. Every new config key is optional, and an install that upgrades
and changes nothing keeps behaving exactly as before.

Two things are worth doing anyway. Run `python3 scripts/setup_status.py` to
see which of your values were inherited from the example rather than chosen. And if
you want research to accumulate rather than be re-read every time, build the Research
Vault base (SETUP.md Step 2b): without it the research skills still produce their
reports, they just cannot tell you what changed since last time.

## [1.4.0] - 2026-08-17

Initial public release of GTM OS: a configurable, vendor-neutral AI-native
go-to-market engine any team can install and point at their own CRM/Airtable/Apify
instances via `instance-config.json`.

**Why this starts at 1.4.0 rather than 0.1.0.** GTM OS is the generalized form of a
private engine that had already shipped four releases against a live pipeline. The
version line continues rather than restarting, so a version number means the same
thing in both places. The engine is not new; only its public, deployment-neutral
packaging is.

### Added

- Six skills: `gtm-signal-scan` (weekly buying-signal sourcing, scoring, tiered
  enrichment, list routing, audit logging), `outreach-audit` (quality gate for
  sequences — personalization depth, merge tokens, honesty rules, A/B discipline,
  configuration defects), `provision-gtm-engine` (provisions the full engine for a
  new deployment from a single company URL, with human gates at ICP sign-off,
  credit spend, and sequence activation), `gtm-blueprint` (composes a motion-classified
  30-day GTM plan behind a configurable CRM field, gated on field completeness),
  `scrape-linkedin-posts` (LinkedIn post/comment scraping into an Airtable
  posts base, with a digest pushed back into the CRM), and `jd-intake` (turns a job
  description into structured intake against the Known/Unknown status model).
- `SETUP.md` — the first-run walkthrough: connectors, instance config, dry run, and
  the local-vs-repo tokenization rule that keeps deployment values out of git.
- `scripts/render_report.py` — PDF renderer for run reports and onboarding output.
- References carried over from live operation: the onboarding template
  (Known/Unknown status model), the scraping playbook, an MCP coverage map, and a
  dated dependency-observations log recording which third-party behaviors have
  proven intermittent.
- Plugin-wide references: the canonical Apollo credit-cost table and
  score-before-you-reveal rule, the 12-signal buying-intent taxonomy, the portable
  Airtable posts-base schema, and the instance-config key reference.
- `examples/`: a synthetic scan report, audit-log entry, and composed blueprint —
  format anchors showing the shape of real run output without any real data.
- Instance-config system: every deployment-specific ID (CRM custom fields, list
  names, Airtable base/table/field IDs, field-name prefix) is resolved from
  `instance-config.json` at `{CONFIG_KEY}` placeholders in the skill bodies, so the
  same skill text works against any instance. `instance-config.example.json` is the
  template; the real file is gitignored.
- CI (`ci.yml`) validating both JSON manifests parse and every `skills/*/SKILL.md`
  has well-formed frontmatter with `name` matching its directory.
- Release automation (`release.yml`): a `VERSION` bump on `main` syncs
  `.claude-plugin/plugin.json`, tags, and publishes a GitHub Release sourced from
  this changelog.
- Tests for `field_gate.py` and `scripts/validate_skills.py`, run via
  `python3 -m unittest discover -s tests -v`.
