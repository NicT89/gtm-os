"""Pin the three copies of the Get Started block to each other.

The block is deliberately duplicated into README.md, CLAUDE.md, and AGENTS.md so that
whoever lands first — a person browsing the repo, an agent reading CLAUDE.md, an agent
reading AGENTS.md — gets the same four steps without being routed somewhere else. That
redundancy is the feature and the hazard: three copies drift the moment one is edited
alone, and a stale install command is worse than no install command, because the reader
follows it.

So the drift fails the build. `references/get-started.md` is the source; the other three
must match it byte for byte, and the install commands in it must still match what the
marketplace manifest actually declares.

Run: python3 -m unittest discover -s tests -v
"""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "references" / "get-started.md"
COPIES = ["README.md", "CLAUDE.md", "AGENTS.md"]

BEGIN = "<!-- BEGIN GET STARTED -->"
END = "<!-- END GET STARTED -->"


def extract(path):
    """Return the marked block from one file, or None when it has none."""
    text = path.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        return None
    return text.split(BEGIN, 1)[1].split(END, 1)[0]


class TheBlockIsIdenticalEverywhere(unittest.TestCase):
    """Byte equality, not "roughly the same"."""

    def setUp(self):
        self.source = extract(SOURCE)
        self.assertIsNotNone(self.source, f"{SOURCE} lost its markers")

    def test_every_copy_exists(self):
        for name in COPIES:
            with self.subTest(file=name):
                path = REPO_ROOT / name
                self.assertTrue(path.is_file(), f"{name} is missing")
                self.assertIsNotNone(extract(path), f"{name} has no Get Started block")

    def test_every_copy_matches_the_source(self):
        for name in COPIES:
            with self.subTest(file=name):
                self.assertEqual(
                    extract(REPO_ROOT / name), self.source,
                    f"{name}'s Get Started block has drifted from references/get-started.md; "
                    "edit the source and re-sync rather than hand-editing one copy")

    def test_the_source_is_not_empty(self):
        """A guard on the parser: two adjacent markers would pass everything above."""
        self.assertGreater(len(self.source.strip()), 400,
                           "the source block is suspiciously short; check the markers")


class TheBlockSaysTrueThings(unittest.TestCase):
    """The content claims things the repo can verify."""

    def setUp(self):
        self.block = extract(SOURCE)

    def test_the_install_commands_match_the_marketplace_manifest(self):
        """A renamed plugin with a stale install line is the worst kind of drift."""
        manifest = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        marketplace = manifest["name"]
        plugin = manifest["plugins"][0]["name"]
        self.assertIn(f"/plugin install {plugin}@{marketplace}", self.block)

    def test_it_points_at_files_that_exist(self):
        """A backticked path in the block must resolve, or step 3 sends people nowhere."""
        for rel in re.findall(r"`((?:references/)?[A-Za-z0-9_.\-/]+\.md)`", self.block):
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), f"{rel} does not exist")

    def test_it_names_the_setup_skill_by_its_real_name(self):
        skill = "environment-setup"
        self.assertIn(skill, self.block)
        self.assertTrue((REPO_ROOT / "skills" / skill / "SKILL.md").is_file())

    def test_it_states_the_rule_that_governs_setup(self):
        """The one sentence that must survive every rewrite of this block."""
        self.assertIn("not set up almost never means not owned", self.block.lower())


if __name__ == "__main__":
    unittest.main()
