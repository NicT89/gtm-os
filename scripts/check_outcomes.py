#!/usr/bin/env python3
"""Check outcome records and learning-loop proposals against references/outcomes.md.

The learning loop is only as honest as what it learns from. Two things make an outcome
record worth learning from, and both are universal, so both are checked here by code:

1. **It says what was true when the contact was enrolled**: the play, the account score,
   the persona score, the variant. Credit goes to that snapshot, never to today's values,
   or a play that was re-assigned last week takes credit for a reply to the old one.
2. **An unknown is marked unknown.** A snapshot field may be null only if it is listed in
   `unknown`. A silent null reads as zero to anything that averages it.

Proposals get one rule that matters more than the rest: **no proposal decides its own
threshold, and none is ever applied.** The minimum sample comes from the deployment's
scoring config (`learning.min_sample`, no default shipped), a proposal below it must say
`insufficient_data`, and `applied` is not a status this file accepts. Applying a change is
a human decision.

Outcome records reach the CRM as a note (or other activity) in a fixed, parseable block,
so the loop can read them back later from the system of record. `render_note` and
`parse_note` are that format; they round-trip.

Usage:
    python3 check_outcomes.py records.json
    python3 check_outcomes.py --proposals proposals.json --scoring scoring-config.json

Exit code 0 = valid, 1 = problems, 2 = usage error. JSON on stdout.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

EVENTS = ("reply", "positive_reply", "meeting_booked", "bounce", "unsubscribe",
          "opportunity_created", "closed_won", "closed_lost")
CRMS = ("apollo", "hubspot")
SOURCES = ("crm_native", "engine_note", "fallback_airtable", "fallback_sqlite")
RUN_MODES = ("LIVE", "FIXTURE", "SIMULATED", "PREVIEW")  # references/run-manifest.md
SNAPSHOT = ("account_score", "persona_score", "variant")
STATUSES = ("proposed", "insufficient_data")
NOTE_HEADER = "[GTM OS outcome v1]"
NOTE_FIELDS = ("event", "occurred_on", "play", "enrolled_on") + SNAPSHOT + ("run_mode",)


def parse_day(value):
    """A YYYY-MM-DD date, or None."""
    try:
        day = date.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return day if day.isoformat() == value else None


def is_number(value):
    """A real number, not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_record(i, rec):
    """Problems with one outcome record."""
    where = f"records[{i}]"
    if not isinstance(rec, dict):
        return [f"{where} is not an object"]
    problems = []
    for key, allowed in (("event", EVENTS), ("crm", CRMS), ("source", SOURCES),
                         ("run_mode", RUN_MODES)):
        if rec.get(key) not in allowed:
            problems.append(f"{where}: `{key}` must be one of {', '.join(allowed)}")
    if not rec.get("contact_id") and not rec.get("account_id"):
        problems.append(f"{where}: needs a contact_id or an account_id")
    if not isinstance(rec.get("play"), str) or not rec["play"].strip():
        problems.append(f"{where}: `play` is required; an outcome with no play credits nothing")
    occurred, enrolled = parse_day(rec.get("occurred_on")), parse_day(rec.get("enrolled_on"))
    if occurred is None:
        problems.append(f"{where}: `occurred_on` must be a YYYY-MM-DD date")
    if enrolled is None:
        problems.append(f"{where}: `enrolled_on` must be a YYYY-MM-DD date (the snapshot's date)")
    if occurred and enrolled and occurred < enrolled:
        problems.append(f"{where}: occurred_on is before enrolled_on")
    unknown = rec.get("unknown", [])
    if not isinstance(unknown, list):
        problems.append(f"{where}: `unknown` must be a list")
        unknown = []
    for key in SNAPSHOT:
        if key not in rec:
            problems.append(f"{where}: `{key}` is missing; write null and list it in `unknown`")
            continue
        value = rec[key]
        if value is None:
            if key not in unknown:
                problems.append(f"{where}: {key} is null but not listed in `unknown`; "
                                "a silent null reads as zero")
        elif key in ("account_score", "persona_score") and not is_number(value):
            problems.append(f"{where}: {key} must be a number or null")
        elif key == "variant" and not isinstance(value, str):
            problems.append(f"{where}: variant must be a string or null")
    return problems


def check_records(doc):
    """Problems with a records file: a JSON list of outcome records."""
    if not isinstance(doc, list):
        return ["the records file must be a JSON list"]
    problems = []
    for i, rec in enumerate(doc):
        problems.extend(check_record(i, rec))
    return problems


def check_proposals(doc, scoring):
    """Problems with a proposals file, judged against the scoring config's threshold."""
    learning = scoring.get("learning") if isinstance(scoring, dict) else None
    min_sample = learning.get("min_sample") if isinstance(learning, dict) else None
    if not isinstance(min_sample, int) or isinstance(min_sample, bool) or min_sample < 1:
        return ["the scoring config has no learning.min_sample; set it to the smallest "
                "sample your team will act on (no default is shipped)"]
    proposals = doc.get("proposals") if isinstance(doc, dict) else None
    if not isinstance(proposals, list):
        return ["the proposals file must be an object with a `proposals` list"]
    problems = []
    for i, prop in enumerate(proposals):
        where = f"proposals[{i}]"
        if not isinstance(prop, dict):
            problems.append(f"{where} is not an object")
            continue
        status = prop.get("status")
        if status not in STATUSES:
            problems.append(f"{where}: `status` must be one of {', '.join(STATUSES)}; "
                            "applying a change is a human decision, never a status")
        for key in ("target", "change", "hypothesis"):
            if not isinstance(prop.get(key), str) or not prop[key].strip():
                problems.append(f"{where}: `{key}` is required")
        size = prop.get("sample_size")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            problems.append(f"{where}: `sample_size` must be a whole number")
            continue
        if status == "proposed" and size < min_sample:
            problems.append(f"{where}: proposed on {size} outcomes, below the deployment's "
                            f"minimum of {min_sample}; mark it insufficient_data")
        if status == "insufficient_data" and size >= min_sample:
            problems.append(f"{where}: {size} outcomes meets the minimum of {min_sample}; "
                            "it is not insufficient")
        evidence = prop.get("evidence")
        if not isinstance(evidence, dict) or not evidence:
            problems.append(f"{where}: `evidence` must name the counts it rests on")
        elif not all(isinstance(v, int) and not isinstance(v, bool) for v in evidence.values()):
            problems.append(f"{where}: every evidence value must be a count")
    return problems


def render_note(rec):
    """The fixed block an outcome takes when written to a CRM note."""
    lines = [NOTE_HEADER]
    for key in NOTE_FIELDS:
        value = rec.get(key)
        lines.append(f"{key}: {'unknown' if value is None else value}")
    return "\n".join(lines)


def parse_note(text, crm, contact_id=None, account_id=None):
    """Read an outcome record back out of a note written by render_note, or None."""
    lines = [ln.strip() for ln in (text or "").strip().splitlines()]
    if not lines or lines[0] != NOTE_HEADER:
        return None
    fields = dict(ln.split(": ", 1) for ln in lines[1:] if ": " in ln)
    rec = {"crm": crm, "contact_id": contact_id, "account_id": account_id,
           "source": "engine_note", "unknown": []}
    for key in NOTE_FIELDS:
        raw = fields.get(key)
        if raw is None or raw == "unknown":
            rec[key] = None
            if key in SNAPSHOT:
                rec["unknown"].append(key)
        elif key in ("account_score", "persona_score"):
            try:
                rec[key] = float(raw) if "." in raw else int(raw)
            except ValueError:
                rec[key] = raw  # left as text so check_record reports it
        else:
            rec[key] = raw
    return rec


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser()
    p.add_argument("records", nargs="?")
    p.add_argument("--proposals")
    p.add_argument("--scoring")
    args = p.parse_args()
    if bool(args.records) == bool(args.proposals) or (args.proposals and not args.scoring):
        print("usage: check_outcomes.py records.json | --proposals FILE --scoring FILE",
              file=sys.stderr)
        sys.exit(2)
    paths = [args.records] if args.records else [args.proposals, args.scoring]
    docs = []
    for path in paths:
        try:
            docs.append(json.loads(Path(path).read_text("utf-8")))
        except (OSError, json.JSONDecodeError) as e:
            print(f"Cannot read {path}: {e}", file=sys.stderr)
            sys.exit(2)
    problems = check_records(docs[0]) if args.records else check_proposals(*docs)
    print(json.dumps({"file": paths[0], "valid": not problems, "problems": problems},
                     indent=2))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
