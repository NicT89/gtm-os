"""Keep the platform-support claim from outrunning the repo.

`references/platform-support.md` tells a user how well this engine speaks their stack.
The Native tier is a promise: skills written against that platform's real semantics, run
end to end, failure modes documented. That promise is easy to make and expensive to break,
and the natural drift is one direction only — a platform gets a paragraph, someone reads
the paragraph as support, and the row quietly says Native.

So the tier table is checked against the repository. A platform may sit in Native only
while the evidence for it is still there.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "references" / "platform-support.md"

# What "Native" has to mean, per platform, in files anyone can open. Each entry is
# (display name, [paths that must exist], [substrings that must appear in the skills or
# references]). These are the artifacts the doc's evidence column points at.
NATIVE_EVIDENCE = {
    "Apollo": (
        ["references/apollo-credit-costs.md",
         "skills/gtm-blueprint/references/field-provenance.md"],
        ["typed_custom_fields"],
    ),
    "Airtable": (
        ["references/airtable-posts-base.md", "references/research-vault.md"],
        ["AIRTABLE_FLD_"],
    ),
    "Apify": (
        ["skills/scrape-linkedin-posts/SKILL.md"],
        ["targetUrls"],
    ),
    "Firecrawl": (
        ["references/scraping-playbook.md"],
        ["Firecrawl"],
    ),
}


def section(name):
    """Return the text of one '### <name>' section of the doc."""
    text = DOC.read_text(encoding="utf-8")
    body = text.split(f"### {name}", 1)
    if len(body) == 1:
        return ""
    return body[1].split("\n### ", 1)[0].split("\n## ", 1)[0]


def haystack():
    """Everything a skill or reference says, as one blob."""
    parts = []
    for path in list((REPO_ROOT / "skills").rglob("*.md")) + \
            list((REPO_ROOT / "references").glob("*.md")) + \
            [REPO_ROOT / "instance-config.example.json"]:
        try:
            parts.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    return "\n".join(parts)


class TheDocIsWellFormed(unittest.TestCase):
    """Guards on the parser, so the assertions below cannot pass vacuously."""

    def test_the_doc_exists(self):
        self.assertTrue(DOC.is_file())

    def test_all_three_tiers_are_present(self):
        for tier in ("### Native", "### Generic", "### Not built"):
            with self.subTest(tier=tier):
                self.assertIn(tier, DOC.read_text(encoding="utf-8"))

    def test_the_native_section_is_not_empty(self):
        self.assertGreater(len(section("Native").strip()), 200)


class NativeClaimsAreBackedByTheRepo(unittest.TestCase):
    """Every Native platform's evidence must still be findable."""

    def test_each_native_platform_is_listed(self):
        native = section("Native")
        for platform in NATIVE_EVIDENCE:
            with self.subTest(platform=platform):
                self.assertIn(platform, native)

    def test_each_native_platform_has_its_evidence_files(self):
        for platform, (paths, _) in NATIVE_EVIDENCE.items():
            for rel in paths:
                with self.subTest(platform=platform, path=rel):
                    self.assertTrue(
                        (REPO_ROOT / rel).is_file(),
                        f"{platform} is listed Native but {rel} is gone; demote the row "
                        "or restore the evidence")

    def test_each_native_platform_has_its_semantics_in_the_skills(self):
        blob = haystack()
        for platform, (_, needles) in NATIVE_EVIDENCE.items():
            for needle in needles:
                with self.subTest(platform=platform, needle=needle):
                    self.assertIn(
                        needle, blob,
                        f"{platform} is listed Native but nothing in skills/ or "
                        f"references/ mentions {needle!r}")

    def test_no_platform_is_in_two_tiers(self):
        """A row copied instead of moved reads as both, and the reader believes the better one."""
        native = set(re.findall(r"\*\*([A-Za-z0-9 /.\-]+)\*\*", section("Native")))
        generic = set(re.findall(r"\*\*([A-Za-z0-9 /.\-]+)\*\*", section("Generic")))
        self.assertEqual(native & generic, set(),
                         f"listed in two tiers: {sorted(native & generic)}")

    def test_salesforce_is_not_claimed_as_native(self):
        """The worked example in the doc: vendor MCP exists, our integration does not."""
        self.assertNotIn("Salesforce", section("Native"))


class TheDocStatesTheDegradationHonestly(unittest.TestCase):
    """The two sentences a reader has to come away with."""

    def test_generic_is_described_as_working_not_broken(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("The motion runs", text)

    def test_the_doc_forbids_implying_equivalence(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("never imply it is equivalent to native", text.lower())

    def test_the_two_questions_are_distinguished_from_the_coverage_map(self):
        """The whole point: vendor MCP availability is a different fact from our support."""
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("mcp-coverage-map.md", text)
        self.assertTrue((REPO_ROOT / "references" / "mcp-coverage-map.md").is_file())


if __name__ == "__main__":
    unittest.main()
