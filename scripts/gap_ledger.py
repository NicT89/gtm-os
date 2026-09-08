#!/usr/bin/env python3
"""Decide, per field, whether a run may write what it learned back to the record.

The engine reads far more than it writes. It learns a company's tool stack in Step 2, uses
it once in Step 4, and lets it evaporate. The next run pays for the same research again.
That is the gap this closes, and the timing is the whole argument: DURING a run the data is
already in hand and writing it costs nothing, while a week later the same field costs a full
re-research.

So gaps are work to do, not findings to report. A reported gap nobody actions is a silent
gap with better manners.

The danger is the mirror image. A bad blueprint gets caught in review; a bad FIELD WRITE
propagates into every future run silently, and nothing downstream can tell a written fact
from a researched one. So every write is gated on two things: how well the fact is known,
and who put the current value there.

    field state \\ confidence   verified          medium            inferred
    ------------------------------------------------------------------------
    empty                       write             write if the      propose
                                                  field accepts
                                                  estimates,
                                                  else propose
    stale (machine-written)     write             propose           propose
    human-entered               propose           propose           propose
    filled and fresh            skip              skip              skip

Two rules carry that table:

**Never overwrite a human without asking.** Somebody who typed a value made a decision. The
engine may propose a replacement and may not quietly make one, whatever its confidence.

**Inferred facts never get written.** They are how a vendor's absent value becomes a number
in an email. Apollo returning `organization_revenue: 0.0` for a private company is the
worked example: written once, it is indistinguishable from a researched zero forever after.

Usage:
    python3 scripts/gap_ledger.py --record record.json [--json]
    python3 scripts/gap_ledger.py --schema

Exit code 0 = ledger produced and nothing needs a human, 1 = at least one item is queued for
a human decision, 2 = usage error.
"""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

# How old a machine-written value may be before the run should refresh it. Deliberately
# generous: churning a field every run costs credits and teaches people to ignore the diff.
DEFAULT_STALE_AFTER_DAYS = 90

CONFIDENCES = ("verified", "medium", "inferred")
PROVENANCES = ("machine", "human", "unknown")

WRITE = "write"
PROPOSE = "propose"
SKIP = "skip"


def parse_date(value):
    """Return a date from an ISO string, or None. A bad date is treated as no date."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def is_empty(value):
    """True when a field holds nothing a reader could act on.

    Whitespace counts as empty. Zero and False do NOT: a real 0 is a value, and conflating
    it with absence is the exact defect this module exists to prevent.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def classify(field, as_of):
    """Return the field's state: empty, human, stale, or fresh.

    Order matters. `human` outranks `stale`, because a human-entered value that is old is
    still a human's decision and must not be overwritten on age alone.
    """
    if is_empty(field.get("value")):
        return "empty"
    if field.get("provenance") == "human":
        return "human"

    stale_after = field.get("stale_after_days", DEFAULT_STALE_AFTER_DAYS)
    updated = parse_date(field.get("updated_at"))
    if updated is None:
        # A machine value with no date could be from any era. Treat as stale rather than
        # fresh: refreshing costs a call, while trusting an undated value costs correctness.
        return "stale"
    if (as_of - updated).days > stale_after:
        return "stale"
    return "fresh"


def decide(state, confidence, accepts_estimates):
    """Return the action for one (state, confidence) pair. This is the table in the docstring."""
    if state == "fresh":
        return SKIP, "already filled and within its freshness window"
    if state == "human":
        return PROPOSE, "a person entered this value; the engine may propose, never overwrite"

    if confidence == "verified":
        return WRITE, f"{state} field and the fact is verified by a primary source"
    if confidence == "medium":
        if state == "empty" and accepts_estimates:
            return WRITE, "empty field that is declared to accept estimates"
        if state == "empty":
            return PROPOSE, "estimate into an empty field that does not accept estimates"
        return PROPOSE, "estimate may not overwrite an existing machine value"
    return PROPOSE, "inferred facts are never written, only proposed"


def build(record, as_of=None):
    """Return the ledger for one record. Pure; no I/O, so it is trivially testable."""
    as_of = as_of or date.today()
    problems, entries = [], []

    if not isinstance(record, dict):
        return [f"the record must be a JSON object, got {type(record).__name__}"], {}

    fields = record.get("fields")
    if not isinstance(fields, list) or not fields:
        return ["`fields` must be a non-empty list"], {}

    for i, field in enumerate(fields, start=1):
        if not isinstance(field, dict):
            problems.append(f"field {i} is not an object")
            continue
        name = str(field.get("name", "")).strip()
        if not name:
            problems.append(f"field {i} has no name")
            continue

        confidence = str(field.get("confidence", "inferred")).strip().lower()
        if confidence not in CONFIDENCES:
            problems.append(f"{name}: confidence {confidence!r} not one of {list(CONFIDENCES)}")
            continue
        provenance = str(field.get("provenance", "unknown")).strip().lower()
        if provenance not in PROVENANCES:
            problems.append(f"{name}: provenance {provenance!r} not one of {list(PROVENANCES)}")
            continue

        state = classify(field, as_of)
        action, why = decide(state, confidence, bool(field.get("accepts_estimates")))
        entries.append({"name": name, "state": state, "confidence": confidence,
                        "provenance": provenance, "action": action, "reason": why})

    if problems:
        return problems, {}

    ledger = {
        "as_of": as_of.isoformat(),
        "record": record.get("record", "unnamed"),
        "write": [e for e in entries if e["action"] == WRITE],
        "propose": [e for e in entries if e["action"] == PROPOSE],
        "skip": [e for e in entries if e["action"] == SKIP],
    }
    ledger["verdict"] = "NEEDS_HUMAN" if ledger["propose"] else "CLEAR"
    return [], ledger


def render(ledger):
    """Human-readable ledger. The propose queue is what a person actually reads."""
    lines = [f"Gap ledger for {ledger['record']} as of {ledger['as_of']}", ""]

    if ledger["write"]:
        lines.append(f"WRITE ({len(ledger['write'])}) - closed by this run, no approval needed")
        for e in ledger["write"]:
            lines.append(f"  {e['name']}: {e['reason']}")
        lines.append("")

    if ledger["propose"]:
        lines.append(f"PROPOSE ({len(ledger['propose'])}) - needs a human decision")
        for e in ledger["propose"]:
            lines.append(f"  {e['name']}: {e['reason']}")
        lines.append("")

    if ledger["skip"]:
        lines.append(f"skip ({len(ledger['skip'])}) - nothing to do")
        lines.append("")

    lines.append(f"{ledger['verdict']}: "
                 + ("every gap this run can close is closed" if ledger["verdict"] == "CLEAR"
                    else f"{len(ledger['propose'])} item(s) waiting on a person"))
    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", help="Path to the record JSON, or - for stdin.")
    parser.add_argument("--as-of", help="Evaluate staleness against this date (YYYY-MM-DD).")
    parser.add_argument("--schema", action="store_true", help="Print the input shape and exit.")
    parser.add_argument("--json", action="store_true", help="Emit the ledger as JSON.")
    args = parser.parse_args()

    if args.schema:
        print(json.dumps({
            "record": "a name for the thing being audited",
            "fields": [{
                "name": "the field's name",
                "value": "current value, or null/empty when the field is blank",
                "confidence": list(CONFIDENCES),
                "provenance": list(PROVENANCES),
                "updated_at": "YYYY-MM-DD, when the current value was written",
                "stale_after_days": DEFAULT_STALE_AFTER_DAYS,
                "accepts_estimates": "true only when a vendor estimate is a valid value here",
            }],
        }, indent=2))
        sys.exit(0)

    if not args.record:
        print("--record is required (or --schema).", file=sys.stderr)
        sys.exit(2)

    try:
        raw = sys.stdin.read() if args.record == "-" else Path(args.record).read_text("utf-8")
        record = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read the record: {e}", file=sys.stderr)
        sys.exit(2)

    as_of = parse_date(args.as_of) if args.as_of else None
    if args.as_of and as_of is None:
        print(f"--as-of {args.as_of!r} is not YYYY-MM-DD.", file=sys.stderr)
        sys.exit(2)

    problems, ledger = build(record, as_of)
    if problems:
        if args.json:
            print(json.dumps({"verdict": "REJECTED", "problems": problems}, indent=2))
        else:
            print(f"REJECTED: {len(problems)} problem(s).\n")
            for problem in problems:
                print(f"  - {problem}")
        sys.exit(2)

    print(json.dumps(ledger, indent=2) if args.json else render(ledger))
    sys.exit(1 if ledger["verdict"] == "NEEDS_HUMAN" else 0)


if __name__ == "__main__":
    main()
