#!/usr/bin/env python3
"""File a bug, a feature request or feedback on a skill as a redacted upstream issue.

This is the general case of scripts/setup_feedback.py, which exists for one skill's
setup run. A company running its own copy of GTM OS finds defects the maintainer never
sees: a skill that stops on a connector it should have degraded around, a gate that fires
on the wrong field, a reference that no longer matches the vendor's API. The person who
hit it is usually mid-run, so the report has to be a step of the run rather than homework.

What reaches the issue
----------------------
The kind (bug, feature, skill-feedback), the skill or area it concerns (an allowlist, so a
free-typed name cannot carry an identifier), the installed plugin version, the surface it
ran on, optionally each connector's S0-S4 state, a one-line title, and the free-text
sections for that kind. Every free-text field goes through setup_feedback.redact_note, so
workspace IDs, CRM field IDs, email addresses, credentials and links outside vendor
documentation are replaced in place with a visible `[redacted: <kind>]` marker. The
patterns are imported, not restated, so the two reporters cannot drift apart. The redactor
recognizes shapes, not meaning: names and IDs in formats it does not know pass through, so
the skill has the reporter remove those before rendering, and the preview is the second
check.

How approval works
------------------
The same two-step flow as setup_feedback.py, for the same reason: the host's own
tool-approval prompt on the submit command is the acceptance gate.

    1. python3 scripts/feedback.py --report f.json
       Renders the exact title and body and prints a token derived from both. Sends
       nothing.

    2. python3 scripts/feedback.py --report f.json --submit --confirm <token>
       Files it with the user's own gh credentials. A title or body that changed after
       it was shown produces a different token and is refused.

Without gh, or in a chat session with no shell, the render step is still the right
output: --json carries a `paste_url` that opens the matching issue form on GitHub with
the title filled in, and the body is pasted by hand.

Usage:
    python3 scripts/feedback.py --report feedback.json
    python3 scripts/feedback.py --report feedback.json --submit --confirm <token>
    python3 scripts/feedback.py --schema

Exit code 0 = rendered or submitted, 1 = report rejected or submission failed,
2 = usage error.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from setup_feedback import (  # noqa: E402
    CONNECTORS, MAX_NOTE_CHARS, STATES, UPSTREAM, VERSION_CHECK_OUTCOMES, redact_note,
    submit, token_for,
)

MARKER = "<!-- gtm-os:feedback:v1 -->"
MAX_TITLE_CHARS = 100

# Each kind names its sections. The order is the order they render, and the prompt is
# what the skill asks the user; the reporter never fills a section on the user's behalf.
KINDS = {
    "bug": [
        ("did", "What you ran, and what you asked it to do"),
        ("happened", "What happened"),
        ("expected", "What you expected instead"),
    ],
    "feature": [
        ("want", "What you want the engine to do"),
        ("why", "What it would let you do that you cannot today"),
        ("today", "How you handle it today, if at all"),
    ],
    "skill-feedback": [
        ("worked", "What the skill did well"),
        ("did_not", "Where it fell short"),
        ("suggest", "What you would change"),
    ],
}

SURFACES = {"claude-code", "cowork", "claude-chat", "scheduled", "other"}

# The matching GitHub issue form for each kind, under .github/ISSUE_TEMPLATE/.
FORMS = {"bug": "bug_report.yml", "feature": "feature_request.yml",
         "skill-feedback": "skill_feedback.yml"}

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
AREAS = {"plugin", "setup", "docs", "scripts", "connectors", "other"}


def known_targets():
    """Skill directory names plus the non-skill areas. Read live so a new skill needs no edit here."""
    skills = {p.name for p in (REPO_ROOT / "skills").iterdir() if (p / "SKILL.md").exists()}
    return skills | AREAS


def validate(report):
    """Return (problems, cleaned). Problems are shape errors; content is redacted, not refused."""
    problems = []
    if not isinstance(report, dict):
        return ["the report must be a JSON object"], None
    cleaned = {"redactions": []}

    kind = report.get("kind")
    if not isinstance(kind, str) or kind not in KINDS:
        problems.append(f"kind must be one of {sorted(KINDS)}")
        kind = None
    cleaned["kind"] = kind

    target = report.get("target")
    targets = known_targets()
    if not isinstance(target, str) or target not in targets:
        problems.append("target must be a skill directory name or one of "
                        f"{sorted(AREAS)}")
    cleaned["target"] = target

    version = report.get("plugin_version")
    if not isinstance(version, str) or not SEMVER.match(version):
        problems.append("plugin_version must look like x.y.z")
    cleaned["plugin_version"] = version

    # Outcome of the version check (references/version-check.md); optional, never guessed.
    version_check = report.get("version_check", "not recorded")
    if not isinstance(version_check, str) or version_check not in VERSION_CHECK_OUTCOMES:
        problems.append(f"version_check must be one of {sorted(VERSION_CHECK_OUTCOMES)}")
        version_check = None
    cleaned["version_check"] = version_check

    surface = report.get("surface", "other")
    if not isinstance(surface, str) or surface not in SURFACES:
        problems.append(f"surface must be one of {sorted(SURFACES)}")
    cleaned["surface"] = surface

    connectors = report.get("connectors", [])
    if not isinstance(connectors, list):
        problems.append("connectors must be a list (it may be empty)")
        connectors = []
    cleaned["connectors"] = []
    for entry in connectors:
        if not isinstance(entry, dict):
            problems.append("each connector must be an object with name and state")
            continue
        name, state = entry.get("name"), entry.get("state")
        if not isinstance(name, str) or name not in CONNECTORS:
            problems.append(f"unknown connector name {name!r}")
        if not isinstance(state, str) or state not in STATES:
            problems.append(f"invalid connector state {state!r}")
        cleaned["connectors"].append({"name": name, "state": state})

    title = report.get("title")
    if not isinstance(title, str) or not title.strip():
        problems.append("title is required")
        title = ""
    title, kinds = redact_note(title.strip().replace("\n", " "))
    cleaned["redactions"].extend(kinds)
    if len(title) > MAX_TITLE_CHARS:
        problems.append(f"title must be <= {MAX_TITLE_CHARS} characters")
    cleaned["title"] = title

    sections = report.get("sections")
    if not isinstance(sections, dict):
        problems.append("sections must be an object keyed by section name")
        sections = {}
    cleaned["sections"] = {}
    if kind in KINDS:
        for key, _prompt in KINDS[kind]:
            text = sections.get(key)
            if not isinstance(text, str) or not text.strip():
                problems.append(f"section {key!r} is required for kind {kind!r}")
                continue
            if len(text) > MAX_NOTE_CHARS:
                problems.append(f"section {key!r} is over {MAX_NOTE_CHARS} characters; "
                                "shorten it rather than relying on truncation")
                continue
            cleaned_text, kinds = redact_note(text.strip())
            cleaned["redactions"].extend(kinds)
            cleaned["sections"][key] = cleaned_text
        extra = set(sections) - {k for k, _ in KINDS[kind]}
        if extra:
            problems.append(f"unknown section(s) for kind {kind!r}: {sorted(extra)}")

    return problems, cleaned


def render(cleaned):
    """Return (title, body). Pure formatting; nothing new is added here."""
    kind = cleaned["kind"]
    title = f"[{kind}] {cleaned['title']}"
    lines = [MARKER, "",
             f"**Kind:** {kind}  ",
             f"**Target:** `{cleaned['target']}`  ",
             f"**Plugin version:** {cleaned['plugin_version']} "
             f"(version check: {cleaned['version_check']})  ",
             f"**Surface:** {cleaned['surface']}", ""]
    if cleaned["connectors"]:
        lines += ["**Connectors at the time:**", ""]
        lines += [f"- {c['name']}: {c['state']} ({STATES[c['state']]})"
                  for c in cleaned["connectors"]]
        lines.append("")
    for key, prompt in KINDS[kind]:
        lines += [f"### {prompt}", "", cleaned["sections"][key], ""]
    count = len(cleaned["redactions"])
    if count:
        kinds = ", ".join(sorted(set(cleaned["redactions"])))
        lines.append(f"_{count} value(s) were stripped before this was shown to the "
                     f"reporter ({kinds}); each is marked in place._")
    else:
        lines.append("_Nothing needed stripping from this report._")
    lines += ["", "_Filed by the gtm-os-feedback skill. This exact title and body were shown to "
              "the reporter before filing._"]
    return title, "\n".join(lines)


def paste_url(kind, title):
    """The matching issue form on GitHub, title filled in, for a reporter without gh."""
    query = urlencode({"template": FORMS[kind], "title": title})
    return f"https://github.com/{UPSTREAM}/issues/new?{query}"


def main():
    """CLI entry point: validate, render, and, with a matching token, submit."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="Path to the feedback JSON, or - for stdin.")
    parser.add_argument("--submit", action="store_true",
                        help="File the issue upstream. Requires --confirm.")
    parser.add_argument("--confirm", metavar="TOKEN",
                        help="The token printed by the render step.")
    parser.add_argument("--schema", action="store_true", help="Print the input shape and exit.")
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    args = parser.parse_args()

    if args.schema:
        print(json.dumps({
            "kind": sorted(KINDS),
            "target": "a skill directory name, or one of " + ", ".join(sorted(AREAS)),
            "plugin_version": "x.y.z",
            "version_check": sorted(VERSION_CHECK_OUTCOMES - {"not recorded"}),
            "surface": sorted(SURFACES),
            "connectors": [{"name": sorted(CONNECTORS), "state": sorted(STATES)}],
            "title": f"one line, <= {MAX_TITLE_CHARS} chars",
            "sections": {kind: {key: prompt for key, prompt in sections}
                         for kind, sections in KINDS.items()},
        }, indent=2))
        sys.exit(0)

    if not args.report:
        print("--report is required (or --schema).", file=sys.stderr)
        sys.exit(2)

    try:
        raw = sys.stdin.read() if args.report == "-" else Path(args.report).read_text("utf-8")
        report = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read the report: {e}", file=sys.stderr)
        sys.exit(2)

    problems, cleaned = validate(report)
    if problems:
        if args.json:
            print(json.dumps({"verdict": "REJECTED", "problems": problems}, indent=2))
        else:
            print(f"REJECTED: {len(problems)} structural problem(s); nothing was sent.\n")
            for problem in problems:
                print(f"  - {problem}")
        sys.exit(1)

    title, body = render(cleaned)
    token = token_for(title + "\n" + body)

    if not args.submit:
        if args.json:
            print(json.dumps({"verdict": "READY", "title": title, "body": body,
                              "confirm_token": token,
                              "redactions": cleaned["redactions"],
                              "paste_url": paste_url(cleaned["kind"], title)}, indent=2))
        else:
            print(f"Title: {title}\n\n{body}\n")
            print("--- nothing has been sent ---")
            print("Show the body above to the reporter. To file it, run:\n")
            print(f"  python3 scripts/feedback.py --report {args.report} "
                  f"--submit --confirm {token}\n")
            print(f"Without gh, paste it here: {paste_url(cleaned['kind'], title)}")
        sys.exit(0)

    if args.confirm != token:
        message = ("Refusing to submit: no --confirm token, or it does not match this body. "
                   "Render the report first and file the exact body that was shown.")
        if args.json:
            print(json.dumps({"verdict": "UNCONFIRMED", "detail": message,
                              "expected_token": token}, indent=2))
        else:
            print(message, file=sys.stderr)
        sys.exit(1)

    code, detail = submit(title, body)
    if args.json:
        print(json.dumps({"verdict": "SUBMITTED" if code == 0 else "FAILED",
                          "detail": detail}, indent=2))
    else:
        print(detail)
    sys.exit(code)


if __name__ == "__main__":
    main()
