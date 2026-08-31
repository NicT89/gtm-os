#!/usr/bin/env python3
"""Validate the instance config and the skills' references to it.

Two independent checks:

1. **Reference check (always runs, no real config needed).** Every `{KEY}` token
   used in a skill or reference doc must exist in instance-config.example.json.
   This is what catches a typo'd key — a skill asking for a value that will never
   be supplied, which at runtime looks like a missing ID rather than a bug.

2. **Config check (runs when instance-config.json exists).** That file must define
   exactly the schema's keys, leave no required key empty, and use plausible ID
   formats for the values it does supply.

Usage:
    python3 scripts/validate_instance_config.py [--config instance-config.json]

Exit code 0 = all checks pass, 1 = a check failed, 2 = usage error.

Runtime placeholders like {MOTION} are NOT config keys — they are filled in during
a run. They live in RUNTIME_PLACEHOLDERS below and are exempt from check 1. Adding
a new one there is a deliberate act: prefer a config key when the value is fixed
for a deployment.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "instance-config.example.json"

# Tokens that look like config keys but are filled in at run time, or are prose
# referring to the mechanism itself rather than to a specific key.
RUNTIME_PLACEHOLDERS = {
    "MOTION",
    "ACCOUNT_LIST",
    "CONTACT_LISTS",
    "SEQUENCE",
    "KEY",
    "KEY_NAME",
}

# Keys allowed to stay empty: optional connectors, or values only some deployments use.
OPTIONAL_KEYS = {
    "APOLLO_CF_ACCOUNT_CBI_MOSAIC_SCORE",
    "APOLLO_CF_ACCOUNT_CBI_COMMERCIAL_MATURITY",
    "APOLLO_CF_ACCOUNT_NAMED_INVESTORS",
    "APOLLO_CF_ACCOUNT_AVAILABLE_GTM_ROLES",
    "APOLLO_CF_ACCOUNT_LINKEDIN_COMPANY_SUMMARY",
    "APOLLO_CF_CONTACT_PERSONA_INTELLIGENCE",
    "APOLLO_CF_CONTACT_HAS_LINKEDIN",
    "APOLLO_CF_CONTACT_STARTUP_SMB_FIT",
    # Research Vault: optional. Empty means the Vault write steps in
    # company-deep-research, gap-closer, event-attribution, and the fan-out
    # harness skip cleanly and say so, rather than guessing a base.
    "AIRTABLE_VAULT_BASE_ID",
    "AIRTABLE_TBL_VAULT_FIELD_KEYS",
    "AIRTABLE_TBL_VAULT_ENTITIES",
    "AIRTABLE_TBL_VAULT_FACTS",
    "AIRTABLE_TBL_VAULT_RUNS",
    "AIRTABLE_TBL_VAULT_QUESTIONS",
    # Tracking: optional. A posts base built before this field existed has no ID
    # to supply; scrape-linkedin-posts then treats every row as in scope for a
    # scheduled refresh and reports that it did so.
    "AIRTABLE_FLD_CONTACTS_TRACKING",
    "AIRTABLE_FLD_COMPANY_TRACKING",
}

# Single-brace {TOKEN}, not part of a {{merge token}}.
TOKEN_RE = re.compile(r"(?<!\{)\{([A-Z][A-Z0-9_]*)\}(?!\})")

SCANNED_GLOBS = ("skills/**/*.md", "references/*.md")


def load_schema():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return {k for k in schema if not k.startswith("_")}, schema


def check_references(schema_keys):
    """Every {KEY} used in prose must be a real config key."""
    problems = []
    for glob in SCANNED_GLOBS:
        for path in sorted(REPO_ROOT.glob(glob)):
            text = path.read_text(encoding="utf-8")
            for token in sorted(set(TOKEN_RE.findall(text))):
                if token in RUNTIME_PLACEHOLDERS or token in schema_keys:
                    continue
                rel = path.relative_to(REPO_ROOT)
                problems.append(f"{rel}: {{{token}}} is not a key in instance-config.example.json")
    return problems


def looks_like_id(key, value):
    """Plausibility only — we cannot verify an ID exists without calling the API."""
    if key.startswith("AIRTABLE_") and key.endswith("_BASE_ID"):
        return value.startswith("app")
    if key.startswith("AIRTABLE_TBL_"):
        return value.startswith("tbl")
    if key.startswith("AIRTABLE_FLD_"):
        return value.startswith("fld")
    if key.startswith("APOLLO_CF_"):
        return bool(re.fullmatch(r"[0-9a-f]{24}", value))
    return True


def check_config(config_path, schema_keys):
    problems = []
    try:
        with open(config_path) as f:
            config = json.load(f)
    except OSError as e:
        return [f"cannot read {config_path}: {e}"]
    except json.JSONDecodeError as e:
        return [f"{config_path} is not valid JSON: {e}"]

    config_keys = {k for k in config if not k.startswith("_")}

    for key in sorted(schema_keys - config_keys):
        problems.append(f"missing key: {key}")
    for key in sorted(config_keys - schema_keys):
        problems.append(f"unknown key (not in schema): {key}")

    for key in sorted(config_keys & schema_keys):
        value = config[key]
        if not isinstance(value, str):
            problems.append(f"{key}: expected a string, got {type(value).__name__}")
            continue
        if not value.strip():
            if key not in OPTIONAL_KEYS:
                problems.append(f"{key}: required but empty")
            continue
        if not looks_like_id(key, value):
            problems.append(f"{key}: '{value}' does not look like a valid ID for this key")

    return problems


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=None,
                   help="Path to instance-config.json. Defaults to the repo root copy if present.")
    args = p.parse_args()

    try:
        schema_keys, _ = load_schema()
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read {SCHEMA_PATH}: {e}", file=sys.stderr)
        sys.exit(2)

    failed = False

    ref_problems = check_references(schema_keys)
    if ref_problems:
        failed = True
        print("Reference check FAILED:")
        for problem in ref_problems:
            print(f"  {problem}")
    else:
        print(f"ok    every {{KEY}} in skills and references resolves ({len(schema_keys)} keys in schema)")

    config_path = Path(args.config) if args.config else REPO_ROOT / "instance-config.json"
    if config_path.exists():
        cfg_problems = check_config(config_path, schema_keys)
        if cfg_problems:
            failed = True
            print(f"Config check FAILED ({config_path.name}):")
            for problem in cfg_problems:
                print(f"  {problem}")
        else:
            print(f"ok    {config_path.name} is complete and well-formed")
    else:
        print(f"skip  no {config_path.name} yet — copy instance-config.example.json and fill it in")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
