#!/usr/bin/env python3
"""The posts scrape must happen BEFORE the contact joins the enrichment trigger list.

This is an ORDERING rule, and ordering is the one kind of defect this repo's checks had
no way to see. Everything else it validates is presence: a field exists, a name matches,
a number is sourced. Until 1.9.3 `gtm-signal-scan` did every required thing and did two
of them in the wrong order -- it added contacts to the cascade list in Step 5 and scraped
their posts in Step 6 -- so the Apollo-side summarize-posts step, which fires on list
membership and reads the posts field, ran against an empty field, wrote an empty summary,
and reported success. A contact who posts weekly and a contact who has never posted
produce byte-identical output. Nothing downstream can tell them apart, and a validator
that only checks presence sees a fully-populated record.

So the assertions here are positional. `gtm-blueprint`'s field-provenance reference is
the source of the rule and `gtm-signal-scan`'s SKILL.md is the procedure that has to obey
it; the test reads both and fails if either the rule disappears or the procedure stops
matching it.

To confirm this check can fail, swap the scrape sub-step back below the list-add sub-step
in the skill and re-run: `test_scrape_precedes_list_add` fails on the position compare.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / "skills" / "gtm-signal-scan" / "SKILL.md"
PROVENANCE = ROOT / "skills" / "gtm-blueprint" / "references" / "field-provenance.md"


def step_five(text):
    """Return just the Step 5 body, so a mention anywhere else cannot satisfy the test."""
    match = re.search(r"^## Step 5:.*?(?=^## Step 6:)", text, re.S | re.M)
    assert match, "Step 5 heading not found in gtm-signal-scan; the test needs updating"
    return match.group(0)


class TestPostsBeforeListAdd(unittest.TestCase):
    def setUp(self):
        self.scan = SCAN.read_text("utf-8")
        self.provenance = PROVENANCE.read_text("utf-8")
        self.step5 = step_five(self.scan)

    def test_rule_still_stated_at_its_source(self):
        """field-provenance owns the rule. If it is edited away, this test is meaningless."""
        posts_pipeline = self.provenance[self.provenance.index("## Posts pipeline"):]
        self.assertIn("scrape-linkedin-posts", posts_pipeline)
        self.assertRegex(
            posts_pipeline,
            r"BEFORE the contact joins the\s+enrichment trigger list",
            "field-provenance no longer states that the scrape precedes list membership",
        )

    def test_scrape_happens_in_step_five(self):
        """Not Step 6. Step 6 composes; by then the cascade has already fired."""
        self.assertIn("scrape-linkedin-posts", self.step5)

    def test_scrape_precedes_list_add(self):
        """The whole point. Position, not presence."""
        scrape_at = self.step5.index("scrape-linkedin-posts")
        list_add_at = self.step5.index("Add to lists SEPARATELY")
        self.assertLess(
            scrape_at, list_add_at,
            "gtm-signal-scan adds contacts to the trigger list before scraping their "
            "posts; the summarize step will fire on an empty field and report success",
        )

    def test_step_five_says_how_many_sub_steps_there_are(self):
        """A count in the prose that disagrees with the list is how a step gets dropped."""
        numbered = re.findall(r"^(\d+)\. \*\*", self.step5, re.M)
        self.assertEqual(numbered, ["1", "2", "3", "4"])
        self.assertIn("four steps, not one", self.step5)


if __name__ == "__main__":
    unittest.main()
