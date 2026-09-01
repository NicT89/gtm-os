# Working on this repo

**Are you here to USE the engine, or to CHANGE it?**

- **To use it** — you want to run a signal scan, compose a blueprint, audit a
  sequence, scrape posts: don't read this file. Install the plugin
  (`/plugin marketplace add NicT89/gtm-os`, then `/plugin install gtm-os@gtm-os`),
  work through [SETUP.md](SETUP.md), and invoke the skills by name or by describing
  what you want. [README.md](README.md) is the overview.
- **To set up your own environment** — connectors, bases, `instance-config.json`: the
  `environment-setup` skill drives it, over
  [references/environment-setup.md](references/environment-setup.md). That module is the
  single setup procedure; every skill routes there rather than carrying its own.
- **To set it up for a company from scratch** — the `provision-gtm-engine` skill
  does that end to end from a single company URL, with human gates at ICP sign-off,
  credit spend, and sequence activation. Start there rather than wiring things by
  hand.
- **To change the repo itself** — read on. Everything below is for that.

---

This repo *is* the GTM OS plugin. It ships prose playbooks (skills)
plus a small amount of deterministic tooling. Editing it is editing what every
installed copy executes, so the conventions below are load-bearing.

For the release process, see [MAINTAINING.md](MAINTAINING.md). For what the plugin
does, see [README.md](README.md). This file is the part an agent needs before
changing anything.

Deployment-specific values are never written into skill bodies — they live in
`instance-config.json` and are referenced as `{KEY}`. See
[references/instance-config.md](references/instance-config.md) before adding any
value that differs between installs.

## Layout

```
.claude-plugin/    plugin.json + marketplace.json  (version lives in plugin.json)
skills/<name>/     SKILL.md, plus optional references/ and scripts/
references/        plugin-wide references shared across skills
                   (environment-setup, research-vault, run-manifest, fanout-harness,
                    airtable-posts-base, instance-config, mcp-coverage-map, ...)
examples/          redacted sample outputs — the format anchors for the skills
.github/workflows/ ci (every push/PR) + release (VERSION change on main)
VERSION            the single source of truth users' version checks read
```

Skill-local `references/` are for one skill. Root `references/` are for material
more than one skill cites — the credit table is the current example. When citing a
root reference from inside a SKILL.md, say "the plugin root's references/..." so it
is not confused with the skill's own folder.

## The rules that CI enforces

- **Both JSON manifests must parse.**
- **Every `skills/*/SKILL.md` needs YAML frontmatter with `name` and `description`,
  and `name` must equal the directory name.** The description is what triggers the
  skill, so it carries the trigger phrases, not just a summary of behavior.

## The rules CI cannot enforce

- **Bump `VERSION` alone; never hand-edit `.claude-plugin/plugin.json`'s version.**
  `release.yml` rewrites the manifest to match `VERSION` and commits it back to
  `main` before tagging. Editing both by hand still works but is redundant, and
  editing only the manifest silently does nothing. There is deliberately no CI
  check that the two match — it would false-fail every release PR. See
  [MAINTAINING.md](MAINTAINING.md).
- **Never commit client data, run artifacts, or audit logs.** Those live in each
  user's own storage and are the personalized layer of the playbook. `.gitignore`
  blocks the common names; that is a safety net, not permission to try.
- **Never commit a credential.** `.env` and `.env.*` are ignored. The audit is
  `python3 scripts/scan_secrets.py --history`, which must exit 0. It runs in CI
  against the working tree; the `--history` pass is the pre-release check.
  It replaced `git log --all -p | grep -iE 'APOLLO|APIFY|API_KEY'`, which matched
  vendor *names*: 271 hits on this repo's own prose and not one credential. An
  audit that can never come back clean teaches everyone to ignore it.
- **Do not invent numbers.** The skills demand "one hard number, verifiable, true
  for this specific recipient" and forbid fabrication. That standard applies to the
  repo's own documentation too: if a figure for the adopter's own pipeline is not in
  hand, leave the placeholder rather than inventing a plausible one.
- **Keep `README.md` shippable as-is.** It is the README installed copies carry.
  Maintainer-only material goes in MAINTAINING.md or here.

## Editing skills

A `SKILL.md` loads on *every* invocation of that skill; `references/` load only when
the skill reaches for them. That is the whole basis for what goes where:

- SKILL.md holds the decision flow, the gates, and anything needed on every run.
- references/ hold lookup material — field dictionaries, templates, cost tables,
  rubrics — that is consulted at one specific step.

When a SKILL.md grows past roughly 80 lines, that is usually a sign a reference
should be split out rather than that the skill got more complex.

Four structural conventions every skill in this repo follows:

1. **Version check first, never blocking.** Fetch the repo VERSION, compare, notify
   on mismatch, continue.
2. **Human gates are named and explicit.** ICP sign-off, credit spend, and pre-send
   review are gates. Do not add a step that automates past one.
3. **Credit-consuming actions state the total before spending** and report actual
   burn after, costed from `references/apollo-credit-costs.md`.
4. **Everything Claude creates in Apollo carries "[Claude]" in its name.**
   Human-managed assets are never edited.
5. **Connector preflight routes to one place.** A skill that needs a connector says what
   it degrades to without it and sends the user to the `environment-setup` skill and
   [references/environment-setup.md](references/environment-setup.md). Do not write
   setup instructions into a SKILL.md: they drift, and a user then gets a different
   procedure depending on which skill they happened to run. The framing that module
   enforces is load-bearing and belongs in any prose you add about it — **not set up does
   not mean not owned.** Most users already have the tool and have simply never shaped it
   for this engine, so probing beats asking and asking beats recommending a signup.

## Shipping a change: the PR loop

Every change lands through a PR, and CodeRabbit reviews it as a second pair of
eyes. Full process in [MAINTAINING.md](MAINTAINING.md#the-review-loop); the part
you need before starting:

1. **Branch.** Never commit to `main`.
2. **Build, running the checks as you go**, not at the end:
   ```bash
   python3 scripts/validate_skills.py
   python3 scripts/validate_instance_config.py
   python3 scripts/scan_secrets.py
   python3 scripts/check_workflow_script.py
   python3 -m unittest discover -s tests
   ```
3. **Review locally before pushing**, if the CLI is authenticated:
   `coderabbit review --base main` (or `--agent` for structured JSON). Findings
   are cheaper here than on the PR.
4. **Bump `VERSION` last**, immediately before opening the PR — merging a changed
   `VERSION` fires the release, so an early bump on a branch that sits is a
   release waiting to go off. Additive is **minor**, not patch.
5. **Open the PR**, fill in every template section, and label it (`release`,
   `area: *`, `safety-review` when it touches redaction, credentials, client
   data, or instance IDs).
6. **Work the review**, per the rules below.

### Working a CodeRabbit review

**Verify each finding against the code before acting on it — before accepting it,
not just before rejecting it.** Agents reviewing agents produce confident, precise
prose either way. On the v1.5.0 PR a finding described a crash whose obvious
repro did not actually crash; the real precondition was narrower, and reproducing
it first is what made the fix correct rather than approximate. Do not take a
finding at face value, and do not dismiss one because it is inconvenient.

**Reply in each finding's own thread**, one conversation per finding, naming what
changed and in which commit. A finding you decline still gets a reply with the
reason.

**When a finding is right about the syntax and wrong about the file, change the
context, not the code.** Never exclude a file from review to silence a false
positive: the first attempt at this excluded `fanout_workflow.js`, which would
have suppressed the prompt-injection finding that file's review produced.
Suppress the specific class in `.coderabbit.yaml`'s `path_instructions` instead.

**Treat a finding about a broken check as the highest-value kind.** Two on that PR
showed audits that could not fail. A check that cannot fail is worse than no
check.

**Then improve the reviewer.** `.coderabbit.yaml` carries per-path instructions;
when a finding shows it lacked repo context, that is a config change and not just
a reply. It already scopes the two rules easiest to get wrong from outside — "do
not invent numbers" means a number a reader could act on as fact, not colloquial
duration; "no client data" whitelists the synthetic names. CodeRabbit also reads
this file, so a convention written here reaches the reviewer.

## Scripts

`skills/gtm-blueprint/scripts/field_gate.py` is the model: standard library only, a
docstring with usage, meaningful exit codes (0 pass / 1 fail / 2 usage error), and
JSON on stdout so results are loggable to the audit trail. New scripts should match
that shape and ship with tests under `tests/`.

Run the tests with `python3 -m unittest discover -s tests -v`.

`scripts/fanout_workflow.js` is the exception to that shape: it is a Workflow-tool
orchestration script, not a CLI, so it has no exit codes and no unit tests. Its rules
instead are that it stays **tokenized** (instance IDs arrive through `args` at call time,
never in the file), it never reads the clock (`as_of_date` is passed in), and its writer
stage is the single place the Vault provenance rules are enforced, so a researcher that
emits a malformed fact fails validation instead of polluting the base. The contract is
[references/fanout-harness.md](references/fanout-harness.md).

**It does not parse as a standalone ES module, and that is correct.** The Workflow tool
wraps the script body in an async function before executing it, which is what makes the
top-level `return` and `await` legal and what injects `args`, `log`, `phase`, `agent`,
and `pipeline`. A module parser reports "Illegal return statement" plus a list of
undefined globals; every one of those findings is right about the syntax and wrong about
the file, and the only way to "fix" the return is to delete the script's output. The file
is not excluded from review: `.coderabbit.yaml` suppresses the known-false syntax
findings specifically and directs the reviewer at the prompt construction instead,
which is where its real risks live.

It is still **syntax**-checked, in CI, by `scripts/check_workflow_script.py`: that
rewrites the one top-level `return` into an assignment and parses the result as a real
module, so every brace and template literal is verified as written. Do not substitute
`node --check` on the `.js` file — node stops checking entirely once it sees `export`
in a `.js` file and exits 0 on a file with a real syntax error, which is how this file
went unchecked in the first place. For behavior, review against the harness reference.

## Connectors

Apollo is required; Apify, Airtable, Google Drive, and CB Insights are optional and
each skill degrades explicitly when one is missing rather than guessing. The Research
Vault base is optional in the same way: with its keys empty, the research skills produce
their reports and persist nothing, and say so. Note that
interactively-authenticated MCP connectors may be unavailable in headless or
scheduled runs — a skill that hard-stops on a missing connector will hard-stop
there, which is correct behavior but worth knowing when scheduling a run.
