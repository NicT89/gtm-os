"""Pin what the feedback reporter strips, and what it refuses to send unapproved.

This script sends a stranger's setup run to a PUBLIC issue tracker, so the only interesting
questions about it are what it removes and what it will not do without approval. Each test
below reintroduces a value that must never reach an issue and asserts it is gone from the
rendered body, or removes an approval and asserts nothing is sent.

Stripping replaced an earlier reject-the-whole-note design. That is only safe because the
body a human approves is the body after redaction, and the confirm token binds the two
together — so the approval tests here are not a separate feature from the redaction tests,
they are what makes redaction acceptable. If TheApprovalIsBound fails, the redaction
guarantee is gone with it.

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
    CONNECTORS, MAX_NOTE_CHARS, MAX_NOTES, STATES, redact_note, render, token_for, validate,
)

MIXED = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def synthetic(seed, length, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"):
    """Build a deterministic high-entropy string without writing one down.

    Stepping by a prime coprime with the alphabet size walks the whole alphabet, so the
    result clears the entropy floor in scan_secrets.
    """
    return "".join(alphabet[(seed + i * 7) % len(alphabet)] for i in range(length))


def good_report(**overrides):
    """A report that must pass, so a failing test proves the behavior, not the fixture."""
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


def body_for(report):
    """Render a report the way the CLI does, and fail loudly if it did not validate."""
    problems, cleaned = validate(report)
    assert not problems, problems
    return render(cleaned)[1]


class TheHappyPathWorks(unittest.TestCase):
    """If this fails, every assertion below proves nothing."""

    def test_a_clean_report_is_accepted(self):
        problems, cleaned = validate(good_report())
        self.assertEqual(problems, [])
        self.assertEqual(cleaned["connectors"], [{"name": "apollo", "state": "S3"}])

    def test_the_rendered_body_carries_the_ladder_and_the_marker(self):
        body = body_for(good_report())
        self.assertIn("gtm-os:setup-feedback:v1", body)
        self.assertIn("| apollo | S3 |", body)

    def test_a_clean_note_survives_untouched(self):
        """Redaction must not mangle ordinary prose, or nobody will trust the output."""
        note = "It stalled at the schema probe and never said which base it wanted."
        text, kinds = redact_note(note)
        self.assertEqual(text, note)
        self.assertEqual(kinds, [])


class SensitiveValuesAreStrippedFromTheBody(unittest.TestCase):
    """Each value must be absent from the rendered issue, not merely flagged."""

    def assert_stripped(self, secret, note, kind):
        body = body_for(good_report(notes=[note]))
        self.assertNotIn(secret, body, f"{kind} survived into the rendered body")
        self.assertIn(f"[redacted: {kind}]", body,
                      f"{kind} was removed without leaving a visible marker")

    def test_an_airtable_object_id_is_stripped(self):
        for prefix in ("app", "tbl", "fld", "rec", "viw"):
            with self.subTest(prefix=prefix):
                ident = prefix + synthetic(5, 14, MIXED)
                self.assert_stripped(ident, f"stalled on {ident}", "workspace-id")

    def test_a_crm_field_id_is_stripped(self):
        ident = synthetic(1, 24, "0123456789abcdef")
        self.assert_stripped(ident, f"field {ident} was empty", "crm-field-id")

    def test_an_email_address_is_stripped(self):
        self.assert_stripped("someone@somewhere.example",
                             "ping someone@somewhere.example about it", "email-address")

    def test_a_credential_is_stripped(self):
        token = "apify_api_" + synthetic(9, 34)
        self.assert_stripped(token, f"my token {token} did not work", "credential")

    def test_a_private_link_is_stripped(self):
        self.assert_stripped("wiki.internal.example",
                             "see https://wiki.internal.example/setup for context",
                             "private-link")

    def test_a_link_that_only_looks_allowlisted_is_stripped(self):
        """The allowlisted name can be userinfo, a prefix, or a different port.

        Each of these reads as vendor documentation and resolves somewhere else. A
        host-prefix regex accepted the first one and kept the rest of the URL intact.
        """
        for raw, leaked in (
            ("https://docs.apify.com@wiki.internal.example/setup", "wiki.internal.example"),
            ("https://user:pw@wiki.internal.example/x", "wiki.internal.example"),
            ("https://docs.apify.com.evil.example/x", "evil.example"),
            ("http://docs.apify.com/actors", "http://"),
            ("https://docs.apify.com:8443/x", "8443"),
        ):
            with self.subTest(url=raw):
                self.assert_stripped(leaked, f"see {raw}", "private-link")

    def test_vendor_documentation_links_survive(self):
        """Stripping these would remove the most useful kind of note."""
        body = body_for(good_report(notes=["https://docs.apify.com/actors says otherwise"]))
        self.assertIn("https://docs.apify.com/actors", body)

    def test_several_values_in_one_note_are_all_stripped(self):
        ident = "app" + synthetic(3, 14, MIXED)
        token = "apify_api_" + synthetic(2, 34)
        body = body_for(good_report(notes=[f"base {ident} and token {token} both failed"]))
        self.assertNotIn(ident, body)
        self.assertNotIn(token, body)

    def test_ordinary_prose_is_not_mangled(self):
        """The ID rule must not fire on English. It once matched 'recommendations'."""
        for note in ("recommendations for the next run were clear",
                     "the application never asked me to pay",
                     "record the ID somewhere, it said, without saying where"):
            with self.subTest(note=note):
                text, kinds = redact_note(note)
                self.assertEqual(kinds, [], f"false positive on: {note}")
                self.assertEqual(text, note)

    def test_an_over_long_note_is_truncated_not_dropped(self):
        text, kinds = redact_note("x" * (MAX_NOTE_CHARS + 200))
        self.assertLessEqual(len(text), MAX_NOTE_CHARS)
        self.assertIn("over-length", kinds)


class TheRedactionIsDisclosedInTheBody(unittest.TestCase):
    """The approving human has to be able to see that something was removed."""

    def test_the_body_counts_what_was_stripped(self):
        ident = "app" + synthetic(4, 14, MIXED)
        body = body_for(good_report(notes=[f"base is {ident}"]))
        self.assertIn("1 value(s) were stripped", body)
        self.assertIn("workspace-id", body)

    def test_a_clean_report_says_nothing_needed_stripping(self):
        self.assertIn("Nothing needed stripping", body_for(good_report()))


class TheApprovalIsBound(unittest.TestCase):
    """What makes stripping safe: the approved body is the body that gets filed."""

    def test_the_token_is_derived_from_the_body(self):
        self.assertEqual(token_for("abc"), token_for("abc"))
        self.assertNotEqual(token_for("abc"), token_for("abd"))

    def test_a_changed_body_changes_the_token(self):
        """An edited note after approval must invalidate the approval."""
        first = token_for(body_for(good_report(notes=["one thing happened"])))
        second = token_for(body_for(good_report(notes=["a different thing happened"])))
        self.assertNotEqual(first, second)


class ItConstrainsTheStructuredFields(unittest.TestCase):
    """The structured fields are allowlists so free text cannot hide in them."""

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

    def test_too_many_notes_are_rejected(self):
        problems, _ = validate(good_report(notes=["ok"] * (MAX_NOTES + 1)))
        self.assertTrue(problems)

    def test_sensitive_content_is_never_a_structural_problem(self):
        """Content is redacted, not refused. This is the contract change from v1.7.0."""
        ident = "app" + synthetic(7, 14, MIXED)
        problems, _ = validate(good_report(notes=[f"base {ident}"]))
        self.assertEqual(problems, [])

    def test_the_allowlist_is_exactly_this_set(self):
        """Connector names go into the body unscanned, so the set is pinned exactly.

        A size bound would let a connector named after a client slip in, which is the one
        way a free-typed identifier could still reach a public issue.
        """
        self.assertEqual(CONNECTORS, {
            "apollo", "airtable", "apify", "firecrawl", "cb-insights", "brand-kit-os",
            "google-drive", "box", "onedrive", "supabase", "bigquery", "hubspot", "clay",
            "salesforce", "workflow-tool", "python-report-env", "other",
        })
        self.assertEqual(set(STATES), {"S0", "S1", "S2", "S3", "S4"})


class TheCliBehaves(unittest.TestCase):
    """Exit codes and the two-step flow are the contract the skill depends on."""

    def run_cli(self, report, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(report, f)
            path = f.name
        return subprocess.run([sys.executable, str(SCRIPT), "--report", path, *args],
                              capture_output=True, text=True)

    def test_rendering_exits_zero_and_prints_the_next_command(self):
        proc = self.run_cli(good_report())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing has been sent", proc.stdout)
        self.assertIn("--submit --confirm", proc.stdout)

    def test_submitting_without_a_token_is_refused(self):
        """The load-bearing one: blanket permission to run this must not be enough."""
        proc = self.run_cli(good_report(), "--submit")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Refusing to submit", proc.stderr)

    def test_submitting_with_a_wrong_token_is_refused(self):
        """Assert the reason, not just the code: submit() also exits 1 when gh is absent."""
        proc = self.run_cli(good_report(), "--submit", "--confirm", "000000000000")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Refusing to submit", proc.stderr)

    def test_a_non_object_report_is_rejected_rather_than_crashing(self):
        """json.loads accepts a list; every field read would then raise, not report."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("[]")
            path = f.name
        proc = subprocess.run([sys.executable, str(SCRIPT), "--report", path],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("must be a JSON object", proc.stdout)

    def test_a_structurally_broken_report_exits_one(self):
        proc = self.run_cli(good_report(checkpoint="nope"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("REJECTED", proc.stdout)

    def test_a_missing_report_argument_exits_two(self):
        proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_the_json_mode_carries_the_token_and_the_redaction_list(self):
        ident = "app" + synthetic(6, 14, MIXED)
        proc = self.run_cli(good_report(notes=[f"base {ident}"]), "--json")
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["verdict"], "READY")
        self.assertIn("confirm_token", payload)
        self.assertIn("workspace-id", payload["redactions"])
        self.assertNotIn(ident, payload["body"])


if __name__ == "__main__":
    unittest.main()
