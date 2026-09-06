"""Pin what the feedback reporter refuses to publish.

This script exists to send a stranger's setup run to a PUBLIC issue tracker, so the only
interesting question about it is what it will not send. Every test here reintroduces a
thing that must never reach an issue and asserts the report is rejected.

Fixtures containing credential-shaped strings are DERIVED at run time rather than written
as literals, for the same reason as tests/test_scan_secrets.py: GitHub push protection
blocked a realistic literal in this repo once already, and a test fixture is not worth a
rotation drill.

Run: python3 -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "setup_feedback.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from setup_feedback import (  # noqa: E402
    CONNECTORS, MAX_NOTE_CHARS, MAX_NOTES, STATES, check_note, render, validate,
)


def synthetic(seed, length, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"):
    """Build a deterministic high-entropy string without writing one down.

    Multiplying by a prime that is coprime with the alphabet size walks the whole
    alphabet, so the result clears the entropy floor in scan_secrets.
    """
    return "".join(alphabet[(seed + i * 7) % len(alphabet)] for i in range(length))


def good_report(**overrides):
    """A report that must pass, so a test that fails proves the rejection, not the shape."""
    report = {
        "checkpoint": "diagnosis",
        "plugin_version": "1.7.0",
        "connectors": [{"name": "apollo", "state": "S3"}],
        "outcome": "continued",
        "misdiagnosed_a_state": False,
        "notes": ["The probe order was clear and nothing asked me to buy anything."],
    }
    report.update(overrides)
    return report


class TheHappyPathWorks(unittest.TestCase):
    """If this fails, every rejection test below proves nothing."""

    def test_a_clean_report_is_accepted(self):
        problems, cleaned = validate(good_report())
        self.assertEqual(problems, [])
        self.assertEqual(cleaned["connectors"], [{"name": "apollo", "state": "S3"}])

    def test_the_rendered_body_carries_the_ladder_and_the_marker(self):
        _, cleaned = validate(good_report())
        title, body = render(cleaned)
        self.assertIn("1.7.0", title)
        self.assertIn("gtm-os:setup-feedback:v1", body)
        self.assertIn("| apollo | S3 |", body)

    def test_the_body_never_contains_the_word_credential_as_a_value(self):
        """The disclosure line must be present, so a reader knows the scope."""
        _, cleaned = validate(good_report())
        _, body = render(cleaned)
        self.assertIn("No IDs, credentials, prospect data", body)


class ItRefusesToPublishIdentifiers(unittest.TestCase):
    """Each of these is a thing that must never leave a tester's machine."""

    def assert_note_rejected(self, note, because):
        reasons = check_note(note)
        self.assertTrue(reasons, f"note was allowed but should have been rejected: {because}")

    def test_an_airtable_base_id_is_rejected(self):
        base = "app" + synthetic(3, 14, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
        self.assert_note_rejected(f"the base is {base}", "Airtable base ID")

    def test_a_table_and_field_id_are_rejected(self):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        for prefix in ("tbl", "fld", "rec", "viw"):
            with self.subTest(prefix=prefix):
                self.assert_note_rejected(f"stalled on {prefix}{synthetic(5, 14, alphabet)}",
                                          f"{prefix} object ID")

    def test_a_crm_field_id_is_rejected(self):
        self.assert_note_rejected(f"field {synthetic(1, 24, '0123456789abcdef')} was empty",
                                  "24-char hex CRM field ID")

    def test_an_email_address_is_rejected(self):
        self.assert_note_rejected("ping someone@somewhere.example about it", "email address")

    def test_a_credential_is_rejected(self):
        token = "apify_api_" + synthetic(9, 34)
        self.assert_note_rejected(f"my token {token} did not work", "Apify token")

    def test_a_non_vendor_url_is_rejected(self):
        self.assert_note_rejected("see https://wiki.internal.example/setup for context",
                                  "link into a private workspace")

    def test_vendor_documentation_links_are_allowed(self):
        """Rejecting these would strip the most useful kind of note."""
        self.assertEqual(check_note("https://docs.apify.com/actors says otherwise"), [])

    def test_ordinary_prose_is_not_rejected(self):
        """The ID rule must not fire on English. It once matched 'recommendations'."""
        for note in ("recommendations for the next run were clear",
                     "the application never asked me to pay",
                     "record the ID somewhere, it said, without saying where"):
            with self.subTest(note=note):
                self.assertEqual(check_note(note), [], f"false positive on: {note}")


class ItRejectsRatherThanStrips(unittest.TestCase):
    """A stripped note is a note the approving human never actually read."""

    def test_a_bad_note_blocks_the_whole_report(self):
        report = good_report(notes=["fine note", "the base is appQ7x2LmNp4KdVcZ"])
        problems, _ = validate(report)
        self.assertTrue(problems)

    def test_the_good_notes_are_not_quietly_kept_alongside_a_rejection(self):
        report = good_report(notes=["fine note", "the base is appQ7x2LmNp4KdVcZ"])
        problems, cleaned = validate(report)
        self.assertTrue(problems, "the report must be rejected outright")
        # cleaned is only ever used when problems is empty; assert the caller contract.
        self.assertNotIn("appQ7x2LmNp4KdVcZ", json.dumps(cleaned))

    def test_the_reason_does_not_leak_the_value_it_caught(self):
        reasons = check_note("the base is appQ7x2LmNp4KdVcZ")
        self.assertTrue(reasons)
        self.assertNotIn("appQ7x2LmNp4KdVcZ", " ".join(reasons))


class ItConstrainsTheStructuredFields(unittest.TestCase):
    """The structured fields are an allowlist so free text cannot hide in them."""

    def test_an_unknown_connector_name_is_rejected(self):
        problems, _ = validate(good_report(
            connectors=[{"name": "acme-corp-internal-crm", "state": "S2"}]))
        self.assertTrue(problems)

    def test_an_invalid_ladder_state_is_rejected(self):
        problems, _ = validate(good_report(connectors=[{"name": "apollo", "state": "S9"}]))
        self.assertTrue(problems)

    def test_an_unknown_checkpoint_is_rejected(self):
        problems, _ = validate(good_report(checkpoint="halfway"))
        self.assertTrue(problems)

    def test_a_non_semver_version_is_rejected(self):
        problems, _ = validate(good_report(plugin_version="latest"))
        self.assertTrue(problems)

    def test_an_empty_connector_list_is_rejected(self):
        """A report with no ladder says nothing about the module under test."""
        problems, _ = validate(good_report(connectors=[]))
        self.assertTrue(problems)

    def test_an_over_long_note_is_rejected(self):
        problems, _ = validate(good_report(notes=["x" * (MAX_NOTE_CHARS + 1)]))
        self.assertTrue(problems)

    def test_too_many_notes_are_rejected(self):
        problems, _ = validate(good_report(notes=["ok"] * (MAX_NOTES + 1)))
        self.assertTrue(problems)

    def test_every_connector_in_the_allowlist_has_a_purpose(self):
        """A guard on the allowlist itself: it must stay small and named."""
        self.assertLessEqual(len(CONNECTORS), 25)
        self.assertIn("apollo", CONNECTORS)
        self.assertEqual(set(STATES), {"S0", "S1", "S2", "S3", "S4"})


class TheCliBehaves(unittest.TestCase):
    """Exit codes are the contract the skill depends on."""

    def run_cli(self, report, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(report, f)
            path = f.name
        return subprocess.run([sys.executable, str(SCRIPT), "--report", path, *args],
                              capture_output=True, text=True)

    def test_a_clean_report_renders_and_exits_zero(self):
        proc = self.run_cli(good_report())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing has been sent", proc.stdout)

    def test_rendering_never_submits(self):
        """The default must be inert. Submitting is what needs the flag."""
        proc = self.run_cli(good_report())
        self.assertNotIn("github.com/NicT89/gtm-os/issues/", proc.stdout.split("---")[0])

    def test_a_rejected_report_exits_one(self):
        proc = self.run_cli(good_report(notes=["base appQ7x2LmNp4KdVcZ"]))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("REJECTED", proc.stdout)

    def test_a_missing_report_argument_exits_two(self):
        proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
