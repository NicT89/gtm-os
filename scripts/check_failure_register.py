#!/usr/bin/env python3
"""Validate references/known-failure-modes.md.

A register of known defects is only useful if every row tells you how to catch
the defect yourself. A row without a detection method is a complaint: it warns
you that something is wrong and leaves you no cheaper off than before.

So this enforces the one rule that makes the register worth keeping: **every
entry has a non-trivial detection method.** It also pins the direction vocabulary,
because "which way does this tool lean" is the column that decides how to
compensate, and a free-text direction stops being comparable across rows.

Usage:
    python3 check_failure_register.py [path]
    python3 check_failure_register.py --self-test

Exit codes:
    0  register is well formed
    1  at least one row is malformed
    2  usage error
"""

import re
import sys
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "references" / "known-failure-modes.md"
VALID_DIRECTIONS = {"UNDER", "OVER", "STALE", "—"}
MIN_DETECTION_CHARS = 40
EXPECTED_COLUMNS = 7  # split("|") on a 5-column row yields 7: "" + 5 cells + ""


def parse_rows(text):
    """Return the register's data rows as lists of cells."""
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        if len(cells) != EXPECTED_COLUMNS:
            continue
        body = cells[1:-1]
        if body[0] in ("#", "") or set(body[0]) <= set("-: "):
            continue          # header or separator
        rows.append(body)
    return rows


def check(text):
    """Return a list of problem strings; empty means the register is sound."""
    problems = []
    rows = parse_rows(text)
    if not rows:
        problems.append("no data rows found -- the register is empty or malformed")
        return problems

    seen_numbers = set()
    for body in rows:
        number, where, direction, what, how = body
        label = "row " + (number or "?")

        if not number.isdigit():
            problems.append(label + ": id is not a number")
        elif number in seen_numbers:
            problems.append(label + ": duplicate id")
        else:
            seen_numbers.add(number)

        if not where:
            problems.append(label + ": no source named")
        if direction not in VALID_DIRECTIONS:
            problems.append(label + ": direction " + repr(direction)
                            + " is not one of " + ", ".join(sorted(VALID_DIRECTIONS)))
        if not what:
            problems.append(label + ": no description of what happens")
        if len(how) < MIN_DETECTION_CHARS:
            problems.append(label + ": detection method is missing or too thin ("
                            + str(len(how)) + " chars, minimum " + str(MIN_DETECTION_CHARS)
                            + ") -- a row without a way to catch it is a complaint")
    return problems


GOOD_ROW = ("| 1 | A source | UNDER | Something specific goes wrong here. | "
            "Run the query twice with a value nothing could match, then compare. |")
HEADER = ("| # | Where | Direction | What actually happens | How to detect it, cheaply |\n"
          "|---|---|---|---|---|\n")

SELF_TESTS = [
    ("a well formed register passes", HEADER + GOOD_ROW, 0),
    ("a row with no detection method fails",
     HEADER + "| 1 | A source | UNDER | Something goes wrong. | see above |", 1),
    ("a row with an invented direction fails",
     HEADER + GOOD_ROW.replace("UNDER", "SOMETIMES"), 1),
    ("a row with no description fails",
     HEADER + GOOD_ROW.replace("Something specific goes wrong here.", ""), 1),
    ("a duplicate id fails", HEADER + GOOD_ROW + "\n" + GOOD_ROW, 1),
    ("an empty register fails", HEADER, 1),
]


def self_test():
    failures = 0
    for name, text, expected in SELF_TESTS:
        got = 1 if check(text) else 0
        ok = got == expected
        failures += 0 if ok else 1
        print(("PASS  " if ok else "FAIL  ") + name)
    print()
    print(str(len(SELF_TESTS) - failures) + "/" + str(len(SELF_TESTS)) + " passed")
    return failures


def main(argv):
    if len(argv) == 2 and argv[1] == "--self-test":
        return 1 if self_test() else 0
    if len(argv) > 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    path = Path(argv[1]) if len(argv) == 2 else DEFAULT_PATH
    try:
        text = path.read_text()
    except OSError as exc:
        print("could not read " + str(path) + ": " + str(exc), file=sys.stderr)
        return 2
    problems = check(text)
    if problems:
        for p in problems:
            print("FAIL  " + p)
        return 1
    print("ok    " + str(len(parse_rows(text))) + " failure modes, each with a detection method.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
