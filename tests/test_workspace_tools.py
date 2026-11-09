"""Pin the two onboarding scripts: the workspace shape gate and the instructions renderer.

Both are shape checks, never content checks. The tests build a correct workspace in a
temp dir and then break one thing at a time, so each assertion is known to catch the
defect it names.

Run: python3 -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_workspace as cw  # noqa: E402
import render_project_instructions as rpi  # noqa: E402

FRONT = "---\nentity: {entity}\nsource: files\nverified: 2026-11-08\nprovenance_default: UNVERIFIED\n---\n"


def good_workspace(root):
    root = Path(root)
    for d in cw.SCHEMA_DIRS + ["brand"]:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "_index" / "instance.md").write_text(
        "# Instance: acme\n\n- Field prefix: ACME\n- instance-config.json: /work/acme/instance-config.json\n")
    (root / "_index" / "overview.md").write_text("# Overview\n")
    (root / "_index" / "pending-tasks.md").write_text("# Pending\n")
    for name in cw.BRAND_FILES:
        entity = name[:-3]
        body = "" if name == "README.md" else "Serves mid-market finance teams. KNOWN (https://example.com/about)\n"
        (root / "brand" / name).write_text(FRONT.format(entity=entity) + body)
    return root


class TheWorkspaceGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = good_workspace(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_correct_workspace_passes(self):
        self.assertEqual(cw.check(self.root, "brand", "yes"), [])

    def test_a_missing_folder_fails(self):
        (self.root / "audit-log").rmdir()
        self.assertTrue(any("audit-log" in p for p in cw.check(self.root, "brand", "yes")))

    def test_a_missing_brand_file_fails(self):
        (self.root / "brand" / "governance.md").unlink()
        self.assertTrue(any("governance.md" in p for p in cw.check(self.root, "brand", "yes")))

    def test_a_brand_file_without_front_matter_fails(self):
        (self.root / "brand" / "products.md").write_text("Just text.\n")
        self.assertTrue(any("no front matter" in p for p in cw.check(self.root, "brand", "yes")))

    def test_an_unknown_source_fails(self):
        (self.root / "brand" / "products.md").write_text(
            FRONT.format(entity="products").replace("source: files", "source: guess"))
        self.assertTrue(any("source must be" in p for p in cw.check(self.root, "brand", "yes")))

    def test_a_quoted_front_matter_value_is_accepted(self):
        """`source: "files"` is the same value as `source: files`; YAML allows both."""
        (self.root / "brand" / "products.md").write_text(
            FRONT.format(entity="products").replace("source: files", 'source: "files"')
            .replace("provenance_default: UNVERIFIED", "provenance_default: 'UNVERIFIED'"))
        self.assertEqual(cw.check(self.root, "brand", "yes"), [])

    def test_a_number_without_a_label_fails(self):
        """The invented-number class: a quantity nobody sourced."""
        (self.root / "brand" / "proof-and-quotes.md").write_text(
            FRONT.format(entity="proof-and-quotes") + "Customers cut cost by 50%.\n")
        problems = cw.check(self.root, "brand", "yes")
        self.assertTrue(any("no KNOWN/INFERRED/UNVERIFIED label" in p for p in problems), problems)

    def test_a_single_digit_quantity_without_a_label_fails(self):
        """'Reduced onboarding to 3 days' is a claim too; one digit must not slip past."""
        (self.root / "brand" / "proof-and-quotes.md").write_text(
            FRONT.format(entity="proof-and-quotes") + "Reduced onboarding to 3 days.\n")
        problems = cw.check(self.root, "brand", "yes")
        self.assertTrue(any("no KNOWN/INFERRED/UNVERIFIED label" in p for p in problems), problems)

    def test_list_markers_dates_and_links_are_not_quantities(self):
        (self.root / "brand" / "products.md").write_text(
            FRONT.format(entity="products")
            + "1. Launched in 2024-03 per https://example.com/v2.1/notes\n"
            + "2. Second item with no number in it\n")
        self.assertEqual(cw.check(self.root, "brand", "yes"), [])

    def test_a_labeled_number_passes(self):
        (self.root / "brand" / "proof-and-quotes.md").write_text(
            FRONT.format(entity="proof-and-quotes") + "Customers cut cost by 50%. KNOWN (https://example.com/case)\n")
        self.assertEqual(cw.check(self.root, "brand", "yes"), [])

    def test_each_resolved_id_shape_in_the_instance_summary_fails(self):
        """One input per pattern in ID_RES, so dropping any one of them fails here."""
        samples = {
            "airtable-id": "app" + "Qx7Lm2Np9Rk4Wz1Ab"[:14],
            "hex-id": "".join("0123456789abcdef"[(i * 7) % 16] for i in range(24)),
            "digit-run": "".join(str((i * 3) % 10) for i in range(11)),
        }
        self.assertEqual(set(samples), {kind for kind, _ in cw.ID_RES})
        for kind, value in samples.items():
            with self.subTest(kind):
                (self.root / "_index" / "instance.md").write_text(f"# Instance\n\n- Ref: {value}\n")
                problems = cw.check(self.root, "brand", "yes")
                self.assertTrue(any(f"({kind})" in p for p in problems), problems)

    def test_a_path_in_the_instance_summary_passes(self):
        (self.root / "_index" / "instance.md").write_text(
            "# Instance\n\n- instance-config.json: /work/acme-2026/instance-config.json\n")
        self.assertEqual(cw.check(self.root, "brand", "yes"), [])

    def test_unconfirmed_instructions_fail(self):
        self.assertTrue(any("instructions" in p for p in cw.check(self.root, "brand", "no")))

    def test_the_no_project_path_passes(self):
        """Cowork with a folder and no Project skips the paste gate; the audit must not fail it."""
        self.assertEqual(cw.check(self.root, "brand", "not-applicable"), [])

    def test_an_unknown_pasted_state_fails(self):
        self.assertTrue(any("instructions-pasted" in p for p in cw.check(self.root, "brand", "maybe")))

    def test_the_cli_exit_codes(self):
        proc = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "check_workspace.py"),
                               "--workspace", str(self.root), "--instructions-pasted", "yes", "--json"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        out = json.loads(proc.stdout)
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual(out["instructions_pasted"], "yes", "the audit log must record the state judged")
        proc = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "check_workspace.py"),
                               "--workspace", str(self.root), "--instructions-pasted", "no"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)


def good_input(**over):
    d = {
        "company": "Acme", "instance_name": "acme", "field_prefix": "ACME",
        "crm_provider": "apollo",
        "connectors": {"apollo": "on", "hubspot": "declined", "airtable": "on",
                       "apify": "on", "firecrawl": "on", "brand-kit-os": "absent"},
        "brand_context": "files", "brand_context_dir": "brand",
        "instance_config_path": "/work/acme/instance-config.json",
        "organization_rules": "We write Acme, never ACME, in prose. Pricing is never quoted in outbound. Only the CEO contacts investors.",
    }
    d.update(over)
    return d


class TheInstructionsRenderer(unittest.TestCase):
    def test_a_good_input_renders_every_placeholder(self):
        problems, cleaned = rpi.validate(good_input())
        self.assertEqual(problems, [])
        text = rpi.render(cleaned)
        self.assertNotIn("{{", text)
        self.assertIn("Acme", text)
        self.assertIn("hubspot: declined; fallback:", text)
        self.assertIn("brand/", text)
        self.assertIn("never quoted in outbound", text)

    def test_a_placeholder_inside_a_value_is_preserved_not_filled(self):
        """An organization rule may quote a merge token of its own; it must survive verbatim."""
        rules = ("Outbound templates always carry {{FIRST_NAME}} as the greeting token. "
                 "We write Acme, never ACME, in prose. Pricing is never quoted in outbound.")
        problems, cleaned = rpi.validate(good_input(organization_rules=rules, company="{{INSTANCE_NAME}}"))
        self.assertEqual(problems, [])
        text = rpi.render(cleaned)
        self.assertIn("{{FIRST_NAME}}", text)
        self.assertIn("{{INSTANCE_NAME}}", text, "a value was re-scanned and filled")

    def test_only_the_paste_block_is_output(self):
        _, cleaned = rpi.validate(good_input())
        self.assertNotIn("for maintainers", rpi.render(cleaned))

    def test_brand_kit_os_mode_needs_the_connector_on(self):
        problems, _ = rpi.validate(good_input(brand_context="brand-kit-os"))
        self.assertTrue(any("connector is not on" in p for p in problems))
        c = good_input()["connectors"]; c["brand-kit-os"] = "on"
        problems, cleaned = rpi.validate(good_input(brand_context="brand-kit-os", connectors=c))
        self.assertEqual(problems, [])
        self.assertIn("Brand Kit OS", rpi.render(cleaned))

    def test_a_keyword_organization_block_is_rejected(self):
        problems, _ = rpi.validate(good_input(organization_rules="be professional"))
        self.assertTrue(any("organization_rules" in p for p in problems))

    def test_an_unknown_connector_state_is_rejected(self):
        c = good_input()["connectors"]; c["apollo"] = "maybe"
        problems, _ = rpi.validate(good_input(connectors=c))
        self.assertTrue(any("apollo" in p for p in problems))

    def test_every_connector_has_a_fallback_sentence(self):
        self.assertEqual(set(rpi.FALLBACKS), set(rpi.CONNECTORS))

    def test_the_template_has_every_placeholder_the_renderer_fills(self):
        template = rpi.TEMPLATE.read_text("utf-8")
        _, cleaned = rpi.validate(good_input())
        # Render with a sentinel so each field's presence in the template is observable.
        for key in ("COMPANY", "INSTANCE_NAME", "FIELD_PREFIX", "CRM_PROVIDER", "CONNECTOR_LINES",
                    "BRAND_CONTEXT_PARAGRAPH", "INSTANCE_CONFIG_PATH", "ORGANIZATION_RULES"):
            self.assertIn("{{" + key + "}}", template, key)


if __name__ == "__main__":
    unittest.main()
