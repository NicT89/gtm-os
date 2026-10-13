"""Tests for skills/play-builder/scripts/check_plays.py.

The checker enforces the SHAPE of a plays file and deliberately nothing about content: plays
are organization-specific, so their criteria are free text judged against guidance
(references/play-fields.md). Each rule here is one that is the same for every organization.

Run: python3 -m unittest discover -s tests -v
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "play-builder" / "scripts" / "check_plays.py"
spec = importlib.util.spec_from_file_location("check_plays", SCRIPT)
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)

DEMO = json.loads((ROOT / "examples" / "demo" / "plays.demo.json").read_text("utf-8"))
KEYS = cp.apollo_field_keys()


def problems_of(mutate):
    doc = copy.deepcopy(DEMO)
    mutate(doc)
    return cp.check(doc, KEYS)[0]


class Valid(unittest.TestCase):
    def test_the_demo_plays_pass_with_an_illustrative_warning(self):
        problems, warnings = cp.check(DEMO, KEYS)
        self.assertEqual(problems, [])
        self.assertTrue(any("illustrative" in w for w in warnings))

    def test_content_is_never_judged(self):
        """Any sentence passes: whether it is a GOOD criterion is the model's call."""
        def m(d):
            d["plays"][0]["entry_criteria"] = "Clinics that opened a second location in the last year, per their site."
        self.assertEqual(problems_of(m), [])


class ShapeRules(unittest.TestCase):
    def test_a_keyword_is_not_a_criterion(self):
        self.assertTrue(problems_of(lambda d: d["plays"][0].update(entry_criteria="hiring")))

    def test_codes_are_unique(self):
        def m(d):
            d["plays"][1]["code"] = d["plays"][0]["code"]
        self.assertTrue(any("used by another play" in p for p in problems_of(m)))

    def test_apollo_names_carry_the_code(self):
        def wrong_code(d):
            d["plays"][0]["apollo"]["sequence"] = "(P9) [Claude] Something"
        self.assertTrue(any("must start with (P1)" in p for p in problems_of(wrong_code)))

    def test_a_human_managed_name_is_a_warning_not_a_failure(self):
        """A play may route to a list a human built; it just must not be edited by us."""
        doc = copy.deepcopy(DEMO)
        doc["plays"][0]["apollo"]["account_list"] = "(P1) Team Buyers"
        problems, warnings = cp.check(doc, KEYS)
        self.assertEqual(problems, [])
        self.assertTrue(any("human-managed" in w for w in warnings))

    def test_an_unnamed_apollo_object_is_a_warning_not_a_failure(self):
        doc = copy.deepcopy(DEMO)
        doc["plays"][0]["apollo"]["sequence"] = ""
        problems, warnings = cp.check(doc, KEYS)
        self.assertEqual(problems, [])
        self.assertTrue(any("sequence" in w for w in warnings))

    def test_standard_fields_must_be_real_keys(self):
        def m(d):
            d["plays"][0]["fields"]["standard"].append("APOLLO_CF_CONTACT_OPENR")
        self.assertTrue(any("OPENR" in p for p in problems_of(m)))

    def test_exclusive_with_must_name_a_real_play(self):
        self.assertTrue(problems_of(lambda d: d["plays"][0].update(exclusive_with=["ghost"])))
        self.assertTrue(problems_of(lambda d: d["plays"][0].update(exclusive_with=[d["plays"][0]["id"]])))

    def test_priority_must_be_a_number(self):
        self.assertTrue(problems_of(lambda d: d["plays"][0].update(priority="high")))

    def test_custom_fields_need_an_object(self):
        def m(d):
            d["plays"][0]["fields"]["custom"][0]["object"] = "deal"
        self.assertTrue(problems_of(m))


class Cli(unittest.TestCase):
    def run_cli(self, doc):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(doc, f)
        return subprocess.run([sys.executable, str(SCRIPT), f.name], capture_output=True, text=True)

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(DEMO).returncode, 0)
        bad = copy.deepcopy(DEMO)
        bad["plays"][0]["entry_criteria"] = "funding"
        self.assertEqual(self.run_cli(bad).returncode, 1)
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT)], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
