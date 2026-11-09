"""Every skill cites the one version-check procedure instead of carrying its own.

Until 1.17.0 all thirty skills restated the fetch in four phrasings, each naming
raw.githubusercontent.com and nothing else, so a deployment that could not reach that host
got no fallback from any of them. The procedure now lives in references/version-check.md.
This test reads the claim (the reference) and the evidence (each SKILL.md) from different
files, and fails on a skill that names a fetch source of its own.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = REPO_ROOT / "references" / "version-check.md"
SKILLS = sorted(REPO_ROOT.glob("skills/*/SKILL.md"))

CITATION = "references/version-check.md"
# Any of these inside a SKILL.md means the skill is restating the procedure.
RESTATEMENTS = (
    "raw.githubusercontent.com",
    "api.github.com/repos",
    "github.com/NicT89/gtm-os/releases",
)


def version_section(text):
    """The '## Version check' section body, or None when the skill has no such heading."""
    m = re.search(r"^## Version check[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else None


def numbered_sources(text):
    """The URLs of the nested numbered list entries (three-space indent), in document order.

    Only list entries qualify; a host named in a paragraph is not a source."""
    return re.findall(r"^   \d\. `(https://[^`]+)`", text, re.M)


def outcome_rows(text):
    """{outcome: response} from the outcome table, so each row is checked against its own cell."""
    rows = re.findall(r"^\| ([^|]+?) \| ([^|]+?) \|$", text, re.M)
    return {k.strip(): v.strip() for k, v in rows if k.strip() not in ("Outcome", "---")}


class TheReferenceHoldsTheChain(unittest.TestCase):
    def test_the_numbered_sources_are_in_fallback_order(self):
        """Reads the list entries themselves, so a mention of a host in the prose above the
        list cannot satisfy the order check."""
        urls = numbered_sources(REFERENCE.read_text("utf-8"))
        self.assertEqual(len(urls), 3, urls)
        for url, host in zip(urls, RESTATEMENTS):
            self.assertIn(host, url, f"source out of order: {urls}")

    def test_each_outcome_row_carries_its_response(self):
        rows = outcome_rows(REFERENCE.read_text("utf-8"))
        expected = {
            "Installed equals current": "current",
            "Current is newer": "is available",
            "Every source failed": "unverified",
        }
        self.assertEqual(set(rows), set(expected), rows)
        for outcome, phrase in expected.items():
            with self.subTest(outcome):
                self.assertIn(phrase, rows[outcome].lower())

    def test_the_reference_says_a_failed_fetch_is_not_a_tool_failure(self):
        """gtm-blueprint stops on a failed tool call; the reference must carve the fetch out
        of that rule, or the first skill a blocked network meets will stop."""
        text = REFERENCE.read_text("utf-8")
        self.assertIn("never blocks", text)
        self.assertIn("is not a tool failure", text)


class EverySkillCitesIt(unittest.TestCase):
    def test_there_are_skills(self):
        self.assertGreater(len(SKILLS), 20)

    def test_every_skill_has_a_version_section_that_cites_the_reference(self):
        for skill in SKILLS:
            with self.subTest(skill.parent.name):
                body = version_section(skill.read_text("utf-8"))
                self.assertIsNotNone(body, "no '## Version check' section")
                self.assertIn(CITATION, body)

    def test_no_skill_restates_a_fetch_source(self):
        for skill in SKILLS:
            with self.subTest(skill.parent.name):
                text = skill.read_text("utf-8")
                for needle in RESTATEMENTS:
                    self.assertNotIn(needle, text, f"restates the chain: {needle}")


class TheCheckCanFail(unittest.TestCase):
    """Pinned on synthetic text so the two assertions are falsifiable without editing a skill."""

    def test_a_restating_section_is_caught(self):
        text = "---\nname: x\n---\n## Version check\n\nFetch https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION.\n## Next\n"
        body = version_section(text)
        self.assertNotIn(CITATION, body)
        self.assertTrue(any(n in text for n in RESTATEMENTS))

    def test_a_reordered_source_list_is_caught(self):
        text = ("2. Fetch the current version, trying each source in order:\n"
                "   1. `https://api.github.com/repos/x/contents/VERSION` (JSON)\n"
                "   2. `https://raw.githubusercontent.com/x/main/VERSION` (plain text)\n"
                "   3. `https://github.com/NicT89/gtm-os/releases/latest`\n")
        urls = numbered_sources(text)
        self.assertEqual(len(urls), 3)
        self.assertNotIn(RESTATEMENTS[0], urls[0])

    def test_a_dropped_outcome_row_is_caught(self):
        text = "| Outcome | Say |\n|---|---|\n| Installed equals current | current. |\n| Current is newer | A.B.C is available. |\n"
        self.assertNotIn("Every source failed", outcome_rows(text))

    def test_a_missing_section_is_caught(self):
        self.assertIsNone(version_section("---\nname: x\n---\n## Step 1\n\ntext\n"))


if __name__ == "__main__":
    unittest.main()
