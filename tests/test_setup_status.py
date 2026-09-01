"""Tests for scripts/setup_status.py.

The script's whole reason to exist is the third state: a key that is non-empty,
works, and was never actually decided because it came in with a `cp` of the
example. If `default` ever collapses into `set`, the script stops earning its
place, so most of these tests pin that boundary.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


status = _load("setup_status", "scripts/setup_status.py")
validator = _load("validate_instance_config", "scripts/validate_instance_config.py")

SCHEMA = status.load_schema()


def write_config(mapping):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(mapping, tmp)
    tmp.close()
    return Path(tmp.name)


def filled_config(**overrides):
    """Every key given a plausible, deliberately-chosen value."""
    config = {}
    for key, shipped in SCHEMA.items():
        if key.startswith("AIRTABLE_") and key.endswith("_BASE_ID"):
            config[key] = "app" + "a" * 14
        elif key.startswith("AIRTABLE_TBL_"):
            config[key] = "tbl" + "a" * 14
        elif key.startswith("AIRTABLE_FLD_"):
            config[key] = "fld" + "a" * 14
        elif key.startswith("APOLLO_CF_"):
            config[key] = "0" * 24
        else:
            # Must differ from the shipped value, or it classifies as `default`.
            config[key] = "chosen-" + key.lower()
    config.update(overrides)
    return config


class Grouping(unittest.TestCase):
    def test_every_schema_key_lands_in_exactly_one_group(self):
        # An ungrouped key means a new config key was added without telling the
        # user what it blocks, which is the one thing this script is for.
        report, _ = status.build_report(write_config(filled_config()))
        grouped = [e["key"] for g in report["groups"] for e in g["keys"]]
        self.assertEqual(sorted(grouped), sorted(SCHEMA))
        self.assertEqual(len(grouped), len(set(grouped)), "a key was grouped twice")
        self.assertNotIn("Ungrouped", [g["group"] for g in report["groups"]])

    def test_vault_keys_group_separately_from_the_posts_base(self):
        report, _ = status.build_report(write_config(filled_config()))
        by_group = {g["group"]: [e["key"] for e in g["keys"]] for g in report["groups"]}
        vault = by_group["Research Vault (optional)"]
        posts = by_group["Airtable posts base"]
        self.assertTrue(all("VAULT" in k for k in vault))
        self.assertTrue(all("VAULT" not in k for k in posts))
        self.assertIn("AIRTABLE_VAULT_BASE_ID", vault)
        self.assertIn("AIRTABLE_POSTS_BASE_ID", posts)


class OptionalKeysStayInSync(unittest.TestCase):
    def test_the_two_scripts_agree_on_what_is_optional(self):
        # setup_status says a key is safe to leave empty; validate_instance_config
        # decides whether leaving it empty fails. If they drift, one of them lies.
        self.assertEqual(status.OPTIONAL_KEYS, validator.OPTIONAL_KEYS)

    def test_every_optional_key_is_a_real_schema_key(self):
        self.assertEqual(status.OPTIONAL_KEYS - set(SCHEMA), set())


class Classification(unittest.TestCase):
    def test_no_config_file_reports_everything_unset(self):
        report, code = status.build_report(Path("/nonexistent/instance-config.json"))
        self.assertFalse(report["config_present"])
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertEqual(code, 1)
        self.assertEqual(report["totals"]["set"], 0)

    def test_naive_copy_of_the_example_flags_the_shipped_defaults(self):
        # `cp instance-config.example.json instance-config.json` is the exact
        # gesture SETUP.md tells people to make, so this is the common case.
        report, code = status.build_report(write_config(dict(SCHEMA)))
        self.assertEqual(code, 1)  # required keys are empty
        self.assertEqual(report["verdict"], "INCOMPLETE")
        # The three non-empty shipped values must surface as unreviewed, not as set.
        self.assertEqual(
            sorted(report["unreviewed_defaults"]),
            sorted(k for k, v in SCHEMA.items() if v.strip()),
        )
        self.assertEqual(report["totals"]["set"], 0)

    def test_inherited_default_is_not_counted_as_set(self):
        config = filled_config(APIFY_POSTS_ACTOR=SCHEMA["APIFY_POSTS_ACTOR"])
        report, code = status.build_report(write_config(config))
        self.assertIn("APIFY_POSTS_ACTOR", report["unreviewed_defaults"])
        self.assertEqual(report["verdict"], "READY_WITH_DEFAULTS")
        # Still runnable: an inherited default is a working configuration.
        self.assertEqual(code, 0)
        self.assertEqual(report["required_still_open"], [])

    def test_a_chosen_value_that_differs_is_set(self):
        config = filled_config(APIFY_POSTS_ACTOR="someone-else/other-actor")
        report, code = status.build_report(write_config(config))
        self.assertEqual(report["verdict"], "READY")
        self.assertEqual(report["unreviewed_defaults"], [])
        self.assertEqual(code, 0)

    def test_whitespace_only_value_is_unset_not_set(self):
        config = filled_config(AIRTABLE_TBL_CONTACTS="   ")
        report, code = status.build_report(write_config(config))
        self.assertIn("AIRTABLE_TBL_CONTACTS", report["required_still_open"])
        self.assertEqual(code, 1)

    def test_absent_key_is_missing_and_blocks(self):
        config = filled_config()
        del config["AIRTABLE_TBL_CONTACTS"]
        report, code = status.build_report(write_config(config))
        self.assertIn("AIRTABLE_TBL_CONTACTS", report["required_still_open"])
        self.assertEqual(code, 1)

    def test_empty_optional_keys_do_not_block(self):
        config = filled_config()
        for key in status.OPTIONAL_KEYS:
            config[key] = ""
        report, code = status.build_report(write_config(config))
        self.assertEqual(report["required_still_open"], [])
        self.assertEqual(code, 0)

    def test_vault_left_empty_still_reports_ready(self):
        # The documented degrade path: no Vault is a supported configuration.
        config = filled_config()
        for key in SCHEMA:
            if "VAULT" in key:
                config[key] = ""
        report, code = status.build_report(write_config(config))
        self.assertEqual(code, 0)
        vault = next(g for g in report["groups"]
                     if g["group"] == "Research Vault (optional)")
        self.assertTrue(vault["ready"])


class Errors(unittest.TestCase):
    def test_malformed_json_is_a_usage_error_not_a_crash(self):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        tmp.write("{not json")
        tmp.close()
        report, code = status.build_report(Path(tmp.name))
        self.assertEqual(code, 2)
        self.assertIn("error", report)


if __name__ == "__main__":
    unittest.main()
