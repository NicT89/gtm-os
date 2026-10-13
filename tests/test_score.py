"""Tests for skills/gtm-signal-scan/scripts/score.py.

The properties worth pinning are the ones a prose rubric could not hold: unknown is never
zero-in-disguise, an account with no play is held rather than tiered, every play earns an
explicit play_fit value, and a config cannot award more than a dimension's doctrinal maximum.
Play assignment itself is the model's judgment against free-form criteria
(references/plays.md), so it is deliberately not tested here: there is nothing
deterministic to test.

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


PLAY_IDS = [p["id"] for p in json.loads(
    (ROOT / "examples" / "demo" / "plays.demo.json").read_text("utf-8"))["plays"]]


def account(**kw):
    base = {"id": "a", "name": "A", "domain": "a.example", "signal_type": "hiring",
            "signal_observed_on": "2026-08-30", "gtm_team_size": 0, "play": "first-gtm-hire",
            "headcount_growth_pct": 40, "hq_country": "US"}
    base.update(kw)
    return base


class Config(unittest.TestCase):
    def test_the_demo_config_is_valid(self):
        self.assertEqual(score.validate_config(DEMO, PLAY_IDS), [])

    def test_a_rule_above_the_dimension_maximum_is_rejected(self):
        """Otherwise a 0-100 score silently stops being one."""
        bad = copy.deepcopy(DEMO)
        bad["dimensions"]["play_fit"]["points_by_play"]["first-gtm-hire"] = 16
        self.assertTrue(any("maximum is 15" in p for p in score.validate_config(bad)))

    def test_tier_cutoffs_must_descend_and_fit_the_pass(self):
        bad = copy.deepcopy(DEMO)
        bad["tiers"] = {"excellent": 60, "good": 70, "fair": 50}
        self.assertTrue(any("must descend" in p for p in score.validate_config(bad)))
        bad["pre_tiers"] = {"excellent": 60, "good": 30, "fair": 20}
        self.assertTrue(any("above the pass maximum" in p for p in score.validate_config(bad)))

    def test_every_play_needs_play_fit_points(self):
        """A new play must not silently score 0 because nobody gave it points."""
        bad = copy.deepcopy(DEMO)
        del bad["dimensions"]["play_fit"]["points_by_play"]["new-leader"]
        self.assertTrue(any("'new-leader'" in p for p in score.validate_config(bad, PLAY_IDS)))
        self.assertEqual(score.validate_config(bad), [], "coverage is only checked against a plays file")

    def test_a_bad_decay_window_is_rejected(self):
        bad = copy.deepcopy(DEMO)
        bad["dimensions"]["signal_age"]["windows"]["hiring"]["full_points_within_days"] = 90
        self.assertTrue(score.validate_config(bad))

    def test_a_non_object_rule_is_a_problem_not_a_crash(self):
        """A list where an object belongs raised AttributeError before 1.10.0 shipped."""
        bad = copy.deepcopy(DEMO)
        bad["dimensions"]["play_fit"] = ["not", "an", "object"]
        self.assertTrue(any("play_fit" in p for p in score.validate_config(bad, PLAY_IDS)))

    def test_the_passes_sum_to_the_doctrine(self):
        self.assertEqual((score.PASS1_MAX, score.FULL_MAX), (55, 100))


class PlayFit(unittest.TestCase):
    def dim(self, result):
        return next(d for d in result["dimensions"] if d["dimension"] == "play_fit")

    def test_no_play_is_unknown_not_zero_fit(self):
        r = score.score_account(account(play=None), DEMO, AS_OF, "1")
        self.assertEqual((self.dim(r)["points"], self.dim(r)["unknown"]), (0, True))

    def test_the_assigned_play_earns_its_points(self):
        r = score.score_account(account(play="team-expansion"), DEMO, AS_OF, "1")
        self.assertEqual(self.dim(r)["points"],
                         DEMO["dimensions"]["play_fit"]["points_by_play"]["team-expansion"])

    def test_an_unrecognized_play_is_unknown_not_zero_fit(self):
        r = score.score_account(account(play="no-such-play"), DEMO, AS_OF, "1")
        self.assertEqual((self.dim(r)["points"], self.dim(r)["unknown"]), (0, True))

    def test_exclusion_uses_the_signal_types_own_ceiling(self):
        self.assertIsNotNone(score.exclusion(account(gtm_team_size=2), DEMO))
        self.assertIsNone(score.exclusion(account(signal_type="funding", gtm_team_size=2), DEMO))
        self.assertIn("competitor", score.exclusion(account(category="competitor"), DEMO))

    def test_score_py_does_not_assign_plays(self):
        """Assignment is the model's job against free-form criteria; a helper here would
        quietly reintroduce a fixed criteria vocabulary."""
        self.assertFalse(hasattr(score, "assign_motion"))
        self.assertFalse(hasattr(score, "assign_play"))


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


class LearningThreshold(unittest.TestCase):
    """learning.min_sample is optional, but when present it must be a real decision."""

    def test_absent_is_fine_and_a_positive_whole_number_is_fine(self):
        self.assertEqual(score.validate_config(DEMO), [])
        self.assertEqual(score.validate_config(dict(DEMO, learning={"min_sample": 25})), [])

    def test_anything_else_is_a_problem(self):
        for bad in ({"min_sample": 0}, {"min_sample": 2.5}, {"min_sample": True}, {}, []):
            with self.subTest(bad):
                self.assertTrue(any("learning.min_sample" in p for p in
                                    score.validate_config(dict(DEMO, learning=bad))))


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

    def test_an_account_with_no_play_is_held_not_tiered(self):
        """A tier would read as enrichment-eligible for an account whose routing is unknown."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([account(play=None)], f)
        out = self.run_cli(f.name, "--config", str(ROOT / "examples/demo/scoring.demo.json"),
                           "--as-of", "2026-09-01")
        entry = json.loads(out.stdout)["results"][0]
        self.assertIn("held", entry)
        self.assertNotIn("score", entry)

    def test_an_account_with_an_unrecognized_play_is_held_not_tiered(self):
        """A typo'd or stale play id must not tier as a zero-fit route."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([account(play="no-such-play")], f)
        out = self.run_cli(f.name, "--config", str(ROOT / "examples/demo/scoring.demo.json"),
                           "--as-of", "2026-09-01")
        entry = json.loads(out.stdout)["results"][0]
        self.assertIn("held", entry)
        self.assertNotIn("score", entry)

    def test_a_play_missing_from_the_plays_file_is_held(self):
        """With --plays, a play the config still scores but the plays file dropped is held."""
        plays = {"plays": [{"id": "first-gtm-hire"}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([account(play="team-expansion")], f)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as g:
            json.dump(plays, g)
        cfg = copy.deepcopy(DEMO)
        cfg["dimensions"]["play_fit"]["points_by_play"] = {"first-gtm-hire": 15,
                                                            "team-expansion": 8}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as h:
            json.dump(cfg, h)
        out = self.run_cli(f.name, "--config", h.name, "--plays", g.name, "--as-of", "2026-09-01")
        entry = json.loads(out.stdout)["results"][0]
        self.assertIn("held", entry)

    def test_the_clock_is_never_read(self):
        """No --as-of is a usage error, not a silent today()."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([account()], f)
        out = self.run_cli(f.name, "--config", str(ROOT / "examples/demo/scoring.demo.json"))
        self.assertEqual(out.returncode, 2)


if __name__ == "__main__":
    unittest.main()
