# Changelog

All notable changes to the GTM OS plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version recorded here must always match the `VERSION` file and the `version`
field in `.claude-plugin/plugin.json`. See [MAINTAINING.md](MAINTAINING.md) for the
release process. Release notes are sourced verbatim from the matching `## [x.y.z]`
section of this file — see MAINTAINING.md for how that extraction works.

## [Unreleased]

### Added

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
  redacted report and files it upstream through the tester's own `gh`. The module's core
  claim — *not set up does not mean not owned* — can only fail on somebody else's
  half-configured accounts, and a tester who has to remember to write it up mostly does
  not. The report carries connector names, S0-S4 states, the checkpoint, the outcome, and
  short notes. **Sensitive values are stripped automatically**: credentials, workspace IDs,
  email addresses, and links outside vendor documentation are each replaced in place with a
  visible `[redacted: <kind>]` marker, and the body states how many were removed — so a
  tester writes their note naturally instead of self-censoring it.

  Approval rides on the host's existing tool-approval prompt rather than on a question the
  agent asks itself. Rendering the report sends nothing and prints a token derived from the
  exact body; submitting requires that token, so a body that changed after it was displayed
  is refused. Nothing can be filed that was not first put on screen, including under a
  permission setting that would otherwise run the script unattended.
  `environment-setup` offers it at three moments, including when a run is abandoned — the
  finding that otherwise never gets reported. A no ends it.

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
