# Forking GTM OS for your company

How a company takes its own copy of GTM OS, installs the plugin from that copy, keeps
receiving upstream releases, and keeps its own changes out of upstream. This is the
"private copy" a Launch99 engagement delivers; it works the same for anyone.

Two repositories, one direction of flow:

| Repo | Who writes to it | What it holds |
|---|---|---|
| `NicT89/gtm-os` (upstream) | The maintainers, by pull request | The engine. Deployment-neutral, no identifiers. |
| `<your-org>/gtm-os` (your fork) | You | Upstream plus your own changes. Still no instance values. |
| `<your-org>/gtm-os-instance` (private, separate) | You | `instance-config.json`, audit log, run reports, project `CLAUDE.md`. |

Your fork never pushes to upstream. GitHub forks only move code toward upstream through a
pull request you open on purpose, so nothing you commit on your fork reaches `NicT89/gtm-os`
unless you ask for it.

## 1. Fork

1. On github.com, open `NicT89/gtm-os` and select **Fork**. Choose your organization as the
   owner. Keep the name `gtm-os` (the marketplace name inside `.claude-plugin/marketplace.json`
   is `gtm-os` and does not depend on the repo name, but keeping it avoids confusion).
2. Make the fork **private** if your organization requires it. A private fork still receives
   upstream releases; the only difference is that `release.yml` skips on private repos so you
   do not spend Actions minutes. You do not need releases on your fork: you install from a
   branch, not from a release.
3. Protect `main` on your fork (Settings > Branches): require a pull request. Your own changes
   land on branches and merge through PRs, the same way upstream works.

## 2. Install the plugin from your fork

In claude.ai or the Claude desktop app: **Customize > Plugins > Add > Add marketplace**, and
enter your fork's URL (`https://github.com/<your-org>/gtm-os`). For a private fork, connect
GitHub when the dialog asks and give the Claude GitHub App access to that repository. On a
Team or Enterprise plan an Owner adds the marketplace for the organization and can mark the
plugin installed by default.

In Claude Code:

```
/plugin marketplace add <your-org>/gtm-os
/plugin install gtm-os@gtm-os
```

Then open the plugin's **Connectors** tab and connect each one with your own account. The
plugin declares the connectors in `.mcp.json`; it carries no credentials.

Turn on **Sync automatically** for the marketplace (or use **Check for updates**) so a merge
to your fork's `main` reaches every installed copy.

## 3. Receive upstream updates

Your fork does not update itself. Each upstream release reaches you one of two ways:

- **By hand.** On your fork's page, GitHub shows "This branch is N commits behind
  NicT89/gtm-os:main" with a **Sync fork** button. Select **Update branch**. This is a merge
  of upstream `main` into your `main`; if you have changed the same lines, GitHub opens a
  pull request instead so you resolve the conflict.
- **On a schedule.** Copy `examples/fork/upstream-sync.yml` into `.github/workflows/` on your
  fork. Once a week it fetches upstream `main` and opens a pull request on your fork titled
  "Upstream release vX.Y.Z". You review and merge; nothing merges on its own. Merging it is
  what updates your installed plugin.

Either way, read the `CHANGELOG.md` section for the release first. A release that needs an
operator action says so at the top of its section.

Pin instead of track when you need to: install from a tag (`v1.15.0`) rather than `main` by
checking that tag out on a branch of your fork and pointing the marketplace at that branch.
You then move the pin deliberately.

## 4. Make your own changes

Branch, change, open a pull request on your fork, merge. Your installed plugin updates on
the next sync. Keep two rules:

- **No instance values in the fork.** Field IDs, base IDs, list names and prefixes go in
  `instance-config.json` in your instance repo. `scripts/scan_secrets.py --history` is the
  check; CI runs it.
- **Change the engine in `skills/` and `references/`; change your deployment in your instance
  repo.** A change to how a skill reads your HubSpot is an engine change. Which portal it
  reads is a deployment value.

If a change of yours would help every deployment, open a pull request against upstream from
your fork with every instance value re-tokenized to a `{KEY}`. `MAINTAINING.md` has the
checklist. Upstream never takes client data; the pull request template asks you to confirm
that.

## 5. When a maintainer updates your fork for you

A Launch99 engagement often has the maintainer making changes to the client's fork directly.
Give that person **write** access to the fork (not admin), keep `main` protected so their
changes also arrive as pull requests you can read, and keep the instance repo's access
separate. The maintainer never needs the instance repo to ship an engine change.
