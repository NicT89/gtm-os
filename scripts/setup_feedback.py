#!/usr/bin/env python3
"""Turn a setup run into a redacted report the maintainer actually receives.

The problem this solves: the environment-setup module has never been watched running
against somebody else's half-configured accounts, and that is the only place its core
claim can fail — "not set up does not mean not owned". A tester who has to remember to
write up what happened, and then send it somewhere, mostly does not. So the agent files
the report as a step of the run instead of leaving it as homework.

What this script will and will not put in a public issue
-------------------------------------------------------
It emits ONLY: the checkpoint reached, the plugin version, each connector's name and its
S0-S4 state, whether the run continued or stalled, whether a state was misdiagnosed, and
free-text notes that survive the scan below. That set is deliberately narrow: a ladder
state is a fact about the setup module, not about the tester's business.

Notes are REJECTED, not silently stripped, when they contain anything that looks like a
credential, a workspace ID (app…, tbl…, fld…, rec…, a 24-char hex CRM field ID), an email
address, or a URL outside the vendor-documentation allowlist. Rejection over redaction is
deliberate: a stripped note is a note whose meaning quietly changed, and the person
approving the submission would be approving text they never read. A rejected note comes
back with the reason so the agent can rewrite it.

The credential patterns are imported from scan_secrets.py rather than restated, so the two
cannot drift apart.

Consent
-------
`--submit` posts to a PUBLIC issue tracker from the tester's own `gh` credentials. The
agent MUST show the exact rendered body and get an explicit yes first; the environment-setup
skill's checkpoint step says so. This script does not ask on its own behalf — it is not the
thing talking to the human — which is why the default is --print and submitting takes a flag.

Usage:
    python3 scripts/setup_feedback.py --report report.json            # render only
    python3 scripts/setup_feedback.py --report report.json --submit   # file the issue
    python3 scripts/setup_feedback.py --schema                        # print input shape

Exit code 0 = rendered or submitted, 1 = report rejected or submission failed,
2 = usage error.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scan_secrets import PATTERNS, is_low_entropy, redact  # noqa: E402

UPSTREAM = "NicT89/gtm-os"

# The marker is how the maintainer filters these out of the issue list without needing a
# label to exist first. Creating a label requires write access the tester does not have.
MARKER = "<!-- gtm-os:setup-feedback:v1 -->"

CHECKPOINTS = {
    "diagnosis": "after Step 1, the free diagnosis, before anything was changed",
    "config": "after instance-config.json was filled and validated",
    "proof": "after the one-target dry run proved a write",
    "abandoned": "the run stopped before finishing",
}

STATES = {
    "S0": "no account with the vendor",
    "S1": "account exists, Claude cannot reach it",
    "S2": "reachable, the engine's objects do not exist",
    "S3": "objects exist, IDs not recorded",
    "S4": "recorded and proven by a live call",
}

# Connector names are an allowlist so a free-typed vendor name cannot smuggle in a
# workspace or client identifier through this field.
CONNECTORS = {
    "apollo", "airtable", "apify", "firecrawl", "cb-insights", "brand-kit-os",
    "google-drive", "box", "onedrive", "supabase", "bigquery", "hubspot", "clay",
    "salesforce", "workflow-tool", "python-report-env", "other",
}

# Shapes that are never acceptable in a note, whatever the surrounding sentence says.
FORBIDDEN = [
    # Airtable IDs are a prefix plus 14 mixed-case alphanumerics. The length is widened to
    # 12-20 so a near-miss transcription is still caught, and the two lookaheads require an
    # uppercase letter and a digit in the tail so ordinary prose ("recommendations",
    # "application") does not match a rule that would then be ignored.
    ("airtable-object-id", re.compile(
        r"\b(?:app|tbl|fld|rec|viw)"
        r"(?=[A-Za-z0-9]{12,20}\b)(?=[A-Za-z0-9]*[A-Z])(?=[A-Za-z0-9]*\d)"
        r"[A-Za-z0-9]{12,20}\b")),
    ("crm-field-id", re.compile(r"\b[0-9a-f]{24}\b")),
    ("email-address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("long-digit-run", re.compile(r"\b\d{9,}\b")),
]

# Vendor documentation is the one kind of URL worth keeping: "their docs said X" is a real
# finding about the setup module. Anything else is a link into someone's workspace.
ALLOWED_URL_HOSTS = {
    "docs.anthropic.com", "github.com", "apollo.io", "docs.apollo.io",
    "airtable.com", "support.airtable.com", "apify.com", "docs.apify.com",
    "firecrawl.dev", "docs.firecrawl.dev",
}
URL = re.compile(r"https?://([A-Za-z0-9.-]+)(?:/\S*)?")

MAX_NOTE_CHARS = 600
MAX_NOTES = 12


def check_note(note):
    """Return a list of reasons this note may not be published; empty means it may.

    Every reason names the shape found and shows it redacted, so the agent can rewrite
    the note without the reason itself leaking what it caught.
    """
    reasons = []
    if len(note) > MAX_NOTE_CHARS:
        reasons.append(f"note is {len(note)} chars, over the {MAX_NOTE_CHARS} limit")

    for name, pattern in FORBIDDEN:
        for match in pattern.finditer(note):
            reasons.append(f"contains something shaped like {name}: {redact(match.group(0))}")

    for name, pattern in PATTERNS:
        for match in pattern.finditer(note):
            hit = match.group(0)
            if is_low_entropy(hit):
                continue
            reasons.append(f"contains something shaped like a credential ({name}): {redact(hit)}")

    for match in URL.finditer(note):
        host = match.group(1).lower()
        if host not in ALLOWED_URL_HOSTS:
            reasons.append(f"links to {host}, which is not vendor documentation")

    return reasons


def validate(report):
    """Return (problems, cleaned). Problems non-empty means nothing is submitted."""
    problems = []

    checkpoint = report.get("checkpoint")
    if checkpoint not in CHECKPOINTS:
        problems.append(f"checkpoint must be one of {sorted(CHECKPOINTS)}, got {checkpoint!r}")

    version = str(report.get("plugin_version", "")).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        problems.append(f"plugin_version must be x.y.z, got {version!r}")

    connectors = report.get("connectors") or []
    if not isinstance(connectors, list) or not connectors:
        problems.append("connectors must be a non-empty list")
        connectors = []

    cleaned_connectors = []
    for entry in connectors:
        if not isinstance(entry, dict):
            problems.append(f"connector entry is not an object: {entry!r}")
            continue
        name = str(entry.get("name", "")).strip().lower()
        state = str(entry.get("state", "")).strip().upper()
        if name not in CONNECTORS:
            problems.append(f"unknown connector {name!r}; allowed: {sorted(CONNECTORS)}")
        if state not in STATES:
            problems.append(f"connector {name!r} has state {state!r}, not one of {sorted(STATES)}")
        if name in CONNECTORS and state in STATES:
            cleaned_connectors.append({"name": name, "state": state})

    outcome = report.get("outcome")
    if outcome not in {"continued", "stalled", "abandoned"}:
        problems.append(f"outcome must be continued/stalled/abandoned, got {outcome!r}")

    misdiagnosed = report.get("misdiagnosed_a_state")
    if misdiagnosed not in (True, False, None):
        problems.append("misdiagnosed_a_state must be true, false, or null")

    notes = report.get("notes") or []
    if not isinstance(notes, list):
        problems.append("notes must be a list of strings")
        notes = []
    if len(notes) > MAX_NOTES:
        problems.append(f"{len(notes)} notes, over the {MAX_NOTES} limit")
        notes = notes[:MAX_NOTES]

    cleaned_notes = []
    for i, note in enumerate(notes, start=1):
        note = str(note).strip()
        if not note:
            continue
        reasons = check_note(note)
        if reasons:
            for reason in reasons:
                problems.append(f"note {i} cannot be published: {reason}")
            continue
        cleaned_notes.append(note)

    cleaned = {
        "checkpoint": checkpoint,
        "plugin_version": version,
        "connectors": cleaned_connectors,
        "outcome": outcome,
        "misdiagnosed_a_state": misdiagnosed,
        "notes": cleaned_notes,
    }
    return problems, cleaned


def render(cleaned):
    """Return (title, body) for the issue. Pure formatting; nothing new is added here."""
    stalled = cleaned["outcome"] != "continued"
    at = CHECKPOINTS[cleaned["checkpoint"]]
    title = (f"Setup feedback: {cleaned['outcome']} at {cleaned['checkpoint']} "
             f"(v{cleaned['plugin_version']})")

    lines = [
        MARKER,
        "Filed automatically by the `environment-setup` skill, with the tester's approval.",
        "",
        f"- **Checkpoint:** {cleaned['checkpoint']} — {at}",
        f"- **Plugin version:** {cleaned['plugin_version']}",
        f"- **Outcome:** {cleaned['outcome']}",
    ]

    if cleaned["misdiagnosed_a_state"] is True:
        lines.append("- **A connector state was misdiagnosed.** This is the failure the "
                     "module exists to prevent; see the notes.")
    elif cleaned["misdiagnosed_a_state"] is False:
        lines.append("- No connector state was misdiagnosed.")
    else:
        lines.append("- Whether a state was misdiagnosed was not established.")

    lines += ["", "## Ladder", "", "| Connector | State | Meaning |", "|---|---|---|"]
    for entry in cleaned["connectors"]:
        lines.append(f"| {entry['name']} | {entry['state']} | {STATES[entry['state']]} |")

    lines += ["", "## Notes", ""]
    if cleaned["notes"]:
        lines += [f"- {note}" for note in cleaned["notes"]]
    else:
        lines.append("_None recorded._")

    if stalled:
        lines += ["", "The run did not reach a proven write. The ladder above is where it "
                       "stopped, not where it ended up."]

    lines += ["", "---", "",
              "No IDs, credentials, prospect data, or account contents are included: this "
              "report carries connector names and ladder states only, and notes are "
              "rejected rather than stripped when they contain anything else. See "
              "`scripts/setup_feedback.py`."]
    return title, "\n".join(lines)


def submit(title, body):
    """File the issue upstream with the tester's own gh credentials."""
    if not shutil.which("gh"):
        return 1, ("gh is not on PATH, so the report cannot be filed from here. "
                   "The rendered body above can be pasted into a new issue at "
                   f"https://github.com/{UPSTREAM}/issues/new")
    proc = subprocess.run(
        ["gh", "issue", "create", "--repo", UPSTREAM, "--title", title, "--body", body],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        return 1, (f"gh could not file the issue: {detail}\n"
                   "This is usually an unauthenticated gh. The rendered body above can be "
                   f"pasted into https://github.com/{UPSTREAM}/issues/new instead.")
    return 0, proc.stdout.strip()


def main():
    """CLI entry point: validate, render, and optionally submit."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="Path to the report JSON, or - for stdin.")
    parser.add_argument("--submit", action="store_true",
                        help="File the issue upstream. Requires the tester's approval first.")
    parser.add_argument("--schema", action="store_true", help="Print the input shape and exit.")
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    args = parser.parse_args()

    if args.schema:
        print(json.dumps({
            "checkpoint": sorted(CHECKPOINTS),
            "plugin_version": "x.y.z",
            "connectors": [{"name": sorted(CONNECTORS), "state": sorted(STATES)}],
            "outcome": ["continued", "stalled", "abandoned"],
            "misdiagnosed_a_state": [True, False, None],
            "notes": [f"free text, <= {MAX_NOTE_CHARS} chars, <= {MAX_NOTES} of them"],
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
            print(f"REJECTED: {len(problems)} problem(s); nothing was sent.\n")
            for problem in problems:
                print(f"  - {problem}")
            print("\nRewrite the offending notes in terms of what happened rather than "
                  "what the value was, and run again.")
        sys.exit(1)

    title, body = render(cleaned)

    if not args.submit:
        if args.json:
            print(json.dumps({"verdict": "READY", "title": title, "body": body}, indent=2))
        else:
            print(f"Title: {title}\n\n{body}\n")
            print("--- nothing has been sent. Show this to the tester, get an explicit "
                  "yes, then re-run with --submit. ---")
        sys.exit(0)

    code, detail = submit(title, body)
    if args.json:
        print(json.dumps({"verdict": "SUBMITTED" if code == 0 else "FAILED",
                          "detail": detail}, indent=2))
    else:
        print(detail)
    sys.exit(code)


if __name__ == "__main__":
    main()
