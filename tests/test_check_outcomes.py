"""Tests for scripts/check_outcomes.py: outcome records and learning-loop proposals.

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
SCRIPT = ROOT / "scripts" / "check_outcomes.py"
spec = importlib.util.spec_from_file_location("check_outcomes", SCRIPT)
co = importlib.util.module_from_spec(spec)
spec.loader.exec_module(co)

RECORD = {
    "event": "meeting_booked", "occurred_on": "2026-09-24", "crm": "hubspot",
    "contact_id": "1001", "account_id": "2001", "play": "first-gtm-hire",
    "enrolled_on": "2026-09-10", "account_score": 64, "persona_score": None,
    "variant": "A", "unknown": ["persona_score"], "source": "engine_note", "run_mode": "LIVE",
}
SCORING = {"learning": {"min_sample": 30}}
PROPOSAL = {"target": "dimensions.signal_age", "change": "narrow the hiring window",
            "hypothesis": "older reqs reply less", "sample_size": 40,
            "evidence": {"replies": 6, "sent": 40}, "status": "proposed"}


def record_problems(**changes):
    rec = copy.deepcopy(RECORD)
    for k, v in changes.items():
        if v is KeyError:
            rec.pop(k)
        else:
            rec[k] = v
    return co.check_records([rec])


def proposal_problems(scoring=SCORING, **changes):
    prop = dict(PROPOSAL, **changes)
    return co.check_proposals({"proposals": [prop]}, scoring)


class Records(unittest.TestCase):
    def test_a_good_record_passes(self):
        self.assertEqual(co.check_records([RECORD]), [])

    def test_each_rule_fires(self):
        cases = {
            "must be one of": dict(event="opened"),
            "needs a contact_id": dict(contact_id=None, account_id=None),
            "credits nothing": dict(play=""),
            "before enrolled_on": dict(occurred_on="2026-09-01"),
            "YYYY-MM-DD": dict(enrolled_on="Sep 10"),
            "silent null": dict(unknown=[]),
            "a number or null": dict(account_score="64"),
            "is missing": dict(variant=KeyError),
        }
        for text, change in cases.items():
            with self.subTest(text):
                problems = record_problems(**change)
                self.assertTrue(any(text in p for p in problems), problems)


class NoteFormat(unittest.TestCase):
    def test_render_then_parse_round_trips(self):
        note = co.render_note(RECORD)
        back = co.parse_note(note, "hubspot", "1001", "2001")
        self.assertEqual(co.check_records([back]), [])
        for key in co.NOTE_FIELDS:
            self.assertEqual(back[key], RECORD[key], key)
        self.assertEqual(back["unknown"], ["persona_score"])

    def test_a_note_without_the_header_is_not_an_outcome(self):
        self.assertIsNone(co.parse_note("event: reply", "hubspot"))


class Proposals(unittest.TestCase):
    def test_a_good_proposal_passes(self):
        self.assertEqual(proposal_problems(), [])

    def test_no_threshold_no_proposals(self):
        """The threshold is the deployment's decision; none is shipped."""
        self.assertIn("no learning.min_sample", proposal_problems(scoring={})[0])

    def test_below_the_minimum_must_say_so(self):
        self.assertTrue(any("mark it insufficient_data" in p
                            for p in proposal_problems(sample_size=10)))
        self.assertEqual(proposal_problems(sample_size=10, status="insufficient_data"), [])

    def test_insufficient_cannot_be_claimed_above_the_minimum(self):
        self.assertTrue(any("not insufficient" in p
                            for p in proposal_problems(status="insufficient_data")))

    def test_applied_is_never_a_status(self):
        self.assertTrue(any("human decision" in p for p in proposal_problems(status="applied")))

    def test_evidence_is_counts(self):
        self.assertTrue(any("must be a count" in p
                            for p in proposal_problems(evidence={"rate": 0.15})))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                              text=True)

    def dump(self, obj):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(obj, f)
        return f.name

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(self.dump([RECORD])).returncode, 0)
        self.assertEqual(self.run_cli(self.dump([dict(RECORD, play="")])).returncode, 1)
        self.assertEqual(self.run_cli("--proposals", self.dump({"proposals": [PROPOSAL]}),
                                      "--scoring", self.dump(SCORING)).returncode, 0)
        self.assertEqual(self.run_cli().returncode, 2)


if __name__ == "__main__":
    unittest.main()
