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


class TheReferenceHoldsTheChain(unittest.TestCase):
    def test_the_reference_names_all_three_sources_in_order(self):
        text = REFERENCE.read_text("utf-8")
        positions = [text.index(h) for h in RESTATEMENTS]
        self.assertEqual(positions, sorted(positions), "sources are not in fallback order")

    def test_the_reference_names_the_three_outcomes(self):
        text = REFERENCE.read_text("utf-8")
        for word in ("current", "available", "unverified"):
            self.assertIn(word, text.lower())


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

    def test_a_missing_section_is_caught(self):
        self.assertIsNone(version_section("---\nname: x\n---\n## Step 1\n\ntext\n"))


if __name__ == "__main__":
    unittest.main()
