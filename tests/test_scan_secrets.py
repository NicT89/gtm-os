"""Tests for scripts/scan_secrets.py.

This replaced an audit that could not fail: `grep -iE 'APOLLO|APIFY|API_KEY'`
over the history matched 271 lines of ordinary documentation on this repo and
zero credentials. So the tests that matter here are the two halves of that
failure: it must catch real credential shapes, and it must stay silent on the
vendor names and placeholder IDs this repo is full of.

Run: python3 -m unittest discover -s tests -v
"""
import hashlib
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "scan_secrets", REPO_ROOT / "scripts" / "scan_secrets.py")
scanner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scanner)


def synthetic(seed, length, alphabet="0123456789abcdef"):
    """Build a deterministic high-entropy string of `length` from `seed`.

    Every credential fixture in this file is derived, never written down. A
    literal of the real shape and entropy is indistinguishable from a live
    credential: GitHub push protection blocked this file when one fixture was a
    literal, and scan_secrets.py itself flags the file it is testing. Both are
    those scanners working correctly, so the fixtures are generated instead.
    """
    out = []
    digest = hashlib.sha256(seed.encode()).digest()
    while len(out) < length:
        for byte in digest:
            out.append(alphabet[byte % len(alphabet)])
            if len(out) == length:
                break
        digest = hashlib.sha256(digest).digest()
    return "".join(out)


ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def kinds(text):
    """Return the set of finding kinds the scanner reports for `text`."""
    return {f["kind"] for f in scanner.scan_text("t", text)}


class DetectsRealCredentials(unittest.TestCase):
    """Each shape the repo's connectors actually issue."""

    def test_secret_assignment_is_caught(self):
        """A long opaque value assigned to a secret-ish name."""
        key = synthetic("apollo-key", 22, ALNUM)
        self.assertIn("assignment", kinds(f'APOLLO_API_KEY = "{key}"'))

    def test_airtable_pat_is_caught(self):
        """Airtable personal access tokens: pat<14>.<40+>."""
        # Derived at runtime, never written down. A literal token of the real
        # shape and entropy is indistinguishable from a live one: GitHub push
        # protection blocked this file when the fixture was a literal, which is
        # the scanner-of-scanners working correctly.
        tok = f'pat{synthetic("pat-body", 14, ALNUM)}.{synthetic("pat-suffix", 64)}'
        self.assertIn("airtable-pat", kinds(f"token: {tok}"))

    def test_apify_token_is_caught(self):
        """Apify API tokens carry a fixed prefix."""
        self.assertIn("apify-token",
                      kinds("apify_api_" + synthetic("apify", 36, ALNUM)))

    def test_private_key_block_is_caught(self):
        """A pasted key file is unambiguous."""
        # Assembled, not written: the literal marker is itself what the scanner
        # (and GitHub's) look for, so this file must not contain it verbatim.
        marker = "-" * 5 + "BEGIN RSA PRIVATE KEY" + "-" * 5
        self.assertIn("private-key-block", kinds(marker))

    def test_findings_redact_the_secret(self):
        """Output goes into PR comments and issues, so it must not carry the value."""
        secret = synthetic("redact-me", 22, ALNUM)
        found = list(scanner.scan_text("t", f'API_KEY = "{secret}"'))
        self.assertTrue(found)
        self.assertNotIn(secret, found[0]["match"])


class StaysQuietOnDocumentation(unittest.TestCase):
    """The failure mode of the command this replaced."""

    def test_vendor_names_in_prose_are_not_findings(self):
        """271 matches on this repo's own docs is what made the old audit useless."""
        prose = ("Apollo is required for enrichment. Apify runs the posts actor. "
                 "See references/apollo-credit-costs.md for the API_KEY discussion.")
        self.assertEqual(kinds(prose), set())

    def test_config_key_names_are_not_findings(self):
        """The schema is full of KEY-suffixed names with no values attached."""
        self.assertEqual(kinds("APOLLO_CF_CONTACT_OPENER and AIRTABLE_POSTS_BASE_ID"), set())

    def test_documented_placeholders_are_not_findings(self):
        """appXXXXXXXXXXXXXX and <your-token> are instructions, not leaks."""
        text = ("Base airtable.com/appXXXXXXXXXXXXXX/api/docs, "
                "api_key: <your-api-key>, token = your_api_key_here")
        self.assertEqual(kinds(text), set())

    def test_test_fixtures_are_not_findings(self):
        """The suite builds IDs as 'a'*14 and '0'*24; those must not trip it."""
        self.assertEqual(kinds('config[key] = "0" * 24; base = "app" + "a" * 14'), set())

    def test_low_entropy_suppression_does_not_hide_real_tokens(self):
        """A real token containing a repeated run must still be caught.

        The first version of this filter suppressed any hit containing sixteen
        repeated characters anywhere inside it, which would silently drop a
        genuine credential. The rule is an entropy floor on the whole payload.
        """
        realistic = f'API_KEY = "{"a" * 16}{synthetic("tail", 22, ALNUM)}"'
        self.assertIn("assignment", kinds(realistic))


class RepoIsClean(unittest.TestCase):
    """The repo as shipped carries no credentials."""

    def test_working_tree_has_no_candidate_credentials(self):
        """Runs in CI, so a leak fails the build rather than waiting for review."""
        self.assertEqual(scanner.scan_working_tree(), [])


if __name__ == "__main__":
    unittest.main()
