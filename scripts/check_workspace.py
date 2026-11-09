#!/usr/bin/env python3
"""Check a deployment workspace against the shape gtm-onboard lays down.

The onboarding sequence has an audit gate between "the workspace exists" and "fill in the
brand context": nothing is written into brand files until the structure that will hold
them is right. This script is that gate. It checks SHAPE, never content: a folder exists,
a file has front matter with the fields the contract names, a brand fact carries a label,
the Project-side instance summary carries no resolved identifier. Whether the brand voice
is any good is the interview's job, not this script's.

What it checks
--------------
1. The folders in references/workspace-schema.md exist (list in SCHEMA_DIRS).
2. `_index/instance.md` exists and contains no value that looks like a resolved ID
   (Airtable base/table/field ids, 24-hex CRM ids, long digit runs). The real IDs live in
   instance-config.json on the filesystem; the Project summary never carries them.
3. Every file in the brand folder has YAML front matter with `entity`, `source`
   (files | brand-kit-os), `verified` (YYYY-MM-DD) and `provenance_default`
   (KNOWN | INFERRED | UNVERIFIED), and `README.md` is present.
4. Every line in a brand file that asserts a number carries one of the three labels,
   headings included. A number without a label is the "invented number" class the repo
   forbids, so it fails. The check is per line: the contract (brand-context.md) is one fact
   per line, and a line carrying two facts and one label is a writing error this script
   cannot see.
5. `--instructions-pasted yes|no|not-applicable` is recorded as an input, not detected: the
   agent confirms it through project_info and passes it in. "no" is a failure;
   "not-applicable" is the no-Project path (Cowork folder or Claude Code with no Project
   attached), where the rules live in `_index/overview.md` instead, and passes.

Usage:
    python3 scripts/check_workspace.py --workspace <dir> [--brand-dir brand] \\
        --instructions-pasted yes|no|not-applicable [--json]

Exit code 0 = pass, 1 = one or more failures, 2 = usage error.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_DIRS = ["_index", "runs", "audit-log", "sequences", "research"]
INDEX_FILES = ["instance.md", "overview.md", "pending-tasks.md"]
BRAND_FILES = [
    "README.md", "company-profile.md", "voice-and-expression.md", "audiences.md",
    "personas.md", "products.md", "competitors.md", "objections.md",
    "proof-and-quotes.md", "governance.md",
]
SOURCES = {"files", "brand-kit-os"}
LABELS = {"KNOWN", "INFERRED", "UNVERIFIED"}
# "yes" and "not-applicable" pass; "no" fails. See the module docstring, item 5.
PASTED_STATES = {"yes", "no", "not-applicable"}
LABEL_RE = re.compile(r"\b(KNOWN|INFERRED|UNVERIFIED)\b")
# A line that asserts a quantity. One digit counts ("3 days" is a claim), and so does a
# quantity that ends a sentence ("Customers: 40.") or starts a hyphenated word ("a 3-day
# setup"). NOT_QUANTITY_RES strip the shapes that carry digits without asserting anything
# (URLs and links, dates, versions, list markers) before NUMBER_RE runs. Deliberately loose
# otherwise; the contract says every fact is labeled anyway.
NOT_QUANTITY_RES = [
    re.compile(r"https?://\S+"),            # URLs, including the target of a markdown link
    re.compile(r"\]\([^)\s]+\)"),             # any markdown link target, including a relative path
    # a bare path: the segment before the slash starts with a letter, dot or tilde
    # (brand/release-5.md, ./brand/x, ~/work/y), so a fraction (3/4), a fraction with a unit
    # (3/4-day) or a pair of quantities ($5k/$10k) is left for the quantity check
    re.compile(r"(?<!\S)[A-Za-z.~][^\s/]*/\S+"),
    re.compile(r"\S+\.(?:md|json|py|js|txt|csv|html|pdf|ya?ml)\b"),  # a bare file name
    # dates and timestamps: 2026-11, 2026-11-08, 2026-11-08T09:30:00Z, and a bare 09:30
    re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?(?:T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?Z?)?\b"),
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),
    # versions: v2.1 or 1.17.0. A bare "3.5" is a quantity, not a version, so two dots or
    # a v prefix are required.
    re.compile(r"\bv\d+(?:\.\d+){1,3}\b|\b\d+(?:\.\d+){2,3}\b"),
    re.compile(r"^\d+\.\s"),                 # a list marker at the start of the line
]
# A quantity: an optionally signed integer or decimal, optionally a fraction (3/4),
# optionally a unit suffix (%, percent, k/m/bn/x in either case), not glued to a word or a
# path segment. Dates, timestamps, versions and list markers were stripped above, so a
# hyphen before a digit here is a minus sign or a range, both of which are claims.
_UNIT = r"(?:\s?%|\s?percent\b|(?:bn|[kKmMBb])\b|x\b)?"
_NUM = r"\$?\d+(?:[.,]\d+)?" + _UNIT
NUMBER_RE = re.compile(r"(?<![\w/.])-?" + _NUM + r"(?:/" + _NUM + r")?(?![\w/]|[.,]\d)")


def asserts_a_quantity(line):
    """True when the line carries a digit run that reads as a quantity."""
    for rx in NOT_QUANTITY_RES:
        line = rx.sub(" ", line)
    return bool(NUMBER_RE.search(line))
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Shapes that are resolved identifiers and must never reach the Project summary.
ID_RES = [
    ("airtable-id", re.compile(r"\b(?:app|tbl|fld|viw|rec|sel)[A-Za-z0-9]{14}\b")),
    ("hex-id", re.compile(r"\b[0-9a-f]{24}\b")),
    ("digit-run", re.compile(r"\b\d{9,}\b")),
]


def unquote(value):
    """Strip one pair of matching quotes: `source: "files"` is the same value as `source: files`."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def front_matter(text):
    """Return (dict, body) for a leading YAML block of simple key: value lines, else (None, text)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    block = text[4:end]
    fm = {}
    for line in block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = unquote(v.split("#", 1)[0].strip())
    return fm, text[end + 4:]


def check_brand_file(path):
    """Return the shape problems of one brand file: front matter, and a label on every quantity."""
    problems = []
    fm, body = front_matter(path.read_text("utf-8"))
    if fm is None:
        return [f"{path.name}: no front matter"]
    for key in ("entity", "source", "verified", "provenance_default"):
        if not fm.get(key):
            problems.append(f"{path.name}: front matter lacks {key}")
    if fm.get("source") and fm["source"] not in SOURCES:
        problems.append(f"{path.name}: source must be one of {sorted(SOURCES)}")
    if fm.get("verified") and not DATE_RE.match(fm["verified"]):
        problems.append(f"{path.name}: verified must be YYYY-MM-DD")
    if fm.get("provenance_default") and fm["provenance_default"] not in LABELS:
        problems.append(f"{path.name}: provenance_default must be one of {sorted(LABELS)}")
    if path.name == "README.md":
        return problems
    for n, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("|--"):
            continue
        if asserts_a_quantity(stripped) and not LABEL_RE.search(stripped):
            problems.append(f"{path.name}:{n}: a number with no KNOWN/INFERRED/UNVERIFIED label")
    return problems


def check(workspace, brand_dir, instructions_pasted):
    """Return the list of failures (empty means pass)."""
    problems = []
    ws = Path(workspace)
    if not ws.is_dir():
        return [f"workspace {workspace} is not a directory"]
    for d in SCHEMA_DIRS:
        if not (ws / d).is_dir():
            problems.append(f"missing folder {d}/")
    for f in INDEX_FILES:
        if not (ws / "_index" / f).is_file():
            problems.append(f"missing _index/{f}")
    instance = ws / "_index" / "instance.md"
    if instance.is_file():
        text = instance.read_text("utf-8")
        for kind, rx in ID_RES:
            if rx.search(text):
                problems.append(f"_index/instance.md carries a resolved identifier ({kind}); "
                                "those live only in instance-config.json")
    brand = ws / brand_dir
    if not brand.is_dir():
        problems.append(f"missing brand folder {brand_dir}/")
    else:
        for name in BRAND_FILES:
            p = brand / name
            if not p.is_file():
                problems.append(f"missing {brand_dir}/{name}")
            else:
                problems.extend(f"{brand_dir}/{x}" for x in check_brand_file(p))
    if instructions_pasted not in PASTED_STATES:
        problems.append(f"--instructions-pasted must be one of {sorted(PASTED_STATES)}")
    elif instructions_pasted == "no":
        problems.append("project instructions not confirmed pasted (project_info shows them empty, "
                        "or the agent did not confirm)")
    return problems


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, help="The deployment workspace root.")
    parser.add_argument("--brand-dir", default="brand",
                        help="The brand folder name ({BRAND_CONTEXT_DIR}); default brand.")
    parser.add_argument("--instructions-pasted", choices=sorted(PASTED_STATES), required=True,
                        help="yes: project_info confirmed the Project instructions are set; "
                             "no: it did not; not-applicable: no Project is attached.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    problems = check(args.workspace, args.brand_dir, args.instructions_pasted)
    verdict = "PASS" if not problems else "FAIL"
    if args.json:
        print(json.dumps({"verdict": verdict, "problems": problems,
                          "workspace": str(Path(args.workspace).resolve()),
                          "brand_dir": args.brand_dir,
                          "instructions_pasted": args.instructions_pasted}, indent=2))
    else:
        print(f"{verdict}: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
