#!/usr/bin/env python3
"""Tally what a run spent and what it filled, and hold it to the cap it stated.

Two rules in this repo depend on arithmetic nobody was doing.

**"State the total before spending, report actual burn after."** The Vault's Cost Summary
field has a fixed format and, until 1.10.0, nothing produced it. On the 2026-09-07 run the
figure was tracked by hand in a chat window and would have been lost with the conversation.
A rule enforced by memory is a rule enforced sometimes.

**"A run projected to exceed its stated cap STOPS and asks; it does not finish and
apologize."** That requires comparing spend to cap while the run is still going, which
requires a number. This produces it, and exits non-zero the moment a meter is over.

Since 1.9.0 runs also WRITE, so the tally has a second half: what the run put back. A run
that spent credits and filled nothing is a different event from one that spent the same and
closed six gaps, and only one of them is worth repeating.

Meters are open, not an allowlist: name whatever a run actually spends. Units are per-meter
strings so `credits` and `USD` do not get silently added together.

Usage:
    python3 scripts/run_cost.py --run run.json [--json]
    python3 scripts/run_cost.py --schema

Exit code 0 = within every cap, 1 = at least one meter over its cap, 2 = usage error.
"""
import argparse
import json
import sys
from pathlib import Path

# Written to the Vault Run row verbatim. The order is fixed so two runs can be diffed by eye.
SUMMARY_METERS = (("apollo", "Apollo credits"), ("actor", "Actor USD"),
                  ("firecrawl", "Firecrawl credits"))


def number(value, label, problems):
    """Coerce to float, or record a problem. Rejects bools, which are ints in Python."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        problems.append(f"{label} must be a number, got {value!r}")
        return 0.0
    if value < 0:
        problems.append(f"{label} must not be negative, got {value}")
        return 0.0
    return float(value)


def tally(run):
    """Return (problems, report). Pure: no I/O, so the arithmetic is directly testable."""
    problems = []
    if not isinstance(run, dict):
        return [f"the run must be a JSON object, got {type(run).__name__}"], {}

    run_id = str(run.get("run_id", "")).strip()
    if not run_id:
        problems.append("run_id is required; it is the key the Vault Run row is found by")

    meters_in = run.get("meters")
    if not isinstance(meters_in, dict) or not meters_in:
        problems.append("`meters` must be a non-empty object")
        meters_in = {}

    meters, over = {}, []
    for name, meter in sorted(meters_in.items()):
        if not isinstance(meter, dict):
            problems.append(f"meter {name!r} is not an object")
            continue
        spent = number(meter.get("spent", 0), f"{name}.spent", problems)
        cap = meter.get("cap")
        unit = str(meter.get("unit", "credits")).strip() or "credits"

        entry = {"spent": spent, "unit": unit, "cap": None, "remaining": None}
        if cap is not None:
            cap = number(cap, f"{name}.cap", problems)
            entry["cap"] = cap
            entry["remaining"] = round(cap - spent, 4)
            if spent > cap:
                over.append(f"{name}: spent {spent:g} {unit}, cap was {cap:g}")
        meters[name] = entry

    # The write half. A run that spends and fills nothing is a different event.
    filled = run.get("fields_filled", 0)
    proposed = run.get("fields_proposed", 0)
    if not isinstance(filled, bool) and isinstance(filled, int) and filled >= 0:
        pass
    else:
        problems.append(f"fields_filled must be a non-negative integer, got {filled!r}")
        filled = 0
    if not isinstance(proposed, bool) and isinstance(proposed, int) and proposed >= 0:
        pass
    else:
        problems.append(f"fields_proposed must be a non-negative integer, got {proposed!r}")
        proposed = 0

    if problems:
        return problems, {}

    report = {
        "run_id": run_id,
        "meters": meters,
        "fields_filled": filled,
        "fields_proposed": proposed,
        "over_cap": over,
        "cost_summary": summary_line(meters, bool(run.get("complete", True))),
        "verdict": "OVER_CAP" if over else "WITHIN_CAP",
    }
    return [], report


def summary_line(meters, complete):
    """The Vault's fixed Cost Summary format, built rather than typed from memory.

    Status is `final` only for a completed run. A partial tally written as final is worse
    than none: it reads as the whole cost of the run forever after.
    """
    parts = [f"{label}: {meters[key]['spent']:g}" if key in meters else f"{label}: 0"
             for key, label in SUMMARY_METERS]
    extra = sorted(set(meters) - {k for k, _ in SUMMARY_METERS})
    parts += [f"{name}: {meters[name]['spent']:g} {meters[name].get('unit', 'credits')}"
              for name in extra]
    parts.append(f"Status: {'final' if complete else 'partial'}")
    return " | ".join(parts)


def render(report):
    """Human-readable tally."""
    lines = [f"Run {report['run_id']}", ""]
    for name, m in report["meters"].items():
        cap = "" if m["cap"] is None else f"  (cap {m['cap']:g}, {m['remaining']:g} left)"
        lines.append(f"  {name}: {m['spent']:g} {m['unit']}{cap}")
    lines += ["", f"  fields filled:   {report['fields_filled']}",
              f"  fields proposed: {report['fields_proposed']}", ""]

    if report["over_cap"]:
        lines.append("OVER CAP - the run should have stopped and asked:")
        lines += [f"  {o}" for o in report["over_cap"]]
        lines.append("")
    if report["fields_filled"] == 0 and any(m["spent"] > 0 for m in report["meters"].values()):
        lines.append("Note: this run spent and filled nothing. That is allowed, and it is")
        lines.append("worth knowing before repeating it.")
        lines.append("")

    lines += ["Cost Summary (paste into the Vault Run row):", f"  {report['cost_summary']}",
              "", report["verdict"]]
    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", help="Path to the run JSON, or - for stdin.")
    parser.add_argument("--schema", action="store_true", help="Print the input shape and exit.")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    args = parser.parse_args()

    if args.schema:
        print(json.dumps({
            "run_id": "run-YYYY-MM-DD-target",
            "complete": "true when the run finished; false writes Status: partial",
            "meters": {"apollo": {"spent": 0, "cap": 0, "unit": "credits"}},
            "fields_filled": 0,
            "fields_proposed": 0,
        }, indent=2))
        sys.exit(0)

    if not args.run:
        print("--run is required (or --schema).", file=sys.stderr)
        sys.exit(2)

    try:
        raw = sys.stdin.read() if args.run == "-" else Path(args.run).read_text("utf-8")
        run = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read the run: {e}", file=sys.stderr)
        sys.exit(2)

    problems, report = tally(run)
    if problems:
        if args.json:
            print(json.dumps({"verdict": "REJECTED", "problems": problems}, indent=2))
        else:
            print(f"REJECTED: {len(problems)} problem(s).\n")
            for problem in problems:
                print(f"  - {problem}")
        sys.exit(2)

    print(json.dumps(report, indent=2) if args.json else render(report))
    sys.exit(1 if report["verdict"] == "OVER_CAP" else 0)


if __name__ == "__main__":
    main()
