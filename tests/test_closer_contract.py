#!/usr/bin/env python3
"""motion-templates.md is the only source of closer lines, and the example must obey it.

`gtm-blueprint`'s quality gate checks that each blueprint's closer matches the motion the
record is filed under. Nothing checked that the repo's own documents agreed on what the
closers ARE, and by 1.9.3 three documents disagreed:

  motion-templates.md      five templates, four distinct closer strings
  outreach-audit/SKILL.md  two closers, chosen by SIGNAL TYPE rather than motion
  examples/blueprint-hiring.md  "Documented for the hire." -- a string in neither list

The example is the format anchor for step 4 output, so its closer is the one that gets
copied. It was filed under the enterprise sales-led motion and carried a closer that motion
does not have, which means the format anchor itself would have failed the quality gate.

The assertions are containment ones, in the direction that matters: a closer NAMED in the
example must be one motion-templates DEFINES, and specifically the one belonging to the
motion the example records. The reverse direction is deliberately not asserted -- a template
whose closer no example uses is fine.

To confirm this can fail: change the example's closer line, or its recorded motion, and
`test_example_closer_matches_its_recorded_motion` fails.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "skills" / "gtm-blueprint" / "references" / "motion-templates.md"
EXAMPLE = ROOT / "examples" / "blueprint-hiring.md"
AUDIT = ROOT / "skills" / "outreach-audit" / "SKILL.md"


def closers_by_motion(text):
    """Map each `## <motion>` heading to the closer string declared under it.

    Keys are casefolded: headings are title-case ("Enterprise sales-led") and prose refers
    to the same motion in lower case, and a motion name is not case-sensitive in this repo.
    """
    out, motion = {}, None
    for line in text.splitlines():
        heading = re.match(r"^## (.+)$", line)
        if heading:
            motion = heading.group(1).strip().casefold()
        closer = re.match(r'^- Closer: "(.+)"\s*$', line)
        if closer and motion:
            out[motion] = closer.group(1)
    return out


class CloserContract(unittest.TestCase):
    def setUp(self):
        self.templates = TEMPLATES.read_text("utf-8")
        self.example = EXAMPLE.read_text("utf-8")
        self.closers = closers_by_motion(self.templates)

    def test_templates_declare_closers_at_all(self):
        """If the parse breaks, every other assertion here passes vacuously."""
        self.assertGreaterEqual(len(self.closers), 5, self.closers)

    def test_example_records_a_motion_that_exists(self):
        """A motion nobody defined cannot have a closer to check against."""
        recorded = re.search(r"Motion classified: \*\*(.+?)\*\*", self.example)
        self.assertIsNotNone(recorded, "the example no longer records its motion")
        self.assertIn(recorded.group(1).strip().casefold(), self.closers)

    def test_example_closer_matches_its_recorded_motion(self):
        """The defect itself: format anchor filed under a motion whose closer it lacked."""
        recorded = re.search(r"Motion classified: \*\*(.+?)\*\*", self.example).group(1).strip().casefold()
        expected = self.closers[recorded]
        self.assertIn(
            expected, self.example,
            f"the example is filed under '{recorded}', whose closer is {expected!r}; "
            "gtm-blueprint's quality gate would reject it",
        )

    def test_example_carries_no_closer_from_another_motion(self):
        """Two closers in one blueprint is the same defect wearing a disguise."""
        recorded = re.search(r"Motion classified: \*\*(.+?)\*\*", self.example).group(1).strip().casefold()
        body = self.example.split("## Why the closer is the one it is")[0]
        for motion, closer in self.closers.items():
            if closer != self.closers[recorded]:
                self.assertNotIn(closer, body, f"{motion}'s closer appears in the example")

    def test_outreach_audit_points_at_the_templates_instead_of_naming_closers(self):
        """It prescribed two closers by signal type, one of which existed nowhere."""
        spec = AUDIT.read_text("utf-8")
        self.assertIn("motion-templates.md", spec)
        self.assertNotIn('ending "documented for the hire"', spec)


if __name__ == "__main__":
    unittest.main()
