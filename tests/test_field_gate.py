"""Tests for skills/gtm-blueprint/scripts/field_gate.py.

The gate decides whether a blueprint may be composed at all, so its failure mode
matters: a false PASS lets a fabricated or generic blueprint reach a prospect. These
tests pin the two rules that produce that outcome — required fields and one_of
groups — plus the emptiness semantics they rest on.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REPO_ROOT / "skills" / "gtm-blueprint" / "scripts" / "field_gate.py"

_spec = importlib.util.spec_from_file_location("field_gate", GATE_PATH)
field_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(field_gate)

LINKEDIN_SUMMARY = "FIELD_ID_LINKEDIN_PROFILE_SUMMARY"  # required
RESEARCH_PROFILE = "FIELD_ID_RESEARCH_COMPANY_PROFILE"  # one_of:company_context
POSTS_FIELD = "FIELD_ID_LINKEDIN_POSTS"     # one_of:company_context
PERSONA_INTEL = "FIELD_ID_PERSONA_INTELLIGENCE"     # optional


def record(**custom_fields):
    """Build a minimal CRM record carrying the given custom fields."""
    return {
        "name": "Test Contact",
        "organization_name": "Testco",
        "typed_custom_fields": dict(custom_fields),
    }


class IsPopulated(unittest.TestCase):
    """What counts as a filled-in field value."""

    def test_absent_and_empty_values_are_not_populated(self):
        """None, empty, and whitespace-only are all "nobody filled this in"."""
        for value in (None, "", "   ", "\n\t ", [], {}):
            with self.subTest(value=repr(value)):
                self.assertFalse(field_gate.is_populated(value))

    def test_meaningful_values_are_populated(self):
        """Real content passes, including short values that are nonetheless real."""
        for value in ("summary text", "  padded  ", ["a"], {"k": "v"}):
            with self.subTest(value=repr(value)):
                self.assertTrue(field_gate.is_populated(value))


class RequiredFields(unittest.TestCase):
    """Required fields block the gate when absent or empty."""

    def test_missing_required_field_fails(self):
        """The core gate: composing without a required input is the defect this prevents."""
        verdict = field_gate.run_gate(
            record(**{RESEARCH_PROFILE: "profile"}),
            field_gate.EXAMPLE_CONFIG,
            "funding",
        )
        self.assertEqual(verdict["gate"], "FAIL")
        self.assertIn("LinkedIn Profile Summary", verdict["missing_required"])

    def test_whitespace_only_required_field_fails(self):
        """A field of spaces looks populated in a CRM grid and is not."""
        verdict = field_gate.run_gate(
            record(**{LINKEDIN_SUMMARY: "   ", RESEARCH_PROFILE: "profile"}),
            field_gate.EXAMPLE_CONFIG,
            "funding",
        )
        self.assertEqual(verdict["gate"], "FAIL")
        self.assertIn("LinkedIn Profile Summary", verdict["missing_required"])

    def test_optional_field_absent_does_not_fail(self):
        """Optional inputs must not block an otherwise complete record."""
        verdict = field_gate.run_gate(
            record(**{LINKEDIN_SUMMARY: "summary", POSTS_FIELD: "digest"}),
            field_gate.EXAMPLE_CONFIG,
            "funding",
        )
        self.assertEqual(verdict["gate"], "PASS")
        optional = next(
            f for f in verdict["fields"] if f["field_id"] == PERSONA_INTEL
        )
        self.assertFalse(optional["populated"])


class OneOfGroups(unittest.TestCase):
    """one_of groups are satisfied by any single member."""

    def test_empty_group_fails_even_when_required_field_present(self):
        """A one_of group with no member satisfied is its own failure, independently."""
        verdict = field_gate.run_gate(
            record(**{LINKEDIN_SUMMARY: "summary"}),
            field_gate.EXAMPLE_CONFIG,
            "funding",
        )
        self.assertEqual(verdict["gate"], "FAIL")
        self.assertTrue(
            any("company_context" in m for m in verdict["missing_required"]),
            verdict["missing_required"],
        )

    def test_either_group_member_satisfies_it(self):
        """one_of means any member, not a specific preferred one."""
        for satisfying in (RESEARCH_PROFILE, POSTS_FIELD):
            with self.subTest(field=satisfying):
                verdict = field_gate.run_gate(
                    record(**{LINKEDIN_SUMMARY: "summary", satisfying: "value"}),
                    field_gate.EXAMPLE_CONFIG,
                    "funding",
                )
                self.assertEqual(verdict["gate"], "PASS")
                self.assertEqual(verdict["missing_required"], [])


class Verdict(unittest.TestCase):
    """The verdict carries what the audit log needs."""

    def test_failing_fields_carry_remediation_and_passing_ones_do_not(self):
        """A failure without a fix path makes the operator go read the config themselves."""
        verdict = field_gate.run_gate(
            record(**{LINKEDIN_SUMMARY: "summary"}),
            field_gate.EXAMPLE_CONFIG,
            "hiring",
        )
        by_id = {f["field_id"]: f for f in verdict["fields"]}
        self.assertIsNone(by_id[LINKEDIN_SUMMARY]["remediation"])
        self.assertTrue(by_id[RESEARCH_PROFILE]["remediation"])

    def test_verdict_carries_run_context_for_the_audit_log(self):
        """The verdict is logged verbatim, so it must be self-describing later."""
        verdict = field_gate.run_gate(
            record(**{LINKEDIN_SUMMARY: "s", POSTS_FIELD: "d"}),
            field_gate.EXAMPLE_CONFIG,
            "hiring",
        )
        self.assertEqual(verdict["contact"], "Test Contact")
        self.assertEqual(verdict["company"], "Testco")
        self.assertEqual(verdict["motion"], "hiring")

    def test_record_without_custom_fields_fails_closed(self):
        """No evidence must fail, never pass: absence of data is not proof of completeness."""
        verdict = field_gate.run_gate({}, field_gate.EXAMPLE_CONFIG, "funding")
        self.assertEqual(verdict["gate"], "FAIL")
        self.assertEqual(verdict["contact"], "unknown")


if __name__ == "__main__":
    unittest.main()
