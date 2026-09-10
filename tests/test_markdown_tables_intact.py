#!/usr/bin/env python3
"""No markdown table in this repo may be split by prose inserted between its rows.

These documents are read as schemas, not as articles. `references/research-vault.md`'s Facts
table IS the Airtable field list somebody builds the base from, and by 1.9.3 three
paragraphs had accumulated between the `Status` row and the `Entity`, `Run` and `Supersedes`
rows. Markdown ends a table at the first non-row line, so the file rendered as one table
missing its last three columns plus a second, HEADER-LESS table further down. The two links
that make a fact retrievable and the one that makes the supersede protocol possible were all
below the break.

Nothing caught it because the source text still contained every row. Reading the file, all
the information is there; reading the RENDER, three required columns are gone -- and the
render is what a person building the base sees.

The rule this asserts: a run of consecutive table-row lines must have a separator
(`|---|---|`) as its second line. An orphaned run of rows has a row there instead, which is
exactly the signature of a table that was cut in half. Fenced code blocks are skipped, since
a code sample may legitimately contain pipe-delimited lines.

To confirm this can fail: move any table's trailing rows below a paragraph and re-run.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")


def is_row(line):
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 1


def headerless_tables(text):
    """Return (line_number, first_row) for every row-run lacking a separator line."""
    found, block, start, fenced = [], [], 0, False

    def close():
        if len(block) >= 2 and not SEPARATOR.match(block[1]):
            found.append((start, block[0][:80]))

    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("```"):
            fenced = not fenced
            if block:
                close()
                block.clear()
            continue
        if fenced:
            continue
        if is_row(line):
            if not block:
                start = number
            block.append(line.strip())
        elif block:
            close()
            block.clear()
    if block:
        close()
    return found


class MarkdownTablesIntact(unittest.TestCase):
    def test_the_detector_finds_a_planted_break(self):
        """Assert the check works before trusting what it says about real files."""
        planted = ("| Field | Type |\n|---|---|\n| A | text |\n\n"
                   "Some prose that ends the table.\n\n| B | text |\n| C | text |\n")
        self.assertTrue(headerless_tables(planted))

    def test_the_detector_accepts_a_whole_table(self):
        """And that it is not simply always positive."""
        whole = "| Field | Type |\n|---|---|\n| A | text |\n| B | text |\n"
        self.assertEqual(headerless_tables(whole), [])

    def test_no_repo_document_has_a_split_table(self):
        problems = []
        for path in sorted(ROOT.rglob("*.md")):
            if ".git" in path.parts:
                continue
            for line_number, first_row in headerless_tables(path.read_text("utf-8")):
                problems.append(f"{path.relative_to(ROOT)}:{line_number}  {first_row}")
        self.assertEqual(problems, [], "table rows orphaned below prose:\n" + "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
