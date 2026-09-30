"""The PR template must keep its "Needs you" section.

Every unticked box in a PR description is either ticked or given a row in
"Needs you" with the exact steps a person must take. The section is where that
row goes; without it, unowned tasks go back to being silent.
"""
import re
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / ".github" / "PULL_REQUEST_TEMPLATE.md"
HEADER = re.compile(r"^\|\s*#\s*\|\s*What\s*\|.*\|\s*Exact steps\s*\|\s*$", re.M)


def needs_you(text):
    """Return the body of the "## Needs you" section, or None if it is absent."""
    match = re.search(r"^## Needs you\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else None


class NeedsYouSection(unittest.TestCase):
    """The section exists and carries a table with an "Exact steps" column."""

    def test_template_has_section_with_steps_column(self):
        """The shipped template has the section and its table header."""
        body = needs_you(TEMPLATE.read_text())
        self.assertIsNotNone(body, "PR template lost its '## Needs you' section")
        self.assertRegex(body, HEADER)

    def test_missing_steps_column_is_caught(self):
        """A table without the steps column fails, so the check can fail."""
        body = needs_you("## Needs you\n\n| # | What |\n|---|---|\n\n## Next\n")
        self.assertIsNotNone(body)
        self.assertNotRegex(body, HEADER)

    def test_missing_section_is_caught(self):
        """A template with no such section returns None."""
        self.assertIsNone(needs_you("## Review findings\n\n| a |\n"))


if __name__ == "__main__":
    unittest.main()
