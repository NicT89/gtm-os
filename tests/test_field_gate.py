"""Tests for skills/gtm-blueprint/scripts/field_gate.py.

The gate decides whether a blueprint may be composed at all, so its failure mode
matters: a false PASS lets a fabricated or generic blueprint reach a prospect. These
tests pin the four rules that produce that outcome — required fields, one_of groups, the
account fields a signal type cannot compose without, and the fact floor — plus the
emptiness semantics they all rest on.

The last two did not exist before 1.9.4, and their absence was invisible for the same
reason in both cases: the gate ACCEPTED the input for a check it never ran. `--motion` was
a required argument that was echoed into the verdict and never read, so a hiring record
with no req, no JD and no archetype exited 0 = PASS; `min_hard_facts` sat in the config
with no reader. A mandatory argument reads as a mandatory check.

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


GTM_JOBS = "FIELD_ID_GTM_JOBS_WITH_URL"     # account, hiring only
JD_SUMMARY = "FIELD_ID_JD_SUMMARY"          # account, hiring only
ARCHETYPES = "FIELD_ID_ROLE_ARCHETYPES"     # account, hiring only

# Enough populated system-enrichment keys to clear the fact floor on their own, so a test
# about required fields is not also silently a test about the floor.
ENRICHED_ORG = {
    "latest_funding_stage": "Series A",
    "estimated_num_employees": 40,
    "technology_names": ["Apollo", "dbt"],
}


def record(account=None, organization_extra=None, **custom_fields):
    """Build a minimal CRM record carrying the given contact and account fields.

    The organization payload is enriched by default: without it every test would also be
    testing the fact floor, and a fixture that fails two checks at once cannot tell you
    which one you broke.
    """
    organization = dict(ENRICHED_ORG)
    organization.update(organization_extra or {})
    organization["typed_custom_fields"] = dict(account or {})
    return {
        "name": "Test Contact",
        "organization_name": "Testco",
        "typed_custom_fields": dict(custom_fields),
        "organization": organization,
    }


def hiring_account():
    """The three account fields the hiring signal type requires."""
    return {GTM_JOBS: "RevOps Lead | https://x.example/jobs/1 | 2026-08-20",
            JD_SUMMARY: "Owns routing and reporting in the first 90 days.",
            ARCHETYPES: "RevOps Builder"}


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
            record(account=hiring_account(), **{LINKEDIN_SUMMARY: "summary"}),
            field_gate.EXAMPLE_CONFIG,
            "hiring",
        )
        by_id = {f["field_id"]: f for f in verdict["fields"]}
        self.assertIsNone(by_id[LINKEDIN_SUMMARY]["remediation"])
        self.assertTrue(by_id[RESEARCH_PROFILE]["remediation"])

    def test_verdict_carries_run_context_for_the_audit_log(self):
        """The verdict is logged verbatim, so it must be self-describing later."""
        verdict = field_gate.run_gate(
            record(account=hiring_account(), **{LINKEDIN_SUMMARY: "s", POSTS_FIELD: "d"}),
            field_gate.EXAMPLE_CONFIG,
            "hiring",
        )
        self.assertEqual(verdict["contact"], "Test Contact")
        self.assertEqual(verdict["company"], "Testco")
        self.assertEqual(verdict["signal_type"], "hiring")

    def test_record_without_custom_fields_fails_closed(self):
        """No evidence must fail, never pass: absence of data is not proof of completeness."""
        verdict = field_gate.run_gate({}, field_gate.EXAMPLE_CONFIG, "funding")
        self.assertEqual(verdict["gate"], "FAIL")
        self.assertEqual(verdict["contact"], "unknown")


class AccountFieldsBySignalType(unittest.TestCase):
    """The signal type selects extra REQUIRED account fields. It used to select nothing.

    This is the regression that mattered: before 1.9.4 every assertion in this class
    passed with the account payload empty, because `--motion` was accepted and discarded.
    """

    def contact_side_complete(self, account=None):
        return record(account=account, **{LINKEDIN_SUMMARY: "summary", POSTS_FIELD: "digest"})

    def test_hiring_fails_without_the_req_the_jd_and_the_archetype(self):
        """All three are required by SKILL.md Step 2 and none was checked."""
        verdict = field_gate.run_gate(
            self.contact_side_complete(), field_gate.EXAMPLE_CONFIG, "hiring")
        self.assertEqual(verdict["gate"], "FAIL")
        for label in ("GTM Jobs w/ URL", "JD Summary", "Role Archetypes"):
            self.assertTrue(any(label in m for m in verdict["missing_required"]),
                            f"{label} missing from {verdict['missing_required']}")

    def test_hiring_fails_when_only_some_of_the_three_are_present(self):
        """Two of three is not the requirement; the opener needs the date AND the scope."""
        partial = {GTM_JOBS: "RevOps Lead | https://x.example/jobs/1 | 2026-08-20",
                   JD_SUMMARY: "scope"}
        verdict = field_gate.run_gate(
            self.contact_side_complete(partial), field_gate.EXAMPLE_CONFIG, "hiring")
        self.assertEqual(verdict["gate"], "FAIL")
        self.assertTrue(any("Role Archetypes" in m for m in verdict["missing_required"]))

    def test_hiring_passes_with_all_three(self):
        verdict = field_gate.run_gate(
            self.contact_side_complete(hiring_account()), field_gate.EXAMPLE_CONFIG, "hiring")
        self.assertEqual(verdict["gate"], "PASS", verdict["missing_required"])

    def test_funding_does_not_require_the_hiring_account_fields(self):
        """The signal type has to select, not just add: funding composes without a req."""
        verdict = field_gate.run_gate(
            self.contact_side_complete(), field_gate.EXAMPLE_CONFIG, "funding")
        self.assertEqual(verdict["gate"], "PASS", verdict["missing_required"])

    def test_missing_account_payload_fails_hiring_closed(self):
        """A record with no organization at all must not pass on absence of evidence."""
        bare = {"typed_custom_fields": {LINKEDIN_SUMMARY: "s", POSTS_FIELD: "d"}}
        verdict = field_gate.run_gate(bare, field_gate.EXAMPLE_CONFIG, "hiring")
        self.assertEqual(verdict["gate"], "FAIL")

    def test_account_fields_are_labeled_account_scope_in_the_verdict(self):
        """The audit log has to say which record a missing field lives on."""
        verdict = field_gate.run_gate(
            self.contact_side_complete(hiring_account()), field_gate.EXAMPLE_CONFIG, "hiring")
        scopes = {f["field_id"]: f["scope"] for f in verdict["fields"]}
        self.assertEqual(scopes[GTM_JOBS], "account")
        self.assertEqual(scopes[LINKEDIN_SUMMARY], "contact")


class FactFloor(unittest.TestCase):
    """`min_hard_facts` had no reader. It does now, and it is honest about what it proves."""

    def test_thin_record_fails_the_floor(self):
        """One populated source cannot yield three hard facts, whatever the fields say."""
        thin = {"name": "T", "organization_name": "Testco",
                "typed_custom_fields": {LINKEDIN_SUMMARY: "summary", POSTS_FIELD: "digest"},
                "organization": {"typed_custom_fields": {}}}
        verdict = field_gate.run_gate(thin, field_gate.EXAMPLE_CONFIG, "funding")
        self.assertEqual(verdict["gate"], "FAIL")
        self.assertEqual(verdict["fact_floor"], {"count": 2, "minimum": 3})
        self.assertTrue(any("fact-bearing" in m for m in verdict["missing_required"]))

    def test_enrichment_keys_count_toward_the_floor(self):
        """Funding's hard numbers arrive through system enrichment, not custom fields."""
        verdict = field_gate.run_gate(
            record(**{LINKEDIN_SUMMARY: "summary", POSTS_FIELD: "digest"}),
            field_gate.EXAMPLE_CONFIG, "funding")
        self.assertEqual(verdict["gate"], "PASS", verdict["missing_required"])
        self.assertGreaterEqual(verdict["fact_floor"]["count"], 3)

    def test_optional_fields_do_not_count_toward_the_floor(self):
        """Otherwise the floor is cleared by fields nobody would cite."""
        verdict = field_gate.run_gate(
            record(organization_extra={"latest_funding_stage": None,
                                       "estimated_num_employees": None,
                                       "technology_names": []},
                   **{LINKEDIN_SUMMARY: "summary", POSTS_FIELD: "digest",
                      PERSONA_INTEL: "persona"}),
            field_gate.EXAMPLE_CONFIG, "funding")
        self.assertEqual(verdict["fact_floor"]["count"], 2)
        self.assertNotIn("Persona Intelligence", verdict["fact_bearing_sources"])

    def test_sources_are_named_so_the_count_is_auditable(self):
        """A bare number invites arguing with the gate instead of reading the record."""
        verdict = field_gate.run_gate(
            record(**{LINKEDIN_SUMMARY: "summary", POSTS_FIELD: "digest"}),
            field_gate.EXAMPLE_CONFIG, "funding")
        self.assertIn("LinkedIn Profile Summary", verdict["fact_bearing_sources"])
        self.assertIn("organization.latest_funding_stage", verdict["fact_bearing_sources"])
        self.assertEqual(verdict["fact_bearing_sources"],
                         sorted(verdict["fact_bearing_sources"]))


if __name__ == "__main__":
    unittest.main()
