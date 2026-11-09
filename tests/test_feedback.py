"""Pin what the general feedback reporter strips and what it refuses to send unapproved.

scripts/feedback.py sends a stranger's run to a PUBLIC issue tracker. The redaction
patterns are imported from setup_feedback.py and pinned there; the tests here prove the
import is actually applied to every free-text field of THIS reporter, that the structured
fields are allowlisted, and that nothing is sent without a token bound to the shown body.

Run: python3 -m unittest discover -s tests -v
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "feedback.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from feedback import (  # noqa: E402
    AREAS, FORMS, KINDS, MARKER, known_targets, paste_url, render, validate,
)
from setup_feedback import MAX_NOTE_CHARS, token_for  # noqa: E402

# A plausible Airtable table id, derived rather than written down: a literal that looks
# real invites a push-protection block and a pointless rotation drill.
TABLE_ID = "tbl" + "Qx7Lm2Np9Rk4Wz1"


def good_report(**overrides):
    report = {
        "kind": "bug",
        "target": "gtm-signal-scan",
        "plugin_version": "1.16.0",
        "surface": "claude-code",
        "connectors": [{"name": "apollo", "state": "S4"}],
        "title": "Step 5 adds contacts to the trigger list before posts are scraped",
        "sections": {
            "did": "Ran the weekly scan on a fresh list.",
            "happened": "The summary field was empty for every contact.",
            "expected": "A posts digest for each Excellent-tier contact.",
        },
    }
    report.update(overrides)
    return report


def body_for(report):
    problems, cleaned = validate(report)
    assert not problems, problems
    return render(cleaned)[1]


class TheHappyPathWorks(unittest.TestCase):
    def test_a_clean_report_is_accepted(self):
        problems, _ = validate(good_report())
        self.assertEqual(problems, [])

    def test_the_body_carries_the_marker_kind_target_and_every_section(self):
        body = body_for(good_report())
        self.assertIn(MARKER, body)
        self.assertIn("**Kind:** bug", body)
        self.assertIn("`gtm-signal-scan`", body)
        for _key, prompt in KINDS["bug"]:
            self.assertIn(f"### {prompt}", body)

    def test_the_version_check_outcome_reaches_the_body(self):
        """A reader must be able to tell whether the version was verified as current."""
        body = body_for(good_report(version_check="update-available"))
        self.assertIn("version check: update-available", body)
        body = body_for(good_report())
        self.assertIn("version check: not recorded", body)

    def test_each_valid_version_check_outcome_reaches_the_body(self):
        """A narrower allowlist would reject current or unverified without this failing."""
        for outcome in ("current", "update-available", "unverified"):
            with self.subTest(outcome):
                self.assertIn(f"version check: {outcome}", body_for(good_report(version_check=outcome)))

    def test_a_non_string_version_check_is_rejected_not_crashed(self):
        for bad in ([], {}, 3):
            with self.subTest(repr(bad)):
                problems, _ = validate(good_report(version_check=bad))
                self.assertTrue(any("version_check" in p for p in problems), problems)

    def test_an_unknown_version_check_outcome_is_rejected(self):
        problems, _ = validate(good_report(version_check="probably fine"))
        self.assertTrue(any("version_check" in p for p in problems), problems)

    def test_each_kind_renders_its_own_sections(self):
        for kind, sections in KINDS.items():
            with self.subTest(kind):
                report = good_report(kind=kind,
                                     sections={k: f"text for {k}" for k, _ in sections})
                body = body_for(report)
                for key, _ in sections:
                    self.assertIn(f"text for {key}", body)


class SensitiveValuesAreStrippedFromEveryFreeTextField(unittest.TestCase):
    def test_an_id_in_a_section_is_stripped(self):
        report = good_report()
        report["sections"]["happened"] = f"It wrote to {TABLE_ID} instead."
        body = body_for(report)
        self.assertNotIn(TABLE_ID, body)
        self.assertIn("[redacted: workspace-id]", body)

    def test_an_id_in_the_title_is_stripped(self):
        problems, cleaned = validate(good_report(title=f"Writes to {TABLE_ID} every run"))
        self.assertEqual(problems, [])
        title, body = render(cleaned)
        self.assertNotIn(TABLE_ID, title)
        self.assertNotIn(TABLE_ID, body)
        self.assertIn("[redacted: workspace-id]", title)

    def test_an_email_in_a_section_is_stripped(self):
        report = good_report()
        report["sections"]["did"] = "Scanned someone@example.com's account."
        body = body_for(report)
        self.assertNotIn("someone@example.com", body)
        self.assertIn("[redacted: email-address]", body)

    def test_the_body_discloses_what_was_stripped(self):
        report = good_report()
        report["sections"]["did"] = f"Used {TABLE_ID} and someone@example.com."
        body = body_for(report)
        self.assertIn("2 value(s) were stripped", body)

    def test_a_clean_report_says_nothing_needed_stripping(self):
        self.assertIn("Nothing needed stripping", body_for(good_report()))


class TheStructuredFieldsAreAllowlisted(unittest.TestCase):
    def test_an_unknown_kind_is_rejected(self):
        problems, _ = validate(good_report(kind="rant"))
        self.assertTrue(any("kind" in p for p in problems))

    def test_a_free_typed_target_is_rejected(self):
        """A target that is not a shipped skill or a named area cannot carry an identifier."""
        problems, _ = validate(good_report(target=f"acme-{TABLE_ID}"))
        self.assertTrue(any("target" in p for p in problems))

    def test_every_shipped_skill_is_a_valid_target(self):
        shipped = {p.name for p in (REPO_ROOT / "skills").iterdir() if (p / "SKILL.md").exists()}
        self.assertTrue(shipped)
        self.assertEqual(shipped | AREAS, known_targets())

    def test_an_unknown_connector_or_state_is_rejected(self):
        problems, _ = validate(good_report(connectors=[{"name": "acme-crm", "state": "S4"}]))
        self.assertTrue(any("connector" in p for p in problems))
        problems, _ = validate(good_report(connectors=[{"name": "apollo", "state": "S9"}]))
        self.assertTrue(any("state" in p for p in problems))

    def test_a_missing_section_is_rejected(self):
        report = good_report()
        del report["sections"]["expected"]
        problems, _ = validate(report)
        self.assertTrue(any("expected" in p for p in problems))

    def test_a_section_from_another_kind_is_rejected(self):
        report = good_report()
        report["sections"]["want"] = "a pony"
        problems, _ = validate(report)
        self.assertTrue(any("unknown section" in p for p in problems))

    def test_a_section_one_over_the_redaction_limit_is_rejected_not_truncated(self):
        """validate() and redact_note() must agree on the limit, or a section in the band
        between them is silently cut at the end, where the reproduction usually is."""
        report = good_report()
        report["sections"]["did"] = "x" * (MAX_NOTE_CHARS + 1)
        problems, _ = validate(report)
        self.assertTrue(any("did" in p and "over" in p for p in problems), problems)
        report["sections"]["did"] = "x" * MAX_NOTE_CHARS
        problems, cleaned = validate(report)
        self.assertEqual(problems, [])
        self.assertNotIn("over-length", cleaned["redactions"])

    def test_an_unhashable_enum_value_is_a_rejection_not_a_crash(self):
        for field, value in (("kind", ["bug"]), ("surface", {"a": 1}),
                             ("connectors", [{"name": ["apollo"], "state": "S4"}]),
                             ("connectors", [{"name": "apollo", "state": {"S4": 1}}])):
            with self.subTest(field=field):
                problems, _ = validate(good_report(**{field: value}))
                self.assertTrue(problems)

    def test_a_non_semver_version_is_rejected(self):
        problems, _ = validate(good_report(plugin_version="latest"))
        self.assertTrue(any("plugin_version" in p for p in problems))

    def test_every_kind_has_an_issue_form_that_exists(self):
        for kind, form in FORMS.items():
            with self.subTest(kind):
                self.assertIn(kind, KINDS)
                self.assertTrue((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / form).exists(), form)

    def test_the_paste_url_names_the_form_for_the_kind(self):
        url = paste_url("feature", "[feature] x")
        self.assertIn("template=feature_request.yml", url)
        self.assertTrue(url.startswith("https://github.com/"))


class TheIssueFormsMatchTheScript(unittest.TestCase):
    """The forms are the human path; the script is the agent path. Same sections."""

    FORM_DIR = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
    SCALAR = re.compile(r"^\s*(?:description|label|about|title|name):\s+(?P<v>.*)$")
    WELL_QUOTED = re.compile(r'^"(?:[^"\\]|\\.)*"$|^\'(?:[^\']|\'\')*\'$')

    def test_every_section_key_is_a_field_id_in_its_form(self):
        for kind, sections in KINDS.items():
            text = (self.FORM_DIR / FORMS[kind]).read_text("utf-8")
            for key, _prompt in sections:
                with self.subTest(kind=kind, key=key):
                    self.assertTrue(re.search(rf"^\s+id: {re.escape(key)}$", text, re.M),
                                    f"{FORMS[kind]} lacks a field with id {key}")

    def test_every_form_scalar_is_well_formed(self):
        """Two defects seen on the first drafts of bug_report.yml, both of which GitHub
        answers by silently falling back to a blank issue: a `: ` inside an unquoted
        scalar (a second mapping key), and a quoted scalar with trailing characters after
        its closing quote (an extra `"`). PyYAML is not in CI, so this is the check."""
        for form in sorted(self.FORM_DIR.glob("*.yml")):
            self.assertEqual(self.scalar_problems(form.read_text("utf-8")), [], form.name)

    @classmethod
    def scalar_problems(cls, text):
        problems = []
        for n, line in enumerate(text.splitlines(), 1):
            m = cls.SCALAR.match(line)
            if not m:
                continue
            v = m.group("v")
            if v[0] in "\"'":
                if not cls.WELL_QUOTED.match(v):
                    problems.append(f"line {n}: quoted scalar is malformed")
            elif v[0] not in "|>" and ": " in v:
                problems.append(f"line {n}: unquoted scalar contains ': '")
        return problems

    def test_the_scalar_check_sees_top_level_fields_and_both_defect_classes(self):
        """Pinned on synthetic text so the check is falsifiable without editing a form:
        a top-level description with an unquoted ': ' (zero indentation, which the first
        version of this regex skipped), a nested one, and a doubled closing quote."""
        self.assertEqual(self.scalar_problems('name: Bug report\ndescription: "fine: quoted"\n'), [])
        self.assertTrue(self.scalar_problems("name: Bug report\ndescription: Bug: details\n"))
        self.assertTrue(self.scalar_problems("  attributes:\n    label: Kind: of thing\n"))
        self.assertTrue(self.scalar_problems('    description: "doubled.""\n'))

    def test_blank_issues_are_off(self):
        self.assertIn("blank_issues_enabled: false",
                      (self.FORM_DIR / "config.yml").read_text("utf-8"))


def token_for_report(report):
    problems, cleaned = validate(report)
    assert not problems, problems
    title, body = render(cleaned)
    return token_for(title + "\n" + body)


class TheApprovalIsBound(unittest.TestCase):
    def test_a_changed_section_changes_the_token(self):
        report = good_report()
        report["sections"]["did"] = "Something else entirely."
        self.assertNotEqual(token_for_report(good_report()), token_for_report(report))

    def test_a_changed_title_changes_the_token(self):
        """The title is filed too, so an edit to it after preview must invalidate the approval."""
        self.assertNotEqual(token_for_report(good_report()),
                            token_for_report(good_report(title="A different title")))

    def test_rendering_never_calls_submit(self):
        """In-process, with submit patched to explode: the render path must not reach it,
        or a machine with an authenticated gh files a real issue at preview time."""
        import feedback
        from unittest import mock
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(good_report(), f)
        with mock.patch.object(feedback, "submit", side_effect=AssertionError("submit called")), \
             mock.patch.object(sys, "argv", ["feedback.py", "--report", f.name]), \
             mock.patch.object(sys, "stdout", new_callable=lambda: __import__("io").StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                feedback.main()
        self.assertEqual(ctx.exception.code, 0)


class TheCliBehaves(unittest.TestCase):
    def run_cli(self, report, *extra):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(report, f)
        return subprocess.run([sys.executable, str(SCRIPT), "--report", f.name, *extra],
                              capture_output=True, text=True)

    def test_rendering_exits_zero_and_sends_nothing(self):
        proc = self.run_cli(good_report())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing has been sent", proc.stdout)
        self.assertIn("--confirm", proc.stdout)

    def test_submitting_without_a_token_is_refused(self):
        proc = self.run_cli(good_report(), "--submit")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Refusing", proc.stderr)

    def test_submitting_with_a_wrong_token_is_refused(self):
        proc = self.run_cli(good_report(), "--submit", "--confirm", "000000000000")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Refusing", proc.stderr)

    def test_a_broken_report_exits_one(self):
        proc = self.run_cli(good_report(kind="rant"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("REJECTED", proc.stdout)

    def test_a_non_object_report_is_rejected_rather_than_crashing(self):
        proc = self.run_cli(["not", "an", "object"])
        self.assertEqual(proc.returncode, 1)

    def test_json_mode_carries_the_token_redactions_and_paste_url(self):
        report = good_report()
        report["sections"]["did"] = f"Used {TABLE_ID}."
        proc = self.run_cli(report, "--json")
        out = json.loads(proc.stdout)
        self.assertEqual(out["verdict"], "READY")
        self.assertEqual(out["confirm_token"], token_for(out["title"] + "\n" + out["body"]))
        self.assertEqual(out["redactions"], ["workspace-id"])
        self.assertIn("bug_report.yml", out["paste_url"])

    def test_schema_prints_the_sections_for_every_kind(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--schema"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(set(json.loads(proc.stdout)["sections"]), set(KINDS))


if __name__ == "__main__":
    unittest.main()
