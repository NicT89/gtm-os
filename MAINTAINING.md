# Maintaining & Releasing

This guide is for maintainers of the GTM OS plugin repo. End users do
not need it — the user-facing README covers installation, connectors, and how the
version check surfaces updates.

## Canonical source of truth

- The repo `main` branch is authoritative. Every skill fetches
  `https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION` on
  invocation and notifies the user when their local copy is behind (it never blocks).
- Because the check reads from `main`, **a version bump is only "live" once it is
  merged to `main`.** Work on a branch, then merge.

## The version lives in two files — `VERSION` is the one you edit

| File | Field |
|---|---|
| `VERSION` | the whole file (e.g. `1.0.0`) — **the source of truth, bump this** |
| `.claude-plugin/plugin.json` | `"version"` — **auto-synced, do not hand-edit** |

`.github/workflows/release.yml` reads `VERSION` on every push to `main` that changes
it, rewrites `.claude-plugin/plugin.json`'s `version` to match, and commits that back
to `main` as `chore: sync plugin.json to X [skip ci]` — before tagging and publishing
the release. Release packages (including Cowork) only ever need to bump `VERSION`;
the manifest follows automatically. There is no CI check enforcing the two fields
match pre-merge (that job, `version-check.yml`, was retired for this reason) — sync
happens after merge, not before.

## Release process

1. Make your changes (edit skills, README, etc.).
2. Decide the new version with [Semantic Versioning](https://semver.org):
   - **patch** (`1.0.x`) — wording fixes, clarifications, non-behavioral tweaks.
   - **minor** (`1.x.0`) — new skill, new capability, backward-compatible additions.
   - **major** (`x.0.0`) — changes that alter how existing skills behave or are invoked.

   **"Additive" is not the test for patch; it is the test for *not major*.** A release
   that adds a skill, a script, a reference, or a config key is a **minor** even though
   nothing breaks and every existing install keeps working untouched. Patch is for
   releases that change no capability at all. This trips people up because a purely
   additive release feels low-risk, and low-risk reads as "patch" — but the number is
   telling users what is *there*, not how nervous the maintainer was. If a user could
   invoke something after upgrading that they could not invoke before, it is a minor.

   Incoming deliveries sometimes propose their own version number. Check it against
   these rules rather than adopting it: the delivery knows what it changed, not what
   the rest of the repo already contains.
3. Bump `VERSION`. Leave `.claude-plugin/plugin.json` alone — the release workflow
   syncs it for you after merge.
4. Move the relevant notes from `## [Unreleased]` into a new dated section in
   `CHANGELOG.md` (add an `### Added` / `### Changed` / `### Fixed` group as needed).
5. Commit, open a PR, let CI pass, and merge to `main`. Merging (with a changed
   `VERSION`) triggers the sync-and-publish workflow automatically.

Tagging and publishing are automatic — do not tag by hand. See below.

## Release notes come from `CHANGELOG.md`

`.github/workflows/release.yml` fires on any push to `main` that changes `VERSION`.
It validates the version, syncs `.claude-plugin/plugin.json` to match and commits
that back to `main`, checks the release does not already exist, then tags
`v<version>` and publishes a GitHub Release.

For the body it extracts the `## [<version>]` section from `CHANGELOG.md` verbatim.
There is no second notes file to keep in sync — **the changelog entry you write in
step 4 is the release page every user reads.** Write it for users: what changed, and
what (if anything) they must do to upgrade. Maintainer instructions belong in this
document instead.

Three consequences worth remembering:

- **A missing or misnamed section silently degrades the release.** If no
  `## [<version>]` heading matches, the workflow logs a warning and falls back to
  auto-generated commit notes. That is what happened to v1.2.0. Match the heading
  format exactly: `## [1.4.0] - 2026-08-20`.
- **The tag is created for you.** `git tag` by hand is unnecessary and risks
  colliding with the workflow. If a release needs republishing, delete the release
  and tag on GitHub first; the workflow skips any version whose release already
  exists.
- **`CHANGES-<version>.md` is deprecated.** The workflow still reads one if the
  changelog section is missing, so old releases keep working, but do not write new
  ones. The remaining files (`CHANGES-1.1.0.md`, `CHANGES-1.3.0.md`) should have
  their content folded into `CHANGELOG.md` and then be deleted.

`workflow_dispatch` is enabled, so you can publish the current `VERSION` on demand
without touching the file.

## One source of truth, one writer at a time

This clone (wherever your team keeps the working copy of `gtm-os`) is canon.
Loose copies elsewhere in the project (zips, `06-plugin/skills/`, scratch outputs) are
not sync targets — installed skills get refreshed FROM this clone, not the other way
around. Any session touching this clone (Cowork, another chat, Claude Code) should
`git pull` before starting work, and treat the `VERSION` bump as the last edit before
opening a PR, since merging it fires the release.

## Updating a local install

Users installed via the marketplace can refresh with Claude Code's plugin update
flow. For belt-and-suspenders freshness, the README documents a monthly scheduled
task that diffs the local plugin version against the repo `VERSION`.

## Notes

- Do not commit run artifacts, audit logs, or client data. Those live in each user's
  own storage (local folder or Google Drive) and are the personalized layer of the
  playbook, per the README.
- Keep `README.md` identical to the plugin's shipped README so installed copies and
  the repo stay consistent; maintainer-only notes belong here, not in the README.
