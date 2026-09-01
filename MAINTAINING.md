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

## Pull requests

Every change lands through a PR against `main`. `.github/PULL_REQUEST_TEMPLATE.md`
populates the description automatically; fill in every section rather than deleting
the awkward ones.

The flow, in order:

1. **Branch.** Never commit to `main` directly. Name the branch for the outcome, not
   the ticket: `v1.5.0-research-vault-and-setup`, not `nt/update-3`.
2. **Do the work**, running the four checks below as you go rather than at the end.
3. **Write the changelog entry** in the same PR as the change. A release whose notes
   are written afterwards describes what someone remembers, not what shipped.
4. **Bump `VERSION` last**, immediately before opening the PR. Merging a changed
   `VERSION` fires the release, so an early bump on a branch that then sits for a
   week is a release waiting to go off.
5. **Open the PR, let CI pass, merge.** Tagging and publishing are automatic.

### The review loop

CodeRabbit reviews every PR on this repo, and it is treated as a second reviewer
rather than as a linter to clear. On the v1.5.0 PR it produced fifteen findings,
all fifteen were valid, and two were defects no amount of re-reading would have
surfaced: a writer stage told to persist data it was never passed, and a prompt
whose supersede instruction contradicted the reference document added alongside
it. Budget for that outcome rather than expecting a rubber stamp.

**Review locally before pushing.** The CLI runs the same analysis against
uncommitted work, so findings arrive while the context is still in your head and
before anything is public:

```bash
coderabbit review --base main          # or --uncommitted for staged work
coderabbit review --agent              # structured JSON, for an agent to consume
```

Setup is `brew install coderabbit` then `coderabbit auth login` (browser). In
Claude Code, `/plugin install coderabbit` adds `/coderabbit:review` over the same
CLI. Neither is required to open a PR: the GitHub review runs regardless.

**Then, on the PR itself:**

1. **Triage every finding against the code before acting on it.** Not before
   rejecting it, and not before accepting it either. On the v1.5.0 PR one finding
   claimed a crash on non-object JSON; the naive cases turned out to be handled
   and the crash needed a config that was a non-object *containing a schema key*.
   Reproducing that first is what made the fix correct instead of approximate.
2. **Fix what is valid.** Most findings are.
3. **Reply in the finding's own thread**, one conversation per finding, saying
   what changed and in which commit. A finding you decline gets a reply too,
   stating the reason. Silence reads as agreement that never shipped.
4. **When a finding is right about the syntax and wrong about the file**, fix the
   context, never the code. See the rule below.
5. **Feed the miss back into `.coderabbit.yaml`.** A finding that reveals the
   reviewer lacked repo context is a config change, not just a reply.

**Never exclude a file from review to silence a false positive.** The first pass
at this excluded `scripts/fanout_workflow.js` because a module parser misreads its
required top-level `return`. That would have suppressed the best finding of the
review — untrusted scraped content interpolated beside Airtable tool instructions
— to save one predictable false positive. Suppress the specific finding class
through `path_instructions` and leave the file reviewed.

**The most valuable findings are the ones about checks, not code.** Two of the
fifteen showed that an audit this repo documented could not fail: a credential
grep matching vendor names (271 hits of prose, zero credentials) and
`node --check`, which silently exits 0 on any `.js` file containing `export`. A
check that cannot fail is worse than no check, because everyone learns to ignore
it. Both became real scripts with tests. Look for that class specifically.

### The checklist CI cannot run

CI validates manifests, skill frontmatter, config references, and the tests. It
cannot see any of the following, which is why they are review gates and why the PR
template restates them:

- **No resolved instance values.** Every deployment ID is a single-brace `{KEY}`.
  This is the one most likely to slip, because a skill improvement ported from a
  local copy arrives with real IDs baked in and works perfectly, which is exactly
  what makes it dangerous. Re-tokenize before committing, and add any new key to
  `instance-config.example.json` and to a group in `scripts/setup_status.py` in the
  same change.
- **No credentials**, in the tree or the history.
- **No client data, run artifacts, or audit logs.** `examples/` is synthetic, uses
  `.example` domains, and stays that way.
- **No real client or prospect names**, including in a war story about a production
  incident. Describe the incident, anonymize the company. The repo has never carried
  a client name; keep it that way.
- **No invented numbers.** The skills forbid fabricating a figure for a recipient;
  the same standard binds the repo's own docs. Leave the placeholder.

### Reviewing an incoming delivery

Work that arrives from elsewhere (a Cowork session, a zip, a patch) gets read, not
applied. Three things to check every time, because all three have actually come up:

- **Its proposed version number.** Check it against the SemVer rules above rather
  than adopting it. A delivery knows what it changed; it does not know what the rest
  of the repo already contains.
- **Its conventions against the repo's.** Token syntax, config shape, and naming
  follow this repo, not the delivery. A nested config block or a `{{double-brace}}`
  key will pass a human read and fail silently at runtime.
- **Its examples for real identifiers.** Deliveries written against a live engagement
  carry that engagement's names, IDs, and URLs in their examples.

State every deviation from the delivery's own instructions in the PR description.
A deviation that is explained is a decision; an unexplained one looks like a mistake
the next reader has to re-litigate.

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
