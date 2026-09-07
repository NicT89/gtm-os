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
         "skills/gtm-blueprint/references/field-provenance.md",
         "skills/gtm-blueprint/SKILL.md"],
        ["typed_custom_fields", "APOLLO_CF_CONTACT_BLUEPRINT"],
    ),
    "Airtable": (
        ["references/airtable-posts-base.md", "references/research-vault.md",
         "skills/scrape-linkedin-posts/SKILL.md"],
        ["AIRTABLE_FLD_", "AIRTABLE_POSTS_BASE_ID"],
    ),
    "Apify": (
        ["skills/scrape-linkedin-posts/SKILL.md"],
        ["targetUrls", "APIFY_POSTS_ACTOR"],
    ),
    "Firecrawl": (
        ["references/scraping-playbook.md", "skills/company-deep-research/SKILL.md"],
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


def evidence_text(paths):
    """The named evidence artifacts for one platform, as one blob.

    This deliberately reads ONLY the files the doc's evidence column points at, plus the
    config example. An earlier version scanned every markdown file in skills/ and
    references/ — which included platform-support.md itself, so every needle was present in
    the claim document and the test passed even with the real evidence deleted. That is the
    check-that-cannot-fail this repo has already been bitten by twice.
    """
    parts = []
    for rel in list(paths) + ["instance-config.example.json"]:
        path = REPO_ROOT / rel
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

    def test_each_native_platform_has_its_semantics_in_its_own_evidence(self):
        for platform, (paths, needles) in NATIVE_EVIDENCE.items():
            blob = evidence_text(paths)
            for needle in needles:
                with self.subTest(platform=platform, needle=needle):
                    self.assertIn(
                        needle, blob,
                        f"{platform} is listed Native but {needle!r} appears in none of "
                        f"its cited evidence files ({', '.join(paths)}); demote the row "
                        "or restore the evidence")

    def test_the_claim_document_is_not_its_own_evidence(self):
        """A guard on the guard: platform-support.md must never be read as evidence."""
        for _, (paths, _) in NATIVE_EVIDENCE.items():
            for rel in paths:
                self.assertNotIn("platform-support", rel,
                                 "a platform cannot cite the claim document as its proof")

    def test_no_platform_is_in_two_tiers(self):
        """A row copied instead of moved reads as both, and the reader believes the better one."""
        tiers = {name: set(re.findall(r"\*\*([A-Za-z0-9 /.\-]+)\*\*", section(name)))
                 for name in ("Native", "Generic", "Not built")}
        for first, second in (("Native", "Generic"), ("Native", "Not built"),
                              ("Generic", "Not built")):
            with self.subTest(pair=(first, second)):
                overlap = tiers[first] & tiers[second]
                self.assertEqual(overlap, set(),
                                 f"listed in both {first} and {second}: {sorted(overlap)}")

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
