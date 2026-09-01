#!/usr/bin/env python3
"""Scan the working tree and git history for committed credentials.

This replaces the audit this repo used to document inline:

    git log --all -p | grep -iE 'APOLLO|APIFY|API_KEY'   # and "must be empty"

That command cannot work. It matches vendor NAMES, so every mention of Apollo or
Apify in the documentation is a hit: on this repo it returned 271 matches, none
of them credentials. An audit that can never come back clean is worse than none,
because the first person to run it learns to ignore it.

What actually indicates a leaked credential is a value's SHAPE, or an assignment
of a long opaque value to a secret-ish name. That is what this matches.

Usage:
    python3 scripts/scan_secrets.py [--history] [--json]

    (default)   scan the working tree
    --history   also scan every commit's full diff (slower; the pre-release check)

Exit code 0 = nothing found, 1 = a candidate credential was found, 2 = usage
error. Findings print as path:line with the secret itself REDACTED, so the
output is safe to paste into an issue or a PR comment.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Each pattern is a known credential shape or a secret-ish assignment. Named so
# a finding says what it thinks it found rather than just "matched a regex".
PATTERNS = [
    ("assignment", re.compile(
        r"(?i)\b[a-z_]*(api[_-]?key|access[_-]?token|auth[_-]?token|secret|password|passwd|bearer)"
        r"[a-z_]*\b[\"']?\s*[=:]\s*[\"']?([A-Za-z0-9_\-]{16,})")),
    ("airtable-pat", re.compile(r"\bpat[A-Za-z0-9]{14}\.[A-Za-z0-9]{40,}")),
    ("apify-token", re.compile(r"\bapify_api_[A-Za-z0-9]{30,}")),
    ("firecrawl-key", re.compile(r"\bfc-[a-f0-9]{32}\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private-key-block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
]

# Documented placeholders. These are instructions to the reader, not leaks.
# Deliberately narrow: a blanket "example" substring test would hide a real
# finding that merely sat on a line mentioning an example.
PLACEHOLDER = re.compile(
    r"(?i)"
    r"X{8,}"                       # appXXXXXXXXXXXXXX and friends
    r"|your[_-]?(api[_-]?)?key"
    r"|<[a-z_ -]+>"                # <your-token>
    r"|\bexample\b"
    r"|\bplaceholder\b"
    r"|\bREDACTED\b"
)

# Minimum distinct characters before a value is credible as a secret. The test
# suite builds IDs as "0" * 24 and "app" + "a" * 14, which are structurally
# credential-shaped and obviously not credentials.
#
# This is deliberately an entropy floor rather than a "contains a long repeated
# run" rule. The repeated-run version suppressed any real token that happened to
# contain sixteen repeated characters anywhere inside it, which is a silent
# false negative: exactly the failure this whole script exists to remove. Caught
# by the tests below, which is why they use high-entropy fixtures now.
MIN_DISTINCT_CHARS = 5


def is_low_entropy(text):
    """True when a match is too repetitive to be a real credential.

    Judged on the whole alphanumeric payload, not on any substring, so a genuine
    high-entropy token containing a repeated run is not suppressed.
    """
    payload = re.sub(r"[^A-Za-z0-9]", "", text)
    return len(set(payload)) < MIN_DISTINCT_CHARS

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".ico", ".woff", ".woff2"}


def redact(text):
    """Return the match with its middle replaced, so output is safe to share."""
    text = text.strip()
    if len(text) <= 12:
        return text[:3] + "…"
    return f"{text[:6]}…{text[-4:]} ({len(text)} chars)"


def scan_text(label, text):
    """Scan one blob of text; yield findings as dicts."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        if len(line) > 4000:  # minified or binary-ish; not source we ship
            continue
        for name, pattern in PATTERNS:
            for match in pattern.finditer(line):
                hit = match.group(0)
                if PLACEHOLDER.search(hit) or is_low_entropy(hit):
                    continue
                yield {"source": label, "line": lineno, "kind": name,
                       "match": redact(hit)}


def iter_tracked_files():
    """Yield tracked files worth scanning, skipping binaries and vendor dirs."""
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return
    for rel in out.split("\0"):
        if not rel:
            continue
        path = REPO_ROOT / rel
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield rel, path


def scan_working_tree():
    """Scan every tracked file; return a findings list."""
    findings = []
    for rel, path in iter_tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(scan_text(rel, text))
    return findings


def scan_history():
    """Scan every commit's full diff; return a findings list.

    A credential deleted in a later commit is still in the history and still
    compromised, which is the whole reason to look here and not only at HEAD.
    """
    try:
        diff = subprocess.run(
            ["git", "log", "--all", "-p", "--no-color"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        return [{"source": "git history", "line": 0, "kind": "scan-error",
                 "match": str(e)}]
    return list(scan_text("git history", diff))


def main():
    """CLI entry point: scan, report redacted findings, exit non-zero on any."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true",
                        help="Also scan every commit's diff, not just the working tree.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args()

    findings = scan_working_tree()
    scanned = "working tree"
    if args.history:
        findings += scan_history()
        scanned += " and full git history"

    if args.json:
        print(json.dumps({"scanned": scanned, "findings": findings,
                          "verdict": "FAIL" if findings else "PASS"}, indent=2))
    elif findings:
        print(f"FAIL: {len(findings)} candidate credential(s) in the {scanned}.\n")
        for f in findings:
            print(f"  {f['source']}:{f['line']}  [{f['kind']}]  {f['match']}")
        print("\nA hit is a candidate, not a conviction. If it is a real credential:")
        print("  1. Rotate it at the vendor FIRST. Rewriting history does not un-leak it.")
        print("  2. Then purge it from the history and force-push.")
        print("If it is documentation, add to PLACEHOLDER in this script rather")
        print("than deleting the check. Test fixtures should be derived at run")
        print("time, not written as literals; see tests/test_scan_secrets.py.")
    else:
        print(f"ok    no candidate credentials in the {scanned}.")

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
