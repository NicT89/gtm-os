"""Tests for scripts/validate_instance_config.py.

The validator's job is to fail when a deployment is misconfigured. A validator
that cannot fail is worse than none, because it reads as a passing gate. These
tests pin each way it is supposed to fail, plus the shape of the real schema.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_instance_config.py"

_spec = importlib.util.spec_from_file_location("validate_instance_config", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)

SCHEMA_KEYS, _RAW_SCHEMA = validator.load_schema()


def write_config(mapping):
    """Write a config dict to a temp file and return its path."""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(mapping, tmp)
    tmp.close()
    return Path(tmp.name)


def valid_config():
    """A config that should pass: plausible IDs for every required key."""
    config = {}
    for key in SCHEMA_KEYS:
        if key.startswith("AIRTABLE_") and key.endswith("_BASE_ID"):
            config[key] = "app" + "a" * 14
        elif key.startswith("AIRTABLE_TBL_"):
            config[key] = "tbl" + "a" * 14
        elif key.startswith("AIRTABLE_FLD_"):
            config[key] = "fld" + "a" * 14
        elif key.startswith("APOLLO_CF_"):
            config[key] = "0" * 24
        else:
            config[key] = "something"
    return config


class Schema(unittest.TestCase):
    """The shipped example schema is itself well-formed."""

    def test_example_config_parses_and_is_not_empty(self):
        """An unparseable or empty schema would make every other check vacuous."""
        self.assertGreater(len(SCHEMA_KEYS), 0)

    def test_underscore_prefixed_readme_key_is_not_a_config_key(self):
        """_README is guidance for the human, and must not be demanded of a config."""
        self.assertNotIn("_README", SCHEMA_KEYS)


class ReferenceCheck(unittest.TestCase):
    """Every {KEY} used in prose resolves to a real schema key."""

    def test_repo_as_shipped_has_no_dangling_key_references(self):
        """A typo'd {KEY} looks like a missing ID at run time, not like a bug."""
        self.assertEqual(validator.check_references(SCHEMA_KEYS), [])

    def test_runtime_placeholders_are_exempt(self):
        """{MOTION} is filled in per run, not per deployment, so it is not a config key."""
        # {MOTION} is filled in per run, not per deployment, so it must not be
        # reported even though it is not a config key.
        self.assertIn("MOTION", validator.RUNTIME_PLACEHOLDERS)
        self.assertNotIn("MOTION", SCHEMA_KEYS)


class ConfigCheck(unittest.TestCase):
    """Each way a real config file is supposed to fail."""

    def test_a_complete_config_passes(self):
        """The validator must be able to pass, or it reads as a gate while blocking everything."""
        path = write_config(valid_config())
        self.assertEqual(validator.check_config(path, SCHEMA_KEYS), [])

    def test_missing_key_is_reported(self):
        """A key the schema defines but the config omits is a gap, not a default."""
        config = valid_config()
        del config["AIRTABLE_POSTS_BASE_ID"]
        problems = validator.check_config(write_config(config), SCHEMA_KEYS)
        self.assertTrue(any("missing key: AIRTABLE_POSTS_BASE_ID" in p for p in problems))

    def test_unknown_key_is_reported(self):
        """An invented key is usually a typo of a real one, and would never be read."""
        config = valid_config()
        config["NOT_A_REAL_KEY"] = "x"
        problems = validator.check_config(write_config(config), SCHEMA_KEYS)
        self.assertTrue(any("unknown key" in p and "NOT_A_REAL_KEY" in p for p in problems))

    def test_empty_required_key_is_reported(self):
        """An empty required key is the failure the validator exists to catch early."""
        config = valid_config()
        config["AIRTABLE_TBL_CONTACTS"] = ""
        problems = validator.check_config(write_config(config), SCHEMA_KEYS)
        self.assertTrue(any("AIRTABLE_TBL_CONTACTS" in p and "required but empty" in p for p in problems))

    def test_empty_optional_key_is_allowed(self):
        """Optional connectors must not force a value nobody has."""
        config = valid_config()
        for key in validator.OPTIONAL_KEYS:
            config[key] = ""
        self.assertEqual(validator.check_config(write_config(config), SCHEMA_KEYS), [])

    def test_malformed_airtable_id_is_reported(self):
        """A table ID where a base ID belongs points the engine at the wrong object."""
        config = valid_config()
        config["AIRTABLE_POSTS_BASE_ID"] = "tblWrongPrefix1"
        problems = validator.check_config(write_config(config), SCHEMA_KEYS)
        self.assertTrue(any("AIRTABLE_POSTS_BASE_ID" in p and "does not look like" in p for p in problems))

    def test_malformed_vault_base_id_is_reported(self):
        """A second base must be checked too, not just the posts base by name.

        The check is keyed on the _BASE_ID suffix. Keyed on the posts base
        instead, the Vault would silently accept a table ID where a base ID
        belongs.
        """
        config = valid_config()
        config["AIRTABLE_VAULT_BASE_ID"] = "tblWrongPrefix1"
        problems = validator.check_config(write_config(config), SCHEMA_KEYS)
        self.assertTrue(any("AIRTABLE_VAULT_BASE_ID" in p and "does not look like" in p
                            for p in problems))

    def test_vault_keys_are_optional(self):
        """Running without the Vault is a supported configuration, not a broken one.

        All six keys empty must still validate; the skills degrade to
        report-only and say so.
        """
        config = valid_config()
        for key in SCHEMA_KEYS:
            if "VAULT" in key:
                config[key] = ""
        self.assertEqual(validator.check_config(write_config(config), SCHEMA_KEYS), [])

    def test_malformed_crm_field_id_is_reported(self):
        """CRM custom field IDs are 24-char hex; anything else was misread or truncated."""
        config = valid_config()
        config["APOLLO_CF_CONTACT_BLUEPRINT"] = "not-hex-and-too-short"
        problems = validator.check_config(write_config(config), SCHEMA_KEYS)
        self.assertTrue(any("APOLLO_CF_CONTACT_BLUEPRINT" in p for p in problems))

    def test_non_string_value_is_reported(self):
        """A JSON number where a string belongs must be reported, not coerced."""
        config = valid_config()
        config["AIRTABLE_POSTS_BASE_ID"] = 12345
        problems = validator.check_config(write_config(config), SCHEMA_KEYS)
        self.assertTrue(any("expected a string" in p for p in problems))

    def test_unreadable_config_is_reported_not_raised(self):
        """A missing path is a problem to report, not a traceback."""
        problems = validator.check_config(Path("/nonexistent/instance-config.json"), SCHEMA_KEYS)
        self.assertTrue(any("cannot read" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
