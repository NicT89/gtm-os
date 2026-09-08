"""Pin every cell of the write gate, and the two rules that carry it.

This module decides whether the engine may write to a customer's CRM. A wrong decision here
does not get caught downstream: a bad blueprint is reviewed before it sends, but a bad field
write propagates into every future run silently, and nothing can later tell a written fact
from a researched one.

So the whole decision table is asserted cell by cell rather than spot-checked, and the two
load-bearing rules get their own tests: a human's value is never overwritten, and an
inferred fact is never written at all. Per CLAUDE.md, each of those is proved by breaking
the thing it protects and watching the assertion fail, not by observing a green run.

Run: python3 -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "gap_ledger.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gap_ledger import (  # noqa: E402
    CONFIDENCES, DEFAULT_STALE_AFTER_DAYS, PROPOSE, PROVENANCES, SKIP, WRITE,
    build, classify, decide, is_empty,
)

AS_OF = date(2026, 9, 8)
FRESH = (AS_OF - timedelta(days=10)).isoformat()
OLD = (AS_OF - timedelta(days=DEFAULT_STALE_AFTER_DAYS + 10)).isoformat()


def field(**overrides):
    """A machine-written, fresh, verified field. Overrides make it the case under test."""
    f = {"name": "Tech Stack Details", "value": "HubSpot, Snowflake", "confidence": "verified",
         "provenance": "machine", "updated_at": FRESH}
    f.update(overrides)
    return f


def ledger_for(*fields):
    problems, ledger = build({"record": "test", "fields": list(fields)}, AS_OF)
    assert not problems, problems
    return ledger


def actions(ledger):
    return {e["name"]: e["action"] for group in ("write", "propose", "skip")
            for e in ledger[group]}


class TheDecisionTableIsCompleteAndExact(unittest.TestCase):
    """Every (state, confidence) pair, asserted individually."""

    TABLE = {
        ("empty", "verified"): WRITE,
        ("empty", "medium"): PROPOSE,      # accepts_estimates False
        ("empty", "inferred"): PROPOSE,
        ("stale", "verified"): WRITE,
        ("stale", "medium"): PROPOSE,
        ("stale", "inferred"): PROPOSE,
        ("unattributed", "verified"): PROPOSE,
        ("unattributed", "medium"): PROPOSE,
        ("unattributed", "inferred"): PROPOSE,
        ("human", "verified"): PROPOSE,
        ("human", "medium"): PROPOSE,
        ("human", "inferred"): PROPOSE,
        ("fresh", "verified"): SKIP,
        ("fresh", "medium"): SKIP,
        ("fresh", "inferred"): SKIP,
    }

    def test_every_cell(self):
        for (state, confidence), expected in self.TABLE.items():
            with self.subTest(state=state, confidence=confidence):
                action, why = decide(state, confidence, accepts_estimates=False)
                self.assertEqual(action, expected)
                self.assertTrue(why, "every decision must carry a reason")

    def test_the_table_covers_every_confidence(self):
        """A guard on the table: a new confidence level must not silently default to write."""
        covered = {c for _, c in self.TABLE}
        self.assertEqual(covered, set(CONFIDENCES))

    def test_an_estimate_may_fill_an_empty_field_that_accepts_estimates(self):
        """The one cell that flips on a field-level declaration."""
        self.assertEqual(decide("empty", "medium", accepts_estimates=True)[0], WRITE)
        self.assertEqual(decide("empty", "medium", accepts_estimates=False)[0], PROPOSE)

    def test_accepting_estimates_never_unlocks_an_overwrite(self):
        """The flag fills a blank. It does not license replacing an existing value."""
        for state in ("stale", "human"):
            with self.subTest(state=state):
                self.assertEqual(decide(state, "medium", accepts_estimates=True)[0], PROPOSE)


class AHumanValueIsNeverOverwritten(unittest.TestCase):
    """The first load-bearing rule."""

    def test_no_confidence_level_can_write_over_a_person(self):
        for confidence in CONFIDENCES:
            with self.subTest(confidence=confidence):
                led = ledger_for(field(provenance="human", confidence=confidence))
                self.assertEqual(actions(led)["Tech Stack Details"], PROPOSE)

    def test_a_human_value_that_is_old_is_still_a_human_value(self):
        """Age must not demote a person's decision to a machine value."""
        self.assertEqual(classify(field(provenance="human", updated_at=OLD), AS_OF), "human")

    def test_an_empty_human_field_is_treated_as_empty_not_as_a_decision(self):
        """A blank a person never filled is a gap, not a choice to leave it blank."""
        self.assertEqual(classify(field(provenance="human", value=""), AS_OF), "empty")


class UnknownProvenanceIsNotMachineProvenance(unittest.TestCase):
    """A missing field must not defeat the never-overwrite-a-human rule.

    Found by review, 2026-09-08: `unknown` provenance fell through to the machine path, so a
    hand-typed value whose author was never recorded could be silently overwritten on age.
    The rule was defeated by an ABSENT attribution rather than by a wrong one.
    """

    def test_an_unattributed_stale_value_is_protected(self):
        led = ledger_for(field(provenance="unknown", updated_at=OLD))
        self.assertEqual(actions(led)["Tech Stack Details"], PROPOSE)

    def test_only_an_explicit_machine_value_may_be_overwritten_on_age(self):
        self.assertEqual(classify(field(provenance="machine", updated_at=OLD), AS_OF), "stale")
        self.assertEqual(classify(field(provenance="unknown", updated_at=OLD), AS_OF),
                         "unattributed")

    def test_an_undated_unattributed_value_is_protected(self):
        """The riskiest combination: no author, no date, existing content."""
        self.assertEqual(classify(field(provenance="unknown", updated_at=None), AS_OF),
                         "unattributed")

    def test_an_empty_unattributed_field_is_still_fillable(self):
        """Protection is for CONTENT. A blank has nothing to protect."""
        led = ledger_for(field(provenance="unknown", value=None))
        self.assertEqual(actions(led)["Tech Stack Details"], WRITE)

    def test_a_fresh_unattributed_value_is_simply_skipped(self):
        self.assertEqual(classify(field(provenance="unknown", updated_at=FRESH), AS_OF), "fresh")


class AnInferredFactIsNeverWritten(unittest.TestCase):
    """The second load-bearing rule. This is the organization_revenue 0.0 defect."""

    def test_inferred_never_reaches_the_write_queue(self):
        led = ledger_for(
            field(name="empty-inferred", value=None, confidence="inferred"),
            field(name="stale-inferred", updated_at=OLD, confidence="inferred"),
            field(name="human-inferred", provenance="human", confidence="inferred"),
        )
        self.assertEqual(led["write"], [])
        self.assertEqual(len(led["propose"]), 3)


class EmptinessIsNotZero(unittest.TestCase):
    """Conflating absence with a real value is the defect the whole module exists to stop."""

    def test_absent_values_are_empty(self):
        for value in (None, "", "   ", [], {}):
            with self.subTest(value=value):
                self.assertTrue(is_empty(value))

    def test_zero_and_false_are_values_not_absence(self):
        for value in (0, 0.0, False):
            with self.subTest(value=value):
                self.assertFalse(is_empty(value),
                                 "a real zero must never be read as a missing value")


class StalenessBehaves(unittest.TestCase):
    def test_a_recent_machine_value_is_fresh(self):
        self.assertEqual(classify(field(), AS_OF), "fresh")

    def test_a_value_past_its_window_is_stale(self):
        self.assertEqual(classify(field(updated_at=OLD), AS_OF), "stale")

    def test_the_window_is_configurable_per_field(self):
        self.assertEqual(classify(field(stale_after_days=3650, updated_at=OLD), AS_OF), "fresh")

    def test_an_undated_machine_value_is_stale_not_fresh(self):
        """Trusting an undated value costs correctness; refreshing it costs one call."""
        self.assertEqual(classify(field(updated_at=None), AS_OF), "stale")

    def test_an_unparseable_date_is_stale_not_fresh(self):
        self.assertEqual(classify(field(updated_at="last Tuesday"), AS_OF), "stale")


class TheLedgerSortsAndReports(unittest.TestCase):
    def test_fields_land_in_the_right_queues(self):
        led = ledger_for(
            field(name="fill-me", value=None),
            field(name="ask-me", provenance="human"),
            field(name="leave-me"),
        )
        self.assertEqual([e["name"] for e in led["write"]], ["fill-me"])
        self.assertEqual([e["name"] for e in led["propose"]], ["ask-me"])
        self.assertEqual([e["name"] for e in led["skip"]], ["leave-me"])

    def test_a_propose_queue_means_needs_human(self):
        self.assertEqual(ledger_for(field(provenance="human"))["verdict"], "NEEDS_HUMAN")

    def test_no_propose_queue_means_clear(self):
        self.assertEqual(ledger_for(field(value=None))["verdict"], "CLEAR")

    def test_writes_alone_do_not_require_a_human(self):
        """The point of the gate: a verified fact into a blank field needs no approval."""
        led = ledger_for(field(name="a", value=None), field(name="b", value=None))
        self.assertEqual(led["verdict"], "CLEAR")
        self.assertEqual(len(led["write"]), 2)


class ItRejectsMalformedInput(unittest.TestCase):
    def test_a_non_object_record_is_rejected(self):
        problems, _ = build([], AS_OF)
        self.assertTrue(problems)

    def test_an_empty_field_list_is_rejected(self):
        problems, _ = build({"fields": []}, AS_OF)
        self.assertTrue(problems)

    def test_an_unknown_confidence_is_rejected_not_defaulted(self):
        """Defaulting an unknown level would silently pick a cell of the table."""
        problems, _ = build({"fields": [field(confidence="pretty sure")]}, AS_OF)
        self.assertTrue(problems)

    def test_an_unknown_provenance_is_rejected(self):
        problems, _ = build({"fields": [field(provenance="the vendor")]}, AS_OF)
        self.assertTrue(problems)

    def test_a_nameless_field_is_rejected(self):
        problems, _ = build({"fields": [field(name="  ")]}, AS_OF)
        self.assertTrue(problems)

    def test_the_provenance_vocabulary_is_pinned(self):
        self.assertEqual(set(PROVENANCES), {"machine", "human", "unknown"})


class MutationCoverage(unittest.TestCase):
    """Reintroduce each defect the gate exists to prevent, in memory, and prove it is caught.

    A green suite is not evidence that a check works; this is. Every mutation below rewrites
    the module source, reloads it in isolation, and asserts the guarantee breaks. Nothing on
    disk is touched.
    """

    MUTATIONS = {
        "overwrite a human": (
            'return PROPOSE, "a person entered this value; the engine may propose, never overwrite"',
            'return WRITE, "MUTANT"'),
        "overwrite an unattributed value": (
            'return PROPOSE, "nobody recorded who wrote this value, so it may be a person\'s"',
            'return WRITE, "MUTANT"'),
        "write an inferred fact": (
            'return PROPOSE, "inferred facts are never written, only proposed"',
            'return WRITE, "MUTANT"'),
        "read zero as absent": (
            "    if isinstance(value, (list, dict)):\n        return len(value) == 0\n    return False",
            "    if isinstance(value, (list, dict)):\n        return len(value) == 0\n    return not value"),
    }

    def load_mutant(self, old, new):
        """Compile a mutated copy of the module without touching the file on disk."""
        source = (REPO_ROOT / "scripts" / "gap_ledger.py").read_text(encoding="utf-8")
        self.assertIn(old, source, "mutation target no longer present; update the mutation")
        namespace = {"__name__": "gap_ledger_mutant"}
        exec(compile(source.replace(old, new), "gap_ledger_mutant", "exec"), namespace)
        return namespace

    def test_every_mutation_breaks_a_guarantee(self):
        checks = {
            "overwrite a human": lambda m: m["decide"]("human", "verified", False)[0] == WRITE,
            "overwrite an unattributed value":
                lambda m: m["decide"]("unattributed", "verified", False)[0] == WRITE,
            "write an inferred fact": lambda m: m["decide"]("empty", "inferred", False)[0] == WRITE,
            "read zero as absent": lambda m: m["is_empty"](0) is True,
        }
        for name, (old, new) in self.MUTATIONS.items():
            with self.subTest(mutation=name):
                mutant = self.load_mutant(old, new)
                self.assertTrue(checks[name](mutant),
                                f"mutation {name!r} did not change behavior; it is not a real mutation")

    def test_the_real_module_holds_every_guarantee(self):
        """The other half: unmutated, none of those breaches exist."""
        self.assertEqual(decide("human", "verified", False)[0], PROPOSE)
        self.assertEqual(decide("unattributed", "verified", False)[0], PROPOSE)
        self.assertEqual(decide("empty", "inferred", False)[0], PROPOSE)
        self.assertFalse(is_empty(0))

    def test_the_mutation_set_covers_every_stated_guarantee(self):
        """A guard on the guard: the docs claim four protections, so four are mutated."""
        self.assertEqual(len(self.MUTATIONS), 4)


class TheCliBehaves(unittest.TestCase):
    def run_cli(self, record, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(record, f)
            path = f.name
        return subprocess.run([sys.executable, str(SCRIPT), "--record", path,
                               "--as-of", AS_OF.isoformat(), *args],
                              capture_output=True, text=True)

    def test_a_clear_ledger_exits_zero(self):
        proc = self.run_cli({"record": "t", "fields": [field(value=None)]})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("CLEAR", proc.stdout)

    def test_a_ledger_needing_a_human_exits_one(self):
        proc = self.run_cli({"record": "t", "fields": [field(provenance="human")]})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("NEEDS_HUMAN", proc.stdout)

    def test_malformed_input_exits_two(self):
        proc = self.run_cli({"record": "t", "fields": []})
        self.assertEqual(proc.returncode, 2)

    def test_a_missing_record_argument_exits_two(self):
        proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_json_mode_emits_the_queues(self):
        proc = self.run_cli({"record": "t", "fields": [field(value=None)]}, "--json")
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["verdict"], "CLEAR")
        self.assertEqual(len(payload["write"]), 1)

    def test_a_bad_as_of_exits_two(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"record": "t", "fields": [field()]}, f)
            path = f.name
        proc = subprocess.run([sys.executable, str(SCRIPT), "--record", path,
                               "--as-of", "yesterday"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
