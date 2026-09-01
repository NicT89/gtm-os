#!/usr/bin/env python3
"""Field completeness gate for gtm-blueprint.

Deterministic check that a contact record has the inputs a blueprint needs
BEFORE composition. Run this instead of eyeballing records: it never forgets
a field and its output is loggable to the audit trail.

Usage:
    python field_gate.py <contact_record.json> --motion funding|hiring [--config gate_config.json]

<contact_record.json> is the raw contact object as returned by the CRM API
(for Apollo: one element of apollo_contacts_search's "contacts" array,
which includes typed_custom_fields).

Exit code 0 = PASS, 1 = FAIL (required input missing), 2 = usage error.
Prints a JSON verdict with per-field status and remediation paths.

--config is effectively required. Without it the gate falls back to
EXAMPLE_CONFIG, whose keys are placeholders rather than real field IDs, so
every record fails closed and a warning is printed. Write a gate config from
your CRM's field inventory (see references/instance-config.md); the logic
below is CRM-agnostic.
"""
import json
import sys
import argparse

# Shape reference ONLY — the keys below are placeholders, not real field IDs.
#
# Every deployment must pass --config with its own file, whose keys are that CRM's
# actual custom field IDs (see references/instance-config.md). Running against this
# example gates on fields that do not exist, so every record fails closed. That is
# the intended failure direction, but it is not a working configuration.
EXAMPLE_CONFIG = {
    "custom_fields": {
        "FIELD_ID_LINKEDIN_PROFILE_SUMMARY": {
            "label": "LinkedIn Profile Summary",
            "populator": "crm_workflow",
            "requirement": "required",
            "remediation": "Re-add contact to the profile-enrichment workflow trigger list, wait, re-check.",
        },
        "FIELD_ID_RESEARCH_COMPANY_PROFILE": {
            "label": "Research Company Profile",
            "populator": "crm_workflow",
            "requirement": "one_of:company_context",
            "remediation": "Re-trigger the AI research play via list membership.",
        },
        "FIELD_ID_LINKEDIN_POSTS": {
            "label": "LinkedIn Posts",
            "populator": "scrape_linkedin_posts_skill",
            "requirement": "one_of:company_context",
            "remediation": "Run the scrape-linkedin-posts skill for this contact.",
        },
        "FIELD_ID_PERSONA_INTELLIGENCE": {
            "label": "Persona Intelligence",
            "populator": "crm_workflow",
            "requirement": "optional",
            "remediation": "Re-trigger via workflow list if wanted.",
        },
    },
    # Account-side system enrichment is verified by presence of these keys
    # on the record's organization/account payload when available.
    "min_hard_facts": 3,
}


def is_populated(value):
    """True when a field value carries real content.

    Absent, None, empty, and whitespace-only all count as unpopulated: a field
    holding only spaces is a field nobody filled in, and treating it as present
    is how an empty blueprint reaches a prospect.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def run_gate(record, config, motion):
    """Run the completeness gate over one record; return the verdict dict.

    Checks required fields and one_of groups from `config` against the record's
    custom fields. The verdict carries per-field status plus remediation for
    every failure, and is shaped to be logged to the audit trail verbatim.

    Fails closed: a record with no custom fields at all fails rather than
    passing on the absence of evidence.
    """
    fields = record.get("typed_custom_fields", {})
    results, missing_required, one_of_groups = [], [], {}

    for fid, spec in config["custom_fields"].items():
        populated = is_populated(fields.get(fid))
        results.append({
            "field": spec["label"],
            "field_id": fid,
            "populator": spec["populator"],
            "requirement": spec["requirement"],
            "populated": populated,
            "remediation": None if populated else spec["remediation"],
        })
        req = spec["requirement"]
        if req == "required" and not populated:
            missing_required.append(spec["label"])
        elif req.startswith("one_of:"):
            group = req.split(":", 1)[1]
            one_of_groups.setdefault(group, []).append(populated)

    for group, statuses in one_of_groups.items():
        if not any(statuses):
            missing_required.append(f"at least one field in group '{group}'")

    verdict = {
        "contact": record.get("name", "unknown"),
        "company": record.get("organization_name", "unknown"),
        "motion": motion,
        "gate": "PASS" if not missing_required else "FAIL",
        "missing_required": missing_required,
        "fields": results,
        "note": "Workflows are invisible to the API; this gate verifies OUTPUTS on the record. Compose the blueprint only on PASS.",
    }
    return verdict


def main():
    """CLI entry point: gate one record file and exit 0 on PASS, 1 on FAIL."""
    p = argparse.ArgumentParser()
    p.add_argument("record")
    p.add_argument("--motion", choices=["funding", "hiring"], required=True)
    p.add_argument("--config", default=None)
    args = p.parse_args()

    try:
        with open(args.record) as f:
            record = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read record: {e}", file=sys.stderr)
        sys.exit(2)

    config = EXAMPLE_CONFIG
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    else:
        print(
            "WARNING: no --config given, using EXAMPLE_CONFIG. Its keys are "
            "placeholders, not real field IDs, so this record will fail closed "
            "regardless of its contents. See references/instance-config.md.",
            file=sys.stderr,
        )

    verdict = run_gate(record, config, args.motion)
    print(json.dumps(verdict, indent=2))
    sys.exit(0 if verdict["gate"] == "PASS" else 1)


if __name__ == "__main__":
    main()
