#!/usr/bin/env python3
"""Turn a setup run into a redacted report the maintainer actually receives.

The problem this solves: the environment-setup module has never been watched running
against somebody else's half-configured accounts, and that is the only place its core
claim can fail — "not set up does not mean not owned". A tester who has to remember to
write up what happened, and then send it somewhere, mostly does not. So the agent files
the report as a step of the run instead of leaving it as homework.

What reaches the issue
----------------------
Only: the checkpoint reached, the plugin version, each connector's name and its S0-S4
state, whether the run continued or stalled, whether a state was misdiagnosed, and short
free-text notes. A ladder state is a fact about the setup module, not about the tester's
business.

Sensitive values inside notes are STRIPPED, not left for a human to catch: credentials,
workspace IDs (app…, tbl…, fld…, rec…, viw…, a 24-char hex CRM field ID), email addresses,
long digit runs, and links outside vendor documentation are each replaced in place with a
visible `[redacted: <kind>]` marker. The credential patterns are imported from
scan_secrets.py rather than restated, so the two cannot drift apart.

Stripping is only safe because of the two-step flow below: the text a human approves is
the text after redaction, so nobody is ever approving something they have not read. An
earlier version rejected these notes outright for exactly that reason; binding the
approval to the redacted body is what made stripping the better answer, because a
rejected note tends to come back rewritten from memory rather than rewritten accurately.

How approval works
------------------
Two steps, so that the host's own tool-approval prompt is the acceptance gate rather than
a question the agent asks and could mis-report the answer to:

    1. python3 scripts/setup_feedback.py --report r.json
       Renders the exact issue body, redactions and all, and prints a confirmation token
       derived from that body. Sends nothing. Nothing to approve.

    2. python3 scripts/setup_feedback.py --report r.json --submit --confirm <token>
       Files it. The host shows this command for approval in the normal way.

The token is a digest of the rendered body. A body that changed after it was shown — an
edited note, a different ladder — produces a different token and the submission is
refused. That is what makes step 1 load-bearing rather than decorative: even with blanket
permission to run this script, nothing can be filed that was not first put on screen.

Usage:
    python3 scripts/setup_feedback.py --report report.json
    python3 scripts/setup_feedback.py --report report.json --submit --confirm <token>
    python3 scripts/setup_feedback.py --schema

Exit code 0 = rendered or submitted, 1 = report rejected or submission failed,
2 = usage error.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scan_secrets import PATTERNS, is_low_entropy  # noqa: E402

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

# Shapes stripped from notes wherever they appear, whatever the surrounding sentence says.
SENSITIVE = [
    # Airtable IDs are a prefix plus 14 mixed-case alphanumerics. The length is widened to
    # 12-20 so a near-miss transcription is still caught, and the two lookaheads require an
    # uppercase letter and a digit in the tail so ordinary prose ("recommendations",
    # "application") is not mangled by a rule nobody would then trust.
    ("workspace-id", re.compile(
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
TRUNCATED = " […truncated]"


def redact_note(note):
    """Return (redacted_text, [kinds_removed]).

    Every removal leaves a visible marker rather than a gap, so the reader of the rendered
    body can see that something was taken out and object before approving. A silent
    deletion would read as a complete sentence that merely says less than it did.
    """
    kinds = []

    def swap(kind):
        def _sub(_match):
            kinds.append(kind)
            return f"[redacted: {kind}]"
        return _sub

    text = note
    for kind, pattern in SENSITIVE:
        text = pattern.sub(swap(kind), text)

    # Credentials come from the same table scan_secrets.py uses, minus its low-entropy
    # escape hatch: a repetitive string is not a credential and mangling it helps nobody.
    for kind, pattern in PATTERNS:
        def _cred(match, kind=kind):
            if is_low_entropy(match.group(0)):
                return match.group(0)
            kinds.append("credential")
            return "[redacted: credential]"
        text = pattern.sub(_cred, text)

    def _url(match):
        host = match.group(1).lower()
        if host in ALLOWED_URL_HOSTS:
            return match.group(0)
        kinds.append("private-link")
        return "[redacted: private-link]"
    text = URL.sub(_url, text)

    if len(text) > MAX_NOTE_CHARS:
        text = text[:MAX_NOTE_CHARS - len(TRUNCATED)] + TRUNCATED
        kinds.append("over-length")

    return text, kinds


def validate(report):
    """Return (problems, cleaned). Problems non-empty means nothing is rendered or sent.

    Problems are STRUCTURAL only — an unknown connector, a bad ladder state, a missing
    version. Sensitive content in a note is never a problem here; it is redacted.
    """
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

    cleaned_notes, redactions = [], []
    for note in notes:
        note = str(note).strip()
        if not note:
            continue
        text, kinds = redact_note(note)
        cleaned_notes.append(text)
        redactions.extend(kinds)

    cleaned = {
        "checkpoint": checkpoint,
        "plugin_version": version,
        "connectors": cleaned_connectors,
        "outcome": outcome,
        "misdiagnosed_a_state": misdiagnosed,
        "notes": cleaned_notes,
        "redactions": redactions,
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
        "Filed by the `environment-setup` skill, with the tester's approval.",
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

    lines += ["", "---", ""]
    if cleaned["redactions"]:
        counts = {}
        for kind in cleaned["redactions"]:
            counts[kind] = counts.get(kind, 0) + 1
        summary = ", ".join(f"{n}× {kind}" for kind, n in sorted(counts.items()))
        lines.append(f"{len(cleaned['redactions'])} value(s) were stripped before this was "
                     f"rendered ({summary}); each is marked in place above.")
    else:
        lines.append("Nothing needed stripping from these notes.")
    lines.append(
        "This report carries connector names and ladder states only. Credentials, "
        "workspace IDs, email addresses, and private links are removed automatically and "
        "the redacted text is what the tester approved. See `scripts/setup_feedback.py`.")
    return title, "\n".join(lines)


def token_for(body):
    """A short digest binding an approval to the exact body that was displayed."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


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
                   "This is usually an unauthenticated gh. The rendered body can be "
                   f"pasted into https://github.com/{UPSTREAM}/issues/new instead.")
    return 0, proc.stdout.strip()


def main():
    """CLI entry point: validate, render, and — with a matching token — submit."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="Path to the report JSON, or - for stdin.")
    parser.add_argument("--submit", action="store_true",
                        help="File the issue upstream. Requires --confirm.")
    parser.add_argument("--confirm", metavar="TOKEN",
                        help="The token printed by the render step, binding this "
                             "submission to the body that was shown.")
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
            "notes": [f"free text, <= {MAX_NOTE_CHARS} chars, <= {MAX_NOTES} of them; "
                      "sensitive values are stripped automatically"],
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
            print("\nThese are shape errors, not content ones. Fix the report and run again.")
        sys.exit(1)

    title, body = render(cleaned)
    token = token_for(body)

    if not args.submit:
        if args.json:
            print(json.dumps({"verdict": "READY", "title": title, "body": body,
                              "confirm_token": token,
                              "redactions": cleaned["redactions"]}, indent=2))
        else:
            print(f"Title: {title}\n\n{body}\n")
            print("--- nothing has been sent ---")
            print("Show the body above to the tester. To file it, run:\n")
            print(f"  python3 scripts/setup_feedback.py --report {args.report} "
                  f"--submit --confirm {token}")
        sys.exit(0)

    if args.confirm != token:
        message = ("Refusing to submit: no --confirm token, or it does not match this body. "
                   "Render the report first and file the exact body that was shown. "
                   "A mismatch means the body changed after it was displayed.")
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
