#!/usr/bin/env python3
"""The two scoring passes must sum to 100, and motion assignment must precede scoring.

Splitting `archetype/motion fit 25` into motion fit 15 + archetype fit 10 is the kind of edit
that silently breaks a rubric: the dimensions still read plausibly, each table still looks
complete, and the total quietly stops being 100. Nothing would catch that, because no reader
adds up a table they are skimming.

The ordering half matters for the same reason finding 4 did. Motion fit is 15 points sourced
from Step 1.5, so Step 1.5 has to run first. If someone later moves motion assignment after
scoring -- the arrangement that existed until 1.9.4, where the motion was not assigned until
`gtm-blueprint` Step 3 -- those 15 points are scored against a value that does not exist yet,
and a missing input scores as a low one rather than as an error.

To confirm this can fail: change any point value, or move the `## Step 1.5` heading below
`## Step 2`.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / "skills" / "gtm-signal-scan" / "SKILL.md"
CODES = ROOT / "references" / "motion-codes.md"


class ScorePasses(unittest.TestCase):
    def setUp(self):
        self.scan = SCAN.read_text("utf-8")

    def points(self, section):
        """Sum the `| <dimension> | <points> |` cells in one pass's table."""
        return [int(m) for m in re.findall(r"^\|[^|]+\|\s*(\d+)\s*\|", section, re.M)]

    def split_sections(self):
        pass1_at = self.scan.index("**Pass 1, the FREE pre-score")
        pass2_at = self.scan.index("**Pass 2, after Step 3 enrichment")
        end = self.scan.index("`archetype/motion fit 25` was one dimension")
        return self.scan[pass1_at:pass2_at], self.scan[pass2_at:end]

    def test_the_two_passes_sum_to_one_hundred(self):
        """A rubric that does not total 100 is not a 0-100 score."""
        pass1, pass2 = self.split_sections()
        first, second = sum(self.points(pass1)), sum(self.points(pass2))
        self.assertEqual(first, 55, f"pass 1 dimensions sum to {first}")
        self.assertEqual(second, 45, f"pass 2 dimensions sum to {second}")
        self.assertEqual(first + second, 100)

    def test_motion_fit_and_archetype_fit_are_separate_dimensions(self):
        """They were one dimension worth 25 and resolve at different stages."""
        pass1, pass2 = self.split_sections()
        self.assertIn("Motion fit", pass1)
        self.assertIn("Archetype fit", pass2)
        self.assertNotIn("archetype/motion fit 25,", self.scan)

    def test_motion_assignment_precedes_scoring(self):
        """Motion fit is scored in pass 1, so the motion must already be assigned."""
        self.assertLess(
            self.scan.index("## Step 1.5: Motion assignment"),
            self.scan.index("## Step 2:"),
            "motion is assigned after the score that depends on it",
        )

    def test_the_step_points_at_the_legend_rather_than_restating_it(self):
        """Every other copy of a taxonomy in this repo drifted from its source."""
        step = self.scan[self.scan.index("## Step 1.5"):self.scan.index("## Step 2:")]
        self.assertIn("motion-codes.md", step)
        self.assertTrue(CODES.exists(), "the legend this step points at must exist")


if __name__ == "__main__":
    unittest.main()
