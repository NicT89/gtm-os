<!--
Editing this repo is editing what every installed copy executes, so a PR here
carries a little more than usual. Fill in every section; delete the ones that
genuinely do not apply, and say why rather than leaving them blank.
Full process: MAINTAINING.md.
-->

## What and why

<!-- One paragraph. What changed, and what problem it solves. If a defect drove
     it, name the defect: this repo's convention is that every gate traces back to
     something that actually broke. -->

## Version

- [ ] `VERSION` bumped, or **no bump needed** (explain below)
- Version: `x.y.z` — **patch** / **minor** / **major**

<!-- "Additive" is the test for NOT MAJOR, not the test for patch. A release that
     adds a skill, script, reference, or config key is a MINOR even though nothing
     breaks. If a user could invoke something after upgrading that they could not
     invoke before, it is a minor. See MAINTAINING.md.

     Bump VERSION AND .claude-plugin/plugin.json's version together, in the same
     commit; check_version_sync.py fails CI if they disagree. Make the bump the LAST
     edit before opening this PR, since merging it fires the release. Patch is the
     default: minor is for a new skill or something an operator can newly ask for. -->

## Changelog

- [ ] `CHANGELOG.md` has a `## [x.y.z]` section for this version
- [ ] It is written for **users**: what changed, and what they must do to upgrade

<!-- release.yml extracts that section verbatim as the GitHub Release body. It is
     the release page every user reads, not an internal note. Maintainer-facing
     detail belongs in MAINTAINING.md or this PR description. -->

## Safety review (CI cannot catch these)

- [ ] **No resolved instance values.** Every CRM/Airtable/Apify ID is a `{KEY}`
      token, single braces. Any new key was added to `instance-config.example.json`
      and grouped in `scripts/setup_status.py` in this same change.
- [ ] **No credentials.** `python3 scripts/scan_secrets.py --history` exits 0.
- [ ] **No client data**, run artifacts, or audit logs. Examples are synthetic and
      use `.example` domains.
- [ ] **No real client or prospect names.** This repo has never carried one.
- [ ] **No invented numbers.** A figure with no source is a placeholder, not a
      plausible guess.

## Checks

<!-- This list must match .github/workflows/ci.yml. A test enforces that. -->

- [ ] `python3 scripts/validate_skills.py`
- [ ] `python3 scripts/scan_secrets.py`
- [ ] `python3 scripts/check_workflow_script.py`
- [ ] `python3 scripts/validate_instance_config.py`
- [ ] `python3 scripts/check_version_sync.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json`

## Review

- [ ] Reviewed locally before pushing (`coderabbit review --base main`), or noted
      below why not (an exhausted free-tier limit is a fine reason, and common)
- [ ] If CodeRabbit did **not** run, that is stated here rather than left implied.
      A green check with zero findings can mean rate-limited, not reviewed
- [ ] Every CodeRabbit finding is answered **in its own thread**, including any
      declined, with the reason
- [ ] Findings were verified against the code before being accepted, not only
      before being rejected
- [ ] Any finding that revealed missing reviewer context became a
      `.coderabbit.yaml` change, not just a reply

<!-- Do not exclude a file from review to silence a false positive. Suppress the
     specific class in .coderabbit.yaml's path_instructions and leave the file
     reviewed. Excluding fanout_workflow.js would have hidden a prompt-injection
     finding to save one predictable parser complaint. -->

## Review findings

- Reviews run: <!-- e.g. "CodeRabbit on <sha>: <count> findings" / "rate-limited on <sha>" / "self-review only" -->
- Commits no reviewer has seen: <!-- list the SHAs, or "none" -->

| # | Source | File | Finding | Outcome |
|---|---|---|---|---|
| 1 | | | | |

<!-- One row per finding, from any reviewer: CodeRabbit (hosted or CLI), a human, or
     your own self-review. Keep this table current as the review goes on; it is the
     record that outlives the threads, which collapse once resolved.

     Source: CodeRabbit, CLI, a reviewer's handle, or self.
     Finding: one line, in your words, not pasted from the bot.
     Outcome: "fixed in <sha>" (with the test that covers it, when there is one),
     "declined: <reason>", or "open". Nothing merges with a row still "open".

     Replace the table with "No findings" only when a review actually completed.
     A rate-limited run is not zero findings; say it in "Reviews run". -->

## Skill changes

<!-- Delete this section if no SKILL.md changed. -->

- [ ] Frontmatter `name` still equals the directory name
- [ ] The `description` carries **trigger phrases** a user would actually say, not
      just a summary of behavior
- [ ] Version-check preamble present (first, never blocking)
- [ ] Human gates intact — no step automates past ICP sign-off, credit spend, catch-all
      enrollment policy, or pre-send review
- [ ] Credit-consuming actions state total cost before spending, report burn after
- [ ] Connector preflight routes to `environment-setup` rather than carrying its
      own setup prose
- [ ] Anything only needed at one step lives in `references/`, not in the SKILL.md

## Deviations

<!-- Did you depart from a documented convention, an incoming delivery's stated
     instructions, or a reviewer's earlier call? List each with its reasoning.
     Silent deviations are the ones that cost trust; stated ones are just decisions. -->

## Follow-ups

<!-- Anything deliberately left out of scope, so it is tracked rather than lost. -->
