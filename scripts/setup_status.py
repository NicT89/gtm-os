#!/usr/bin/env python3
"""Report how far this deployment's instance-config has actually been filled in.

`validate_instance_config.py` answers "is this file well-formed?" This answers the
question a user setting up actually has: **what is left for me to replace, and what
does each gap block?**

The distinction that makes this worth a script is the third state. A key is not
just set or unset:

  unset    empty. Nothing was ever put here.
  default  non-empty, but still byte-identical to what instance-config.example.json
           ships. It WORKS, but nobody has confirmed it is right for this workspace.
  set      non-empty and different from the shipped value. Someone decided this.

A fresh `cp instance-config.example.json instance-config.json` inherits every shipped
default silently. Those defaults are the ones that get forgotten, because nothing
fails: the actor name, the CRM provider, the roster filename. This script names them
so they get a decision instead of a shrug.

Usage:
    python3 scripts/setup_status.py [--config instance-config.json] [--json]

Exit codes: 0 = usable (every required key has a value), 1 = at least one required
key is unset or absent, 2 = usage error.

A required key still holding its shipped default exits 0, because it is a working
configuration. It is reported loudly anyway, under its own verdict (READY_WITH_DEFAULTS),
because "works" and "was decided" are different things and only one of them survives
the first surprise.

Prints a human-readable report by default, or the raw verdict with --json so a run
can log it to the audit trail.
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "instance-config.example.json"

# Keys that may stay empty. Kept in sync with validate_instance_config.py's
# OPTIONAL_KEYS by the test suite, so the two files cannot silently disagree.
OPTIONAL_KEYS = {
    "APOLLO_CF_ACCOUNT_CBI_MOSAIC_SCORE",
    "APOLLO_CF_ACCOUNT_CBI_COMMERCIAL_MATURITY",
    "APOLLO_CF_ACCOUNT_NAMED_INVESTORS",
    "APOLLO_CF_ACCOUNT_AVAILABLE_GTM_ROLES",
    "APOLLO_CF_ACCOUNT_LINKEDIN_COMPANY_SUMMARY",
    "APOLLO_CF_CONTACT_PERSONA_INTELLIGENCE",
    "APOLLO_CF_CONTACT_HAS_LINKEDIN",
    "APOLLO_CF_CONTACT_STARTUP_SMB_FIT",
    "AIRTABLE_VAULT_BASE_ID",
    "AIRTABLE_TBL_VAULT_FIELD_KEYS",
    "AIRTABLE_TBL_VAULT_ENTITIES",
    "AIRTABLE_TBL_VAULT_FACTS",
    "AIRTABLE_TBL_VAULT_RUNS",
    "AIRTABLE_TBL_VAULT_QUESTIONS",
    "AIRTABLE_FLD_CONTACTS_TRACKING",
    "AIRTABLE_FLD_COMPANY_TRACKING",
}

# Ordered because setup has a dependency order and the report should read in it.
# Each group: (label, predicate, what a gap here blocks, how to close it).
GROUPS = [
    (
        "Instance identity",
        lambda k: k.startswith("INSTANCE_"),
        "Every skill. INSTANCE_FIELD_PREFIX becomes CRM field labels and merge "
        "tokens, so it must be chosen BEFORE any Apollo custom field is created.",
        "Pick a short prefix once and record it. Renaming later means editing "
        "every sequence that references the merge token.",
    ),
    (
        "CRM provider",
        lambda k: k == "CRM_PROVIDER",
        "Nothing on its own, but it names which API the field-writing calls target.",
        "Ships as 'apollo', the reference implementation. Confirm it rather than "
        "inheriting it.",
    ),
    (
        "Apollo custom fields",
        lambda k: k.startswith("APOLLO_CF_"),
        "gtm-blueprint, gtm-signal-scan, outreach-audit, company-deep-research "
        "writeback, scrape-linkedin-posts push-back.",
        "The human creates the field definitions in the Apollo UI (the API cannot), "
        "then read the 24-hex IDs out of a record's typed_custom_fields.",
    ),
    (
        "Apollo lists",
        lambda k: k.startswith("APOLLO_LIST_"),
        "gtm-signal-scan list routing, and the profile-enrichment workflow trigger.",
        "These are list NAMES, not IDs. Create them in Apollo first; the enrichment "
        "list name must match exactly what your enrichment workflow watches.",
    ),
    (
        "Airtable posts base",
        lambda k: k.startswith("AIRTABLE_") and "VAULT" not in k,
        "scrape-linkedin-posts entirely, and gtm-signal-scan Step 6.",
        "Build the base per references/airtable-posts-base.md, then read base, "
        "table, and field IDs from airtable.com/<base>/api/docs.",
    ),
    (
        "Research Vault (optional)",
        lambda k: "VAULT" in k,
        "Nothing hard-stops. Empty means company-deep-research, gap-closer, "
        "event-attribution, and the fan-out harness degrade to report-only: full "
        "reports, no persisted facts, no baseline for the next run to diff against.",
        "Build a second base per references/research-vault.md. Skip deliberately, "
        "not by accident.",
    ),
    (
        "Apify",
        lambda k: k.startswith("APIFY_"),
        "scrape-linkedin-posts.",
        "Ships pointing at the default posts actor. If you substitute an actor, "
        "scrape-linkedin-posts Step 4's parsing must be re-matched to its output.",
    ),
    (
        "Run artifacts",
        lambda k: k == "SCRAPE_ROSTER_ARTIFACT",
        "Nothing. It names the roster file every scrape run rebuilds.",
        "Ships as 'scrape-roster.md'. Change it only if that name collides with "
        "something in your artifact home.",
    ),
]


def load_schema():
    with open(SCHEMA_PATH) as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def classify(key, schema_value, config, config_present):
    """Return one of: unset, default, set, missing."""
    if not config_present:
        return "unset"
    if key not in config:
        return "missing"
    value = config[key]
    if not isinstance(value, str) or not value.strip():
        return "unset"
    if schema_value.strip() and value.strip() == schema_value.strip():
        return "default"
    return "set"


def build_report(config_path):
    schema = load_schema()
    config, config_present = {}, False

    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            config_present = True
        except (OSError, json.JSONDecodeError) as e:
            return {"error": f"cannot read {config_path}: {e}"}, 2

    assigned, groups = set(), []
    for label, predicate, blocks, how in GROUPS:
        keys = sorted(k for k in schema if predicate(k) and k not in assigned)
        assigned.update(keys)
        if not keys:
            continue
        entries = []
        for key in keys:
            entries.append({
                "key": key,
                "state": classify(key, schema[key], config, config_present),
                "required": key not in OPTIONAL_KEYS,
            })
        counts = {s: sum(1 for e in entries if e["state"] == s)
                  for s in ("set", "default", "unset", "missing")}
        blocking = [e for e in entries
                    if e["required"] and e["state"] in ("unset", "missing")]
        review = [e["key"] for e in entries if e["state"] == "default"]
        groups.append({
            "group": label,
            "blocks": blocks,
            "how_to_close": how,
            "counts": counts,
            "keys": entries,
            "ready": not blocking,
            "needs_attention": [e["key"] for e in blocking],
            "needs_review": review,
        })

    leftover = sorted(set(schema) - assigned)
    if leftover:
        groups.append({
            "group": "Ungrouped",
            "blocks": "Unknown: this key was added to the schema without a group "
                      "in setup_status.py. Add one.",
            "how_to_close": "See references/instance-config.md.",
            "counts": {},
            "keys": [{"key": k,
                      "state": classify(k, schema[k], config, config_present),
                      "required": k not in OPTIONAL_KEYS} for k in leftover],
            "ready": False,
            "needs_attention": leftover,
            "needs_review": [],
        })

    all_entries = [e for g in groups for e in g["keys"]]
    required_open = [e["key"] for e in all_entries
                     if e["required"] and e["state"] in ("unset", "missing")]
    unreviewed_defaults = [e["key"] for e in all_entries if e["state"] == "default"]

    report = {
        "config_present": config_present,
        "config_path": str(config_path),
        "totals": {
            "keys": len(all_entries),
            "set": sum(1 for e in all_entries if e["state"] == "set"),
            "default": len(unreviewed_defaults),
            "unset": sum(1 for e in all_entries if e["state"] == "unset"),
            "missing": sum(1 for e in all_entries if e["state"] == "missing"),
        },
        "required_still_open": required_open,
        "unreviewed_defaults": unreviewed_defaults,
        "groups": groups,
        "verdict": ("INCOMPLETE" if required_open
                    else "READY_WITH_DEFAULTS" if unreviewed_defaults
                    else "READY"),
    }
    return report, (0 if not required_open else 1)


MARK = {"set": "set     ", "default": "DEFAULT ", "unset": "unset   ", "missing": "MISSING "}


def print_human(report):
    if not report["config_present"]:
        print(f"No {Path(report['config_path']).name} yet.\n")
        print("  cp instance-config.example.json instance-config.json\n")
        print("Then re-run this. Everything below is what you will need to fill in.\n")

    for g in report["groups"]:
        flag = "TODO" if not g["ready"] else ("look" if g["needs_review"] else "ok  ")
        print(f"{flag}  {g['group']}")
        for e in g["keys"]:
            opt = "" if e["required"] else "  (optional)"
            print(f"        {MARK[e['state']]} {e['key']}{opt}")
        if not g["ready"]:
            print(f"        blocks: {g['blocks']}")
            print(f"        close it: {g['how_to_close']}")
        elif g["needs_review"]:
            print(f"        works as shipped: {g['how_to_close']}")
        print()

    t = report["totals"]
    print(f"{t['set']} set, {t['default']} still shipped defaults, "
          f"{t['unset']} unset, {t['missing']} missing of {t['keys']} keys.")

    if report["unreviewed_defaults"]:
        print("\nStill on the value this repo ships. These work, which is exactly why")
        print("they get forgotten. Confirm each is right for your workspace:")
        for key in report["unreviewed_defaults"]:
            print(f"  - {key}")

    print(f"\n{report['verdict']}", end="")
    if report["required_still_open"]:
        print(f": {len(report['required_still_open'])} required key(s) still open.")
        print("Run the environment-setup skill, or see references/environment-setup.md.")
        return
    if report["unreviewed_defaults"]:
        print(": runnable, but the values above were inherited, not chosen.")
    else:
        print(".", end=" ")
    print("Shape is not existence: prove it with the one-target dry run in")
    print("SETUP.md Step 4 before trusting it.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=None,
                   help="Path to instance-config.json. Defaults to the repo root copy.")
    p.add_argument("--json", action="store_true", help="Emit the raw verdict as JSON.")
    args = p.parse_args()

    try:
        load_schema()
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read {SCHEMA_PATH}: {e}", file=sys.stderr)
        sys.exit(2)

    config_path = Path(args.config) if args.config else REPO_ROOT / "instance-config.json"
    report, code = build_report(config_path)

    if "error" in report:
        print(report["error"], file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)
    sys.exit(code)


if __name__ == "__main__":
    main()
