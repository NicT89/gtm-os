"""Every ```json block in the repo's Markdown must parse as JSON.

Observed on the 1.13.0 PR: schema-markup shipped a JSON-LD template with `//` comments and two
`@graph` examples with `...` elisions. All three were labeled `json`, all three were meant to be
copied into a page or a validator, and all three were parse errors. CodeRabbit caught the first;
parsing every block found the other two. Nothing in CI read these blocks at all.

The rule this enforces: a block labeled `json` is a promise that it can be pasted and parsed.
Use placeholder STRING values ("YYYY-MM-DD", "SCHEMA_TYPE") rather than comments or `...`.
A block that genuinely needs comments should be labeled `jsonc`, which this test skips.

To confirm it can fail: add `// comment` inside any ```json block under skills/ and run the
suite. `JsonBlockScanner` also proves the scanner itself on in-memory input, so a regex change
that stops matching fences fails here instead of passing vacuously.

Run: python3 -m unittest discover -s tests -v
"""
import json
import re
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A fence may be indented (inside a list item). Per CommonMark, a closing fence is a line of
# backticks with nothing but whitespace after it, and an unclosed fence runs to the end of the
# document. Without both rules a line like ```extra would end the block early, and an unclosed
# block would be skipped entirely: either way invalid JSON goes unchecked.
FENCE = re.compile(r"^(?P<indent>[ \t]*)```json[ \t]*\n(?P<body>.*?)(?:^[ \t]*```+[ \t]*$|\Z)",
                   re.S | re.M)


def json_blocks(text):
    """Yield (line_number, body) for every ```json block in a Markdown string."""
    for m in FENCE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        yield line, textwrap.dedent(m.group("body"))


def markdown_files():
    """Every Markdown file in the repo, outside .git and node_modules."""
    return sorted(p for p in ROOT.rglob("*.md")
                  if ".git" not in p.parts and "node_modules" not in p.parts)


class JsonBlockScanner(unittest.TestCase):
    """The scanner must find blocks, or every repo-wide assertion below is vacuous."""

    def test_finds_a_top_level_block(self):
        """A fence at the start of a line is found."""
        self.assertEqual(len(list(json_blocks('x\n```json\n{"a": 1}\n```\n'))), 1)

    def test_finds_an_indented_block(self):
        """A fence inside a list item is found and dedented before parsing."""
        text = '- item\n\n  ```json\n  {"a": 1}\n  ```\n'
        (_, body), = json_blocks(text)
        self.assertEqual(json.loads(body), {"a": 1})

    def test_comment_inside_a_block_is_a_parse_error(self):
        """The defect this file exists for: a `//` comment does not parse."""
        (_, body), = json_blocks('```json\n{\n  // note\n  "a": 1\n}\n```\n')
        with self.assertRaises(json.JSONDecodeError):
            json.loads(body)

    def test_jsonc_blocks_are_skipped(self):
        """`jsonc` is the escape hatch for blocks that need comments."""
        self.assertEqual(list(json_blocks('```jsonc\n{ // ok\n}\n```\n')), [])

    def test_reports_the_line_the_block_starts_on(self):
        """Failures point at the opening fence's line."""
        (line, _), = json_blocks('one\ntwo\n```json\n{}\n```\n')
        self.assertEqual(line, 3)

    def test_backticks_followed_by_text_do_not_close_a_block(self):
        """A line like ```extra is content, so invalid JSON after it is still checked."""
        (_, body), = json_blocks('```json\n{}\n```extra\n// invalid\n```\n')
        self.assertIn("// invalid", body)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(body)

    def test_an_unclosed_block_runs_to_the_end_and_is_checked(self):
        """An unclosed fence is not skipped: it extends to the end of the document."""
        (_, body), = json_blocks('intro\n```json\n{"a": [...]}\n')
        with self.assertRaises(json.JSONDecodeError):
            json.loads(body)

    def test_a_longer_closing_fence_closes_the_block(self):
        """Four backticks with nothing after them are a valid closer."""
        (_, body), = json_blocks('```json\n{"a": 1}\n````\nnot json\n')
        self.assertEqual(json.loads(body), {"a": 1})


class RepoJsonBlocksParse(unittest.TestCase):
    def test_the_repo_has_json_blocks_to_check(self):
        """Guards against the scan silently finding nothing (a moved root, a broken glob)."""
        found = sum(len(list(json_blocks(p.read_text("utf-8")))) for p in markdown_files())
        self.assertGreater(found, 0)

    def test_every_json_block_parses(self):
        """Every ```json block in every Markdown file parses."""
        for path in markdown_files():
            for line, body in json_blocks(path.read_text("utf-8")):
                where = f"{path.relative_to(ROOT)}:{line}"
                with self.subTest(block=where):
                    try:
                        json.loads(body)
                    except json.JSONDecodeError as e:
                        self.fail(f"{where}: ```json block does not parse ({e}). Use "
                                  "placeholder string values, not comments or `...`; "
                                  "label it `jsonc` if it truly needs comments.")


if __name__ == "__main__":
    unittest.main()
