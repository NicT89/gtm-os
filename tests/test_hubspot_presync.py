"""Tests for scripts/hubspot_presync.py, the HubSpot pre-sync gate.

Each test breaks one rule on a copy of the shipped example and asserts that exact rule
fires, so a check that quietly stopped working would turn a test red rather than pass.

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
SCRIPT = ROOT / "scripts" / "hubspot_presync.py"
spec = importlib.util.spec_from_file_location("hubspot_presync", SCRIPT)
hp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hp)

PORTAL = json.loads((ROOT / "examples/hubspot/portal-map.example.json").read_text("utf-8"))
PLAN = json.loads((ROOT / "examples/hubspot/planned-writes.example.json").read_text("utf-8"))


def run(mutate_plan=None, mutate_portal=None):
    portal, plan = copy.deepcopy(PORTAL), copy.deepcopy(PLAN)
    if mutate_portal:
        mutate_portal(portal)
    if mutate_plan:
        mutate_plan(plan)
    return hp.check(portal, plan)


def contact(plan):
    return plan["writes"][0]["properties"]


class TheExampleIsClean(unittest.TestCase):
    def test_the_shipped_example_passes(self):
        """If the example fails, every test below proves nothing."""
        self.assertEqual(run(), ([], []))


class EachRuleFires(unittest.TestCase):
    def assertProblem(self, text, **kw):
        problems, _ = run(**kw)
        self.assertTrue(any(text in p for p in problems), problems)

    def test_unknown_object(self):
        self.assertProblem("not in the portal map",
                           mutate_plan=lambda p: p["writes"][0].update(object="leads"))

    def test_object_without_write_access(self):
        self.assertProblem("cannot write", mutate_plan=lambda p: p["writes"].append(
            {"object": "p0000_pilot_programs", "id": 5, "properties": {}}))

    def test_unknown_property(self):
        self.assertProblem("is not a property",
                           mutate_plan=lambda p: contact(p).update(gtm_typo="x"))

    def test_human_managed_property_is_never_written(self):
        self.assertProblem("human-managed",
                           mutate_plan=lambda p: contact(p).update(jobtitle="CEO"))

    def test_values_are_strings(self):
        self.assertProblem("as a string",
                           mutate_plan=lambda p: contact(p).update(gtm_persona_score=72))

    def test_number(self):
        self.assertProblem("not a number",
                           mutate_plan=lambda p: contact(p).update(gtm_persona_score="high"))

    def test_date(self):
        self.assertProblem("YYYY-MM-DD",
                           mutate_plan=lambda p: contact(p).update(gtm_play_assigned_on="9/27/26"))

    def test_enumeration_option(self):
        self.assertProblem("is not an option",
                           mutate_plan=lambda p: contact(p).update(gtm_play="P9"))

    def test_multi_select_checks_every_value(self):
        self.assertProblem("'ipo' is not an option", mutate_plan=lambda p: p["writes"][1][
            "properties"].update(gtm_signals="hiring;ipo"))

    def test_max_length(self):
        self.assertProblem("characters", mutate_plan=lambda p: contact(p).update(
            gtm_opener="x" * 2001))

    def test_create_needs_its_dedupe_key(self):
        self.assertProblem("dedupe key domain",
                           mutate_plan=lambda p: p["writes"][1]["properties"].pop("domain"))

    def test_append_only_objects_skip_the_dedupe_rule_and_only_they_do(self):
        """Removing append_only from notes must bring the dedupe problem back."""
        self.assertProblem("names no dedupe_key",
                           mutate_portal=lambda m: m["objects"]["notes"].pop("append_only"))

    def test_association_target(self):
        self.assertProblem("association target", mutate_plan=lambda p: p["writes"][2][
            "associations"].append({"object": "deals", "id": 1}))

    def test_a_bad_map_cannot_pass_writes(self):
        self.assertProblem("needs its `options`", mutate_portal=lambda m: m["objects"][
            "contacts"]["properties"]["gtm_play"].pop("options"))

    def test_every_property_needs_an_owner(self):
        """No owner could be a human-managed property written by mistake."""
        self.assertProblem("`owner` must be engine or human", mutate_portal=lambda m: m[
            "objects"]["contacts"]["properties"]["gtm_opener"].pop("owner"))

    def test_options_must_be_a_list_not_a_string(self):
        """A string would turn membership into substring matching: 'P' in 'P1,P2'."""
        def stringly(m):
            m["objects"]["contacts"]["properties"]["gtm_play"]["options"] = "P1,P2"
        self.assertProblem("non-empty list of strings", mutate_portal=stringly)

    def test_a_create_may_set_a_human_owned_property_and_an_update_may_not(self):
        problems, _ = run()  # writes[1] creates a company, setting human-owned domain + name
        self.assertEqual(problems, [])
        self.assertProblem("human-managed", mutate_plan=lambda p: p["writes"][1].update(id=77))

    def test_batch_limit_is_a_warning(self):
        def many(p):
            p["writes"] = [copy.deepcopy(p["writes"][0]) for _ in range(hp.BATCH_LIMIT + 1)]
        problems, warnings = run(mutate_plan=many)
        self.assertEqual(problems, [])
        self.assertTrue(any("split them" in w for w in warnings))


class Cli(unittest.TestCase):
    def test_exit_codes(self):
        ok = subprocess.run([sys.executable, str(SCRIPT),
                             str(ROOT / "examples/hubspot/portal-map.example.json"),
                             str(ROOT / "examples/hubspot/planned-writes.example.json")],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        bad = copy.deepcopy(PLAN)
        contact(bad)["jobtitle"] = "CEO"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
        out = subprocess.run([sys.executable, str(SCRIPT),
                              str(ROOT / "examples/hubspot/portal-map.example.json"), f.name],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT)],
                                        capture_output=True).returncode, 2)

    def test_prose_by_default_json_on_request(self):
        args = [sys.executable, str(SCRIPT), str(ROOT / "examples/hubspot/portal-map.example.json"),
                str(ROOT / "examples/hubspot/planned-writes.example.json")]
        prose = subprocess.run(args, capture_output=True, text=True)
        self.assertTrue(prose.stdout.startswith("PASS:"), prose.stdout)
        self.assertTrue(json.loads(subprocess.run(args + ["--json"], capture_output=True,
                                                  text=True).stdout)["pass"])


if __name__ == "__main__":
    unittest.main()
