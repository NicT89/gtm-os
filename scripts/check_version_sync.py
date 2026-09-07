#!/usr/bin/env python3
"""Assert VERSION and .claude-plugin/plugin.json agree, so releases need no bot push.

Why this exists, and why it did not before
------------------------------------------
`release.yml` used to fix the drift itself: on a push to `main` that changed VERSION, it
rewrote plugin.json and committed the result back to `main` as `github-actions[bot]`.
That worked, and it made a CI check pointless — the two files were legitimately different
on every release PR, so a check would have false-failed all of them.

The cost only showed up when `main` needed protecting. "Require a pull request before
merging" is the load-bearing branch-protection rule here, because the safety checklist
(no resolved instance IDs, no credentials, no client data) is a human gate that a direct
push skips entirely. But a bot pushing straight to `main` violates exactly that rule, and
on a personal repository GitHub Actions is not offered in the ruleset's bypass list. So
the automated push was the thing standing between this repo and a protected `main`.

Bumping both files in the PR removes the push. The sync step in `release.yml` already
exits 0 when the versions match, so it stays as a safety net and simply never fires. This
check is what keeps that true: it fails the PR if the two ever disagree, which is also the
fix for the older trap the previous rule warned about — editing only plugin.json used to
do nothing at all, silently.

Usage:
    python3 scripts/check_version_sync.py [--json]

Exit code 0 = the two agree, 1 = they disagree or a file is unreadable, 2 = usage error.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "VERSION"
PLUGIN_FILE = REPO_ROOT / ".claude-plugin" / "plugin.json"

SEMVER = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)*$")


def read_version():
    """The VERSION file's contents, stripped. Returns (value, problem)."""
    try:
        raw = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError as e:
        return None, f"cannot read {VERSION_FILE.name}: {e}"
    if not SEMVER.match(raw):
        return raw, f"VERSION is {raw!r}, which is not MAJOR.MINOR.PATCH"
    return raw, None


def read_plugin_version():
    """plugin.json's `version` field. Returns (value, problem)."""
    try:
        data = json.loads(PLUGIN_FILE.read_text(encoding="utf-8"))
    except OSError as e:
        return None, f"cannot read plugin.json: {e}"
    except json.JSONDecodeError as e:
        return None, f"plugin.json does not parse: {e}"
    if not isinstance(data, dict) or "version" not in data:
        return None, "plugin.json has no `version` field"
    return str(data["version"]).strip(), None


def check():
    """Return a list of problems; empty means the two files agree."""
    version, problem_v = read_version()
    plugin, problem_p = read_plugin_version()
    problems = [p for p in (problem_v, problem_p) if p]
    if problems:
        return problems
    if version != plugin:
        problems.append(
            f"VERSION is {version} but .claude-plugin/plugin.json says {plugin}. "
            "Bump both in the same commit — the release workflow no longer pushes a fix "
            "to main, so a mismatch ships as-is."
        )
    return problems


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    args = parser.parse_args()

    problems = check()
    version, _ = read_version()

    if args.json:
        print(json.dumps({"version": version, "problems": problems,
                          "verdict": "FAIL" if problems else "PASS"}, indent=2))
    elif problems:
        print(f"FAIL: {len(problems)} problem(s).\n")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print(f"ok    VERSION and plugin.json both say {version}.")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
