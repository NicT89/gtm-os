"""Tests for skills/gtm-signal-scan/scripts/field_match.py.

Two providers describing the same seat rarely spell it the same way, and a
comparison that treats spelling as disagreement is worse than no comparison: it
sends someone to re-source a field that was already correct, or drops a real
match out of a qualification search.

The risk runs both ways, so these tests pin both. A normalizer that is too
timid reports false mismatches; one that is too eager folds "Head of Sales"
into "Head of Marketing" and qualifies a company on a seat nobody holds. The
must-differ cases below are the half that catches the second failure, and they
are why a normalizer returning a constant cannot pass this file.

One case here is load-bearing rather than illustrative. An explicit separator
character class was deleted from the normalizer during review after sabotage
testing showed all self-tests still passed without it -- the strip pass already
replaced every non-alphanumeric character. `test_hyphen_folding_is_really_tested`
pins the behaviour to the pass that actually performs it, so the same dead
reassurance cannot grow back.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MATCH_PATH = REPO_ROOT / "skills" / "gtm-signal-scan" / "scripts" / "field_match.py"

_spec = importlib.util.spec_from_file_location("field_match", MATCH_PATH)
field_match = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(field_match)


class TestCosmeticVariationAgrees(unittest.TestCase):
    """Differences of spelling, spacing and punctuation are not disagreements."""

    def test_hyphenation(self):
        # The case that prompted this: one provider's index against its own search.
        self.assertTrue(field_match.agree("VP, Go-to-Market", "VP, Go to Market"))

    def test_closed_compound(self):
        self.assertTrue(field_match.agree("Cofounder", "Co-Founder"))

    def test_parenthetical_suffix(self):
        self.assertTrue(field_match.agree("Chief Revenue Officer (CRO)",
                                          "Chief Revenue Officer"))

    def test_ampersand(self):
        self.assertTrue(field_match.agree("SVP Strategy & Commercial",
                                          "SVP Strategy and Commercial"))

    def test_seniority_abbreviation(self):
        self.assertTrue(field_match.agree("VP Sales", "Vice President Sales"))

    def test_whitespace_and_case(self):
        self.assertTrue(field_match.agree("  head   OF  sales ", "Head of Sales"))


class TestRealDifferenceStillDiffers(unittest.TestCase):
    """The half that a too-eager normalizer fails."""

    def test_different_function(self):
        self.assertFalse(field_match.agree("Head of Sales", "Head of Marketing"))

    def test_different_seniority(self):
        self.assertFalse(field_match.agree("VP Sales", "Director Sales"))

    def test_svp_is_not_vp(self):
        self.assertFalse(field_match.agree("SVP Sales", "VP Sales"))

    def test_founding_ic_is_not_a_founder(self):
        # Reading "Founding X" as founder-level is a documented provider defect;
        # the normalizer must not reproduce it.
        self.assertFalse(field_match.agree("Founding Account Executive", "Founder"))

    def test_substring_is_not_a_match(self):
        self.assertFalse(field_match.agree("Sales", "Head of Sales"))

    def test_a_constant_normalizer_would_fail_this_file(self):
        """Guard the guard: prove these cases discriminate at all."""
        collapsed = [("Head of Sales", "Head of Marketing"),
                     ("VP Sales", "Director Sales"),
                     ("SVP Sales", "VP Sales")]
        for a, b in collapsed:
            self.assertNotEqual(field_match.normalize(a), field_match.normalize(b),
                                msg=a + " and " + b + " normalized to the same value")


class TestAbsence(unittest.TestCase):
    """An absent value is an absence, not a disagreement."""

    def test_both_absent_agree(self):
        self.assertTrue(field_match.agree(None, ""))

    def test_one_absent_does_not_agree(self):
        self.assertFalse(field_match.agree("", "Head of Sales"))
        self.assertFalse(field_match.agree(None, "Head of Sales"))


class TestNormalizerInternals(unittest.TestCase):

    def test_hyphen_folding_is_really_tested(self):
        """Pin hyphen folding to the pass that performs it.

        Sabotage testing showed an explicit separator class could be deleted
        with every test still green, because the strip pass already handled
        hyphens. This asserts the observable behaviour directly so the check
        cannot become decoration again.
        """
        self.assertEqual(field_match.normalize("go-to-market"), "go to market")
        self.assertEqual(field_match.normalize("VP—Sales"), "vice president sales")

    def test_self_test_suite_is_green(self):
        self.assertEqual(field_match.self_test(), 0)


if __name__ == "__main__":
    unittest.main()
