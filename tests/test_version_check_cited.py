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


SOURCE_URLS = [
    "https://raw.githubusercontent.com/NicT89/gtm-os/main/VERSION",
    "https://api.github.com/repos/NicT89/gtm-os/contents/VERSION",
    "https://github.com/NicT89/gtm-os/releases/latest",
]
# The response each row must carry, as the exact phrase the reference specifies.
OUTCOME_RESPONSES = {
    "Installed equals current": "gtm os x.y.z, current.",
    "Current is newer": "gtm os x.y.z installed; a.b.c is available. update the plugin when "
                        "convenient; continuing on x.y.z.",
    "Every source failed": "version check unverified: could not reach",
}


def source_order_problems(text):
    """Empty when the numbered sources are exactly SOURCE_URLS, in that order."""
    urls = numbered_sources(text)
    return [] if urls == SOURCE_URLS else [f"sources are {urls}, expected {SOURCE_URLS}"]


def outcome_row_problems(text):
    """Empty when every outcome row is present and carries its own response phrase."""
    rows = outcome_rows(text)
    problems = [f"missing outcome row: {k}" for k in OUTCOME_RESPONSES if k not in rows]
    for outcome, phrase in OUTCOME_RESPONSES.items():
        if outcome in rows and phrase not in rows[outcome].lower():
            problems.append(f"row {outcome!r} does not say {phrase!r}")
    return problems


def outcome_rows(text):
    """{outcome: response} from the outcome table, so each row is checked against its own cell."""
    rows = re.findall(r"^\| ([^|]+?) \| ([^|]+?) \|$", text, re.M)
    return {k.strip(): v.strip() for k, v in rows if k.strip() not in ("Outcome", "---")}


class TheReferenceHoldsTheChain(unittest.TestCase):
    def test_the_numbered_sources_are_exactly_the_three_urls_in_fallback_order(self):
        """Reads the list entries themselves, so a mention of a host in the prose above the
        list cannot satisfy the check, and a source pointing at another repository on the
        same host fails it."""
        self.assertEqual(source_order_problems(REFERENCE.read_text("utf-8")), [])

    def test_each_outcome_row_carries_its_response(self):
        self.assertEqual(outcome_row_problems(REFERENCE.read_text("utf-8")), [])

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

    def test_a_reordered_source_list_fails_the_check(self):
        """The same check the real test runs, on a fixture with sources 1 and 2 swapped."""
        text = REFERENCE.read_text("utf-8")
        lines = text.splitlines(True)
        i = next(k for k, l in enumerate(lines) if l.startswith(f"   1. `{SOURCE_URLS[0]}`"))
        j = next(k for k, l in enumerate(lines) if l.startswith(f"   2. `{SOURCE_URLS[1]}`"))
        lines[i], lines[j] = lines[j], lines[i]
        swapped = "".join(lines)
        self.assertNotEqual(swapped, text)
        self.assertEqual(source_order_problems(text), [])
        self.assertTrue(source_order_problems(swapped))

    def test_a_source_in_another_repository_fails_the_check(self):
        text = REFERENCE.read_text("utf-8")
        other = text.replace("NicT89/gtm-os/main/VERSION", "someone-else/gtm-os/main/VERSION")
        self.assertNotEqual(other, text)
        self.assertTrue(source_order_problems(other))

    def test_a_dropped_outcome_row_fails_the_check(self):
        text = REFERENCE.read_text("utf-8")
        lines = [l for l in text.splitlines(True) if not l.startswith("| Every source failed |")]
        dropped = "".join(lines)
        self.assertNotEqual(dropped, text)
        self.assertEqual(outcome_row_problems(text), [])
        self.assertTrue(any("missing outcome row" in p for p in outcome_row_problems(dropped)))

    def test_a_row_without_its_response_fails_the_check(self):
        text = REFERENCE.read_text("utf-8")
        for old, new in (("Version check unverified:", "Version check skipped:"),
                         ('"GTM OS X.Y.Z, current."', "the current version is unknown."),
                         ("A.B.C is available.", "A.B.C exists."),
                         ("; continuing on X.Y.Z.", ".")):
            with self.subTest(new):
                changed = text.replace(old, new)
                self.assertNotEqual(changed, text)
                self.assertTrue(outcome_row_problems(changed))

    def test_a_missing_section_is_caught(self):
        self.assertIsNone(version_section("---\nname: x\n---\n## Step 1\n\ntext\n"))


if __name__ == "__main__":
    unittest.main()
