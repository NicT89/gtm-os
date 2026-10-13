"""One operator's plays must never ship as the engine's.

Until 1.11.0 the plugin carried Launch99's five routes (M1-M5), their live Apollo sequence
names, and the operator's personal job-search tracks, presented as engine doctrine. They moved
to that operator's own plays file. This fails if any of it comes back into a file an installed
copy loads: the sequence names, the job-search codes, or M-codes used as routing in a skill or
an example. History in CHANGELOG.md, and the one-line mention of the move in CLAUDE.md and
references/plays.md, are the only places the names may appear.

To confirm it can fail: add "M3" to any SKILL.md, or a sequence name below to an example.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OPERATOR_STRINGS = (
    "GTM Outbound AI- No Jobs Posting",
    "Founder Direct - Funding Signal",
    "(Assisted)First GTM Hire",
    "[Claude] GTM Team Expansion",
    "[Claude] First 90 Days",
    "Job Search - Hiring Manager Track",
    "Job Search - Recruiter Track",
    "JS-HM",
    "JS-REC",
)
SHIPPED = [p for pattern in ("skills/**/*", "references/*", "examples/**/*", "scripts/*",
                             "README.md", "SETUP.md", "AGENTS.md", "instance-config.example.json")
           for p in ROOT.glob(pattern) if p.is_file() and p.suffix in (".md", ".json", ".py", ".js")]


class NoOperatorPlays(unittest.TestCase):
    def test_the_scan_covers_the_shipped_files(self):
        names = {p.name for p in SHIPPED}
        self.assertIn("SKILL.md", names)
        self.assertIn("plays.demo.json", names)

    def test_no_operator_sequence_or_track_names(self):
        for path in SHIPPED:
            text = path.read_text("utf-8")
            for needle in OPERATOR_STRINGS:
                with self.subTest(file=str(path.relative_to(ROOT)), needle=needle):
                    self.assertNotIn(needle, text)

    def test_no_m_codes_in_skills_or_examples(self):
        for path in SHIPPED:
            rel = path.relative_to(ROOT).parts[0]
            if rel not in ("skills", "examples"):
                continue
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertIsNone(re.search(r"\bM[1-5]\b", path.read_text("utf-8")))


if __name__ == "__main__":
    unittest.main()
