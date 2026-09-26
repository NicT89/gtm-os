"""Tests for skills/gtm-signal-scan/scripts/score.py.

The properties worth pinning are the ones a prose rubric could not hold: unknown is never
zero-in-disguise, a motion is never assigned on a guess, an override outranks a quadrant,
and a config cannot award more than a dimension's doctrinal maximum.

Run: python3 -m unittest discover -s tests -v
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "gtm-signal-scan" / "scripts" / "score.py"
DEMO = json.loads((ROOT / "examples" / "demo" / "scoring.demo.json").read_text("utf-8"))

spec = importlib.util.spec_from_file_location("score", SCRIPT)
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

AS_OF = date(2026, 9, 1)


def account(**kw):
    base = {"id": "a", "name": "A", "domain": "a.example", "signal_type": "hiring",
            "signal_observed_on": "2026-08-30", "gtm_team_size": 0,
            "headcount_growth_pct": 40, "hq_country": "US"}
    base.update(kw)
    return base


class Config(unittest.TestCase):
    def test_the_demo_config_is_valid(self):
        self.assertEqual(score.validate_config(DEMO), [])

    def test_a_rule_above_the_dimension_maximum_is_rejected(self):
        """Otherwise a 0-100 score silently stops being one."""
        bad = copy.deepcopy(DEMO)
        bad["dimensions"]["motion_fit"]["points_by_motion"]["first-gtm-hire"] = 16
        self.assertTrue(any("maximum is 15" in p for p in score.validate_config(bad)))

    def test_tier_cutoffs_must_descend_and_fit_the_pass(self):
        bad = copy.deepcopy(DEMO)
        bad["tiers"] = {"excellent": 60, "good": 70, "fair": 50}
        self.assertTrue(any("must descend" in p for p in score.validate_config(bad)))
        bad["pre_tiers"] = {"excellent": 60, "good": 30, "fair": 20}
        self.assertTrue(any("above the pass maximum" in p for p in score.validate_config(bad)))

    def test_every_motion_needs_motion_fit_points(self):
        bad = copy.deepcopy(DEMO)
        del bad["dimensions"]["motion_fit"]["points_by_motion"]["new-leader"]
        self.assertTrue(any("'new-leader'" in p for p in score.validate_config(bad)))

    def test_a_bad_decay_window_is_rejected(self):
        bad = copy.deepcopy(DEMO)
        bad["dimensions"]["signal_age"]["windows"]["hiring"]["full_points_within_days"] = 90
        self.assertTrue(score.validate_config(bad))

    def test_a_non_object_rule_is_a_problem_not_a_crash(self):
        """A list where an object belongs raised AttributeError before 1.10.0 shipped."""
        bad = copy.deepcopy(DEMO)
        bad["dimensions"]["motion_fit"] = ["not", "an", "object"]
        self.assertTrue(any("motion_fit" in p for p in score.validate_config(bad)))

    def test_the_passes_sum_to_the_doctrine(self):
        self.assertEqual((score.PASS1_MAX, score.FULL_MAX), (55, 100))


class Motion(unittest.TestCase):
    def test_unknown_team_state_assigns_no_motion(self):
        """Not found is not absent: the account is held, not routed on a guess."""
        out = score.assign_motion(account(gtm_team_size=None), DEMO["motions"])
        self.assertIsNone(out["motion"])
        self.assertIn("has_gtm_team", out["reason"])

    def test_a_recency_override_outranks_its_quadrant(self):
        out = score.assign_motion(account(gtm_team_size=2, gtm_leader_tenure_months=3),
                                  DEMO["motions"])
        self.assertEqual(out["motion"], "new-leader")
        out = score.assign_motion(account(gtm_team_size=2, gtm_leader_tenure_months=30),
                                  DEMO["motions"])
        self.assertEqual(out["motion"], "team-expansion")

    def test_funding_signal_means_not_hiring_unless_stated(self):
        out = score.assign_motion(account(signal_type="funding"), DEMO["motions"])
        self.assertEqual(out["motion"], "founder-direct")

    def test_exclusion_uses_the_signal_types_own_ceiling(self):
        self.assertIsNotNone(score.exclusion(account(gtm_team_size=2), DEMO))
        self.assertIsNone(score.exclusion(account(signal_type="funding", gtm_team_size=2), DEMO))
        self.assertIn("competitor", score.exclusion(account(category="competitor"), DEMO))


class Scoring(unittest.TestCase):
    def dim(self, result, name):
        return next(d for d in result["dimensions"] if d["dimension"] == name)

    def test_an_unknown_date_is_never_fresh(self):
        r = score.score_account(account(signal_observed_on=None), DEMO, AS_OF, "1")
        age = self.dim(r, "signal_age")
        self.assertEqual((age["points"], age["unknown"]), (0, True))
        self.assertIn("signal_age", r["unknown"])

    def test_a_future_date_is_unknown_not_fresh(self):
        r = score.score_account(account(signal_observed_on="2026-09-20"), DEMO, AS_OF, "1")
        self.assertTrue(self.dim(r, "signal_age")["unknown"])

    def test_signal_age_decays_between_the_window_edges(self):
        pts = [self.dim(score.score_account(account(signal_observed_on=d), DEMO, AS_OF, "1"),
                        "signal_age")["points"]
               for d in ("2026-08-25", "2026-08-01", "2026-07-01")]
        self.assertEqual(pts[0], 15)
        self.assertTrue(0 < pts[1] < 15)
        self.assertEqual(pts[2], 0)

    def test_absent_geography_is_flagged_for_pass_two(self):
        r = score.score_account(account(hq_country=None), DEMO, AS_OF, "1")
        self.assertIn("geography", r["unknown"])

    def test_pass_one_is_a_pre_score_on_its_own_scale(self):
        r = score.score_account(account(), DEMO, AS_OF, "1")
        self.assertEqual((r["kind"], r["out_of"]), ("pre-score", 55))
        self.assertEqual(len(r["dimensions"]), 4)

    def test_full_score_has_all_eight(self):
        r = score.score_account(account(latest_funding_stage="Series A", role_archetype="build",
                                        technologies=["Clay", "n8n", "HubSpot"], warm_path=True),
                                DEMO, AS_OF, "full")
        self.assertEqual(len(r["dimensions"]), 8)
        self.assertEqual(self.dim(r, "stack_overlap")["points"], 10)  # capped at max
        self.assertEqual(r["points"], 100)


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_check_config_exit_codes(self):
        self.assertEqual(self.run_cli("--check-config", str(ROOT / "examples/demo/scoring.demo.json")).returncode, 0)
        bad = copy.deepcopy(DEMO)
        bad["tiers"]["excellent"] = 200
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
        self.assertEqual(self.run_cli("--check-config", f.name).returncode, 1)

    def test_an_account_with_no_motion_is_held_not_tiered(self):
        """A tier would read as enrichment-eligible for an account whose routing is unknown."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([account(gtm_team_size=None)], f)
        out = self.run_cli(f.name, "--config", str(ROOT / "examples/demo/scoring.demo.json"),
                           "--as-of", "2026-09-01")
        entry = json.loads(out.stdout)["results"][0]
        self.assertIn("held", entry)
        self.assertNotIn("score", entry)

    def test_the_clock_is_never_read(self):
        """No --as-of is a usage error, not a silent today()."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([account()], f)
        out = self.run_cli(f.name, "--config", str(ROOT / "examples/demo/scoring.demo.json"))
        self.assertEqual(out.returncode, 2)


if __name__ == "__main__":
    unittest.main()
