#!/usr/bin/env python3
"""Syntax-check a Workflow-tool script, which no stock parser will do correctly.

`scripts/fanout_workflow.js` is a script BODY that the Workflow tool wraps in an
async function before executing. That wrapper is what makes its top-level
`return` and `await` legal and what injects `args`, `log`, `phase`, `agent`, and
`pipeline`. The file is therefore not a standalone ES module, and the obvious
ways to check it all fail:

  node --check file.js    Silently exits 0. Node bails out of syntax checking
                          entirely once it sees `export` in a .js file, so this
                          reports success on a file with a real syntax error in
                          it. Verified on Node v22. This is the trap: it looks
                          like the file is checked when nothing was checked.
  node --check file.mjs   Parses as a module and rejects the top-level `return`,
                          which is required by the Workflow contract.
  eslint                  `parserOptions.ecmaFeatures.globalReturn` permits a
                          top-level return but is incompatible with
                          sourceType: module, which `export const meta` forces.

So this script makes the one transformation that reconciles them: it rewrites
the single top-level `return` into an assignment, then parses the result as a
real ES module. Everything else, every brace, template literal, and arrow
function, is checked exactly as written. Only the intentional deviation is
neutralized, and only for the duration of the check; the file on disk is never
modified.

Usage:
    python3 scripts/check_workflow_script.py [path ...]

Defaults to scripts/fanout_workflow.js. Exit code 0 = parses, 1 = syntax error,
2 = usage error or node unavailable.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ["scripts/fanout_workflow.js"]

# A `return` at column zero: the top-level return that the Workflow harness
# consumes. Indented returns are inside functions and are left alone.
TOP_LEVEL_RETURN = re.compile(r"^return\b", re.MULTILINE)


def neutralize(source):
    """Rewrite top-level `return` as an assignment; return (source, count).

    Only column-zero returns are touched. An indented one is inside a function
    and is already legal, so rewriting it would change what gets checked.
    """
    return TOP_LEVEL_RETURN.subn("const __workflow_result =", source)


def check(path):
    """Parse one workflow script as a module after neutralizing its return.

    Returns a list of problem strings; empty means the file parses.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"{path}: cannot read: {e}"]

    neutralized, count = neutralize(source)
    if count == 0:
        # Not fatal, but worth saying: a workflow script with no top-level
        # return produces no result for the invoking session to read.
        print(f"note  {path}: no top-level return found; the workflow yields nothing")

    with tempfile.TemporaryDirectory() as tmp:
        # .mjs forces real module parsing. A .js extension is what makes node
        # skip the check entirely once it sees `export`.
        target = Path(tmp) / (path.stem + ".mjs")
        target.write_text(neutralized, encoding="utf-8")
        proc = subprocess.run(
            ["node", "--check", str(target)],
            capture_output=True, text=True,
        )

    if proc.returncode == 0:
        return []

    detail = (proc.stderr or proc.stdout).strip()
    # Map the temp path back to the real one so the error is clickable.
    detail = detail.replace(str(target), str(path))
    return [f"{path}: syntax error\n{detail}"]


def main():
    """CLI entry point: check each target and report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=None,
                        help="Workflow scripts to check. Defaults to the known ones.")
    args = parser.parse_args()

    if not shutil.which("node"):
        print("Cannot check: node is not on PATH.", file=sys.stderr)
        sys.exit(2)

    targets = [Path(p) for p in args.paths] if args.paths else [
        REPO_ROOT / p for p in DEFAULT_TARGETS
    ]

    problems = []
    for path in targets:
        if not path.is_file():
            problems.append(f"{path}: no such file")
            print(f"FAIL  {path}")
            continue
        found = check(path)
        problems.extend(found)
        print(f"{'FAIL' if found else 'ok  '}  {path}")

    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    print(f"\nAll {len(targets)} workflow script(s) parse.")


if __name__ == "__main__":
    main()
