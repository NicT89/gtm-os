"""Pin the arithmetic two standing rules depend on.

"State the total before spending, report actual burn after" and "a run projected to exceed
its cap STOPS and asks" both need a number, and until 1.10.0 nothing produced one. So the
cases that matter are the ones where the tally would let a run past a cap, or write a
summary that misrepresents what happened.

Per CLAUDE.md, the guarantees are proved by breaking them, not by observing a green run:
MutationCoverage reintroduces each one as a defect and asserts it is caught.

Run: python3 -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_cost.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_cost import SUMMARY_METERS, summary_line, tally  # noqa: E402


def run(**overrides):
    r = {"run_id": "run-2026-09-07-beta-candidates",
         "meters": {"apollo": {"spent": 5, "cap": 10, "unit": "credits"}},
         "fields_filled": 3, "fields_proposed": 1}
    r.update(overrides)
    return r


def report_for(**overrides):
    problems, report = tally(run(**overrides))
    assert not problems, problems
    return report


class TheCapIsEnforced(unittest.TestCase):
    """The half that stops a run rather than describing it afterwards."""

    def test_within_cap_passes(self):
        self.assertEqual(report_for()["verdict"], "WITHIN_CAP")

    def test_over_cap_is_caught(self):
        r = report_for(meters={"apollo": {"spent": 11, "cap": 10}})
        self.assertEqual(r["verdict"], "OVER_CAP")
        self.assertEqual(len(r["over_cap"]), 1)

    def test_exactly_at_cap_is_not_over(self):
        """The boundary. Off by one here either blocks a legal run or permits an illegal one."""
        self.assertEqual(report_for(meters={"apollo": {"spent": 10, "cap": 10}})["verdict"],
                         "WITHIN_CAP")

    def test_a_meter_with_no_cap_is_reported_but_never_blocks(self):
        r = report_for(meters={"apollo": {"spent": 999}})
        self.assertEqual(r["verdict"], "WITHIN_CAP")
        self.assertIsNone(r["meters"]["apollo"]["cap"])

    def test_every_over_meter_is_named_not_just_the_first(self):
        r = report_for(meters={"apollo": {"spent": 11, "cap": 10},
                               "firecrawl": {"spent": 50, "cap": 20}})
        self.assertEqual(len(r["over_cap"]), 2)

    def test_one_meter_over_condemns_the_run(self):
        r = report_for(meters={"apollo": {"spent": 1, "cap": 10},
                               "firecrawl": {"spent": 50, "cap": 20}})
        self.assertEqual(r["verdict"], "OVER_CAP")


class UnitsAreNeverAddedTogether(unittest.TestCase):
    """Credits and dollars are different things; a single total would be meaningless."""

    def test_each_meter_keeps_its_own_unit(self):
        r = report_for(meters={"apollo": {"spent": 5, "unit": "credits"},
                               "actor": {"spent": 2.5, "unit": "USD"}})
        self.assertEqual(r["meters"]["apollo"]["unit"], "credits")
        self.assertEqual(r["meters"]["actor"]["unit"], "USD")

    def test_there_is_no_grand_total_field(self):
        self.assertNotIn("total", report_for())


class TheCostSummaryMatchesTheVaultFormat(unittest.TestCase):
    """The string is written into a field with a fixed shape, so it is built, not typed."""

    def test_the_three_named_meters_appear_in_order(self):
        line = report_for(meters={"firecrawl": {"spent": 20}, "apollo": {"spent": 5},
                                  "actor": {"spent": 0}})["cost_summary"]
        self.assertTrue(line.startswith("Apollo credits: 5 | Actor USD: 0 | Firecrawl credits: 20"))

    def test_a_missing_meter_is_reported_as_zero_not_omitted(self):
        """An absent meter must not shorten the line; a reader compares runs by position."""
        line = report_for(meters={"apollo": {"spent": 5}})["cost_summary"]
        for _, label in SUMMARY_METERS:
            self.assertIn(label, line)

    def test_a_complete_run_is_final(self):
        self.assertIn("Status: final", report_for(complete=True)["cost_summary"])

    def test_an_incomplete_run_is_partial_not_final(self):
        """A partial tally written as final reads as the run's whole cost forever after."""
        self.assertIn("Status: partial", report_for(complete=False)["cost_summary"])

    def test_an_unnamed_meter_is_appended_with_its_unit(self):
        line = summary_line({"openai": {"spent": 4, "unit": "USD"}}, True)
        self.assertIn("openai: 4 USD", line)


class TheWriteHalfIsCounted(unittest.TestCase):
    """Since 1.9.0 runs write too, so what went back is half the record."""

    def test_filled_and_proposed_are_carried(self):
        r = report_for(fields_filled=6, fields_proposed=2)
        self.assertEqual((r["fields_filled"], r["fields_proposed"]), (6, 2))

    def test_a_run_that_spent_and_filled_nothing_is_still_valid(self):
        """Allowed, and worth noticing. Not an error."""
        r = report_for(fields_filled=0)
        self.assertEqual(r["verdict"], "WITHIN_CAP")
        self.assertEqual(r["fields_filled"], 0)


class MalformedInputIsRejected(unittest.TestCase):
    def test_a_missing_run_id_is_rejected(self):
        self.assertTrue(tally(run(run_id="  "))[0])

    def test_no_meters_is_rejected(self):
        self.assertTrue(tally(run(meters={}))[0])

    def test_a_negative_spend_is_rejected(self):
        self.assertTrue(tally(run(meters={"apollo": {"spent": -1}}))[0])

    def test_a_non_numeric_spend_is_rejected(self):
        self.assertTrue(tally(run(meters={"apollo": {"spent": "five"}}))[0])

    def test_a_boolean_spend_is_rejected(self):
        """True is an int in Python; a bool reaching a meter is a bug, not a quantity."""
        self.assertTrue(tally(run(meters={"apollo": {"spent": True}}))[0])

    def test_a_negative_field_count_is_rejected(self):
        self.assertTrue(tally(run(fields_filled=-2))[0])

    def test_a_non_object_run_is_rejected(self):
        self.assertTrue(tally([])[0])


class MutationCoverage(unittest.TestCase):
    """Reintroduce each guarantee as a defect in an in-memory copy; assert it is caught."""

    MUTATIONS = {
        "let a run exceed its cap": ("if spent > cap:", "if spent > cap * 1000:"),
        "call a partial run final": (
            "f\"Status: {'final' if complete else 'partial'}\"",
            'f"Status: final"'),
        "accept a negative spend": ("    if value < 0:", "    if False:"),
    }

    def load_mutant(self, old, new):
        source = (REPO_ROOT / "scripts" / "run_cost.py").read_text(encoding="utf-8")
        self.assertIn(old, source, "mutation target no longer present; update the mutation")
        ns = {"__name__": "run_cost_mutant"}
        exec(compile(source.replace(old, new), "run_cost_mutant", "exec"), ns)
        return ns

    def test_every_mutation_breaks_a_guarantee(self):
        checks = {
            "let a run exceed its cap":
                lambda m: m["tally"]({"run_id": "r", "meters": {"a": {"spent": 99, "cap": 1}}}
                                     )[1]["verdict"] == "WITHIN_CAP",
            "call a partial run final":
                lambda m: "Status: final" in m["summary_line"]({"a": {"spent": 1}}, False),
            "accept a negative spend":
                lambda m: m["tally"]({"run_id": "r", "meters": {"a": {"spent": -5}}})[0] == [],
        }
        for name, (old, new) in self.MUTATIONS.items():
            with self.subTest(mutation=name):
                self.assertTrue(checks[name](self.load_mutant(old, new)),
                                f"mutation {name!r} changed nothing; it is not a real mutation")

    def test_the_real_module_holds_every_guarantee(self):
        self.assertEqual(report_for(meters={"a": {"spent": 99, "cap": 1}})["verdict"], "OVER_CAP")
        self.assertIn("Status: partial", summary_line({"a": {"spent": 1}}, False))
        self.assertTrue(tally(run(meters={"a": {"spent": -5}}))[0])


class TheCliBehaves(unittest.TestCase):
    def run_cli(self, payload, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            path = f.name
        return subprocess.run([sys.executable, str(SCRIPT), "--run", path, *args],
                              capture_output=True, text=True)

    def test_within_cap_exits_zero(self):
        proc = self.run_cli(run())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("WITHIN_CAP", proc.stdout)

    def test_over_cap_exits_one(self):
        proc = self.run_cli(run(meters={"apollo": {"spent": 99, "cap": 1}}))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("OVER CAP", proc.stdout)

    def test_malformed_input_exits_two(self):
        self.assertEqual(self.run_cli(run(meters={})).returncode, 2)

    def test_a_missing_run_argument_exits_two(self):
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT)],
                                        capture_output=True, text=True).returncode, 2)

    def test_the_summary_line_is_printed_for_pasting(self):
        self.assertIn("Cost Summary (paste into the Vault Run row)", self.run_cli(run()).stdout)

    def test_json_mode_carries_the_summary(self):
        payload = json.loads(self.run_cli(run(), "--json").stdout)
        self.assertIn("Apollo credits: 5", payload["cost_summary"])


if __name__ == "__main__":
    unittest.main()
