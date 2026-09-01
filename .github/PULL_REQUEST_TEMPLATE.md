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

     Bump VERSION alone. Never hand-edit .claude-plugin/plugin.json's version;
     release.yml syncs it after merge. Make the bump the LAST edit before opening
     this PR, since merging it fires the release. -->

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

- [ ] `python3 scripts/validate_skills.py`
- [ ] `python3 scripts/validate_instance_config.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json`

## Skill changes

<!-- Delete this section if no SKILL.md changed. -->

- [ ] Frontmatter `name` still equals the directory name
- [ ] The `description` carries **trigger phrases** a user would actually say, not
      just a summary of behavior
- [ ] Version-check preamble present (first, never blocking)
- [ ] Human gates intact — no step automates past ICP sign-off, credit spend, or
      pre-send review
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
