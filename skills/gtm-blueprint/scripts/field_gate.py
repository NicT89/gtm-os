#!/usr/bin/env python3
"""Field completeness gate for gtm-blueprint.

Deterministic check that a contact record has the inputs a blueprint needs
BEFORE composition. Run this instead of eyeballing records: it never forgets
a field and its output is loggable to the audit trail.

Usage:
    python field_gate.py <record.json> --signal-type funding|hiring [--config gate_config.json]

`--signal-type` is the axis that says what pulled the account into the run. It is NOT the
GTM motion: the motion is one of the five shapes in references/motion-templates.md (or a
custom one) and decides the plan and the closer, while the signal type decides which
account fields the opener's hard number can come from. The flag was called `--motion` until
1.9.4, which is where the confusion started; that spelling still works and prints a
deprecation notice.

Two things this gate did not check until 1.9.4, both of which it appeared to:

**The signal type was accepted and never used.** It was echoed into the verdict and
nothing branched on it, so a hiring record missing GTM Jobs w/ URL, JD Summary and Role
Archetypes — all three of which SKILL.md requires for that signal — exited 0 = PASS. The
flag was required, which is what made this hard to see: a mandatory argument reads as a
mandatory check.

**`min_hard_facts` sat in the config and nothing read it.** "Never compose from fewer than
three hard facts" is a rule the gate looked like it enforced.

What the fact floor can and cannot do: a script cannot tell whether a populated field
yields a quotable number, so this counts populated FACT-BEARING SOURCES and treats the
count as a floor. Three sources is a necessary condition for three hard facts, never a
sufficient one; the pre-send review is still where a human reads the facts themselves. A
floor that is honest about being a floor beats a check that implies more than it does.

<record.json> is the raw contact object as returned by the CRM API (for Apollo: one element
of apollo_contacts_search's "contacts" array, which includes typed_custom_fields). Account
fields are read from `organization.typed_custom_fields`, or from the path named by the
config's `account_path`.

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
    # Account-side fields required for ONE signal type only. Hiring cannot produce its
    # opener without the req, the JD and the archetype; funding's equivalents arrive
    # through system enrichment rather than custom fields, so its list is empty here.
    # SKILL.md Step 2 is the source of both lists.
    "account_fields": {
        "hiring": {
            "FIELD_ID_GTM_JOBS_WITH_URL": {
                "label": "GTM Jobs w/ URL",
                "populator": "ai_field_prompt",
                "remediation": "Re-run gtm-signal-scan step 3 for this account, or write the role | URL | posted-date lines by hand.",
            },
            "FIELD_ID_JD_SUMMARY": {
                "label": "JD Summary",
                "populator": "ai_field_prompt",
                "remediation": "Re-trigger the JD summary field prompt on the account.",
            },
            "FIELD_ID_ROLE_ARCHETYPES": {
                "label": "Role Archetypes",
                "populator": "signal_scan",
                "remediation": "Classify the req into an archetype during gtm-signal-scan step 3.",
            },
        },
        "funding": {},
    },
    # Where account fields live on the record. Apollo nests the organization.
    "account_path": ["organization", "typed_custom_fields"],
    # System-enrichment keys on the organization payload that carry a citable number or
    # named fact. Counted toward the floor when populated; never required individually,
    # because which ones a given company has is not something a gate should dictate.
    "system_enrichment_keys": [
        "annual_revenue",
        "estimated_num_employees",
        "latest_funding_stage",
        "latest_funding_round_date",
        "technology_names",
    ],
    # A necessary floor, not a sufficient test. See the module docstring.
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


def dig(record, path):
    """Walk a list of keys into nested dicts, returning {} rather than raising.

    A missing account payload must read as "no account fields populated", which fails the
    hiring requirements closed. Raising here would turn a gate failure into a crash, and a
    crash in a loop over a cohort gets worked around rather than fixed.
    """
    node = record
    for key in path:
        if not isinstance(node, dict):
            return {}
        node = node.get(key)
    return node if isinstance(node, dict) else {}


def run_gate(record, config, signal_type):
    """Run the completeness gate over one record; return the verdict dict.

    Three checks, and the second two did not exist until 1.9.4:

    1. Contact custom fields: `required` and `one_of:<group>` from the config.
    2. Account fields required by THIS signal type. `signal_type` used to be accepted and
       ignored, so a hiring record with no req, no JD and no archetype passed.
    3. The fact floor: populated fact-bearing sources against `min_hard_facts`. A count of
       sources is a necessary condition for that many hard facts, never a sufficient one.

    The verdict carries per-field status plus remediation for every failure, and is shaped
    to be logged to the audit trail verbatim.

    Fails closed: a record with no custom fields at all fails rather than passing on the
    absence of evidence.
    """
    fields = record.get("typed_custom_fields", {})
    results, missing_required, one_of_groups = [], [], {}
    fact_sources = []

    for fid, spec in config["custom_fields"].items():
        populated = is_populated(fields.get(fid))
        results.append({
            "field": spec["label"],
            "field_id": fid,
            "scope": "contact",
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
        if populated and req != "optional":
            fact_sources.append(spec["label"])

    for group, statuses in one_of_groups.items():
        if not any(statuses):
            missing_required.append(f"at least one field in group '{group}'")

    # 2. Account fields this signal type cannot compose without.
    account_fields = dig(record, config.get("account_path") or ["organization", "typed_custom_fields"])
    for fid, spec in (config.get("account_fields", {}).get(signal_type) or {}).items():
        populated = is_populated(account_fields.get(fid))
        results.append({
            "field": spec["label"],
            "field_id": fid,
            "scope": "account",
            "populator": spec["populator"],
            "requirement": f"required for signal type '{signal_type}'",
            "populated": populated,
            "remediation": None if populated else spec["remediation"],
        })
        if not populated:
            missing_required.append(f"{spec['label']} (account, required for {signal_type})")
        else:
            fact_sources.append(spec["label"])

    # 3. The fact floor.
    organization = record.get("organization") if isinstance(record.get("organization"), dict) else {}
    for key in config.get("system_enrichment_keys", []):
        if is_populated(organization.get(key)):
            fact_sources.append(f"organization.{key}")

    min_facts = config.get("min_hard_facts", 3)
    if len(fact_sources) < min_facts:
        missing_required.append(
            f"only {len(fact_sources)} fact-bearing source(s) populated; the floor is {min_facts}"
        )

    verdict = {
        "contact": record.get("name", "unknown"),
        "company": record.get("organization_name", "unknown"),
        "signal_type": signal_type,
        "gate": "PASS" if not missing_required else "FAIL",
        "missing_required": missing_required,
        "fact_bearing_sources": sorted(fact_sources),
        "fact_floor": {"count": len(fact_sources), "minimum": min_facts},
        "fields": results,
        "note": ("Workflows are invisible to the API; this gate verifies OUTPUTS on the "
                 "record. Compose the blueprint only on PASS. The fact floor counts "
                 "populated SOURCES, which is necessary for three hard facts and not "
                 "sufficient: a human still reads the facts at pre-send review."),
    }
    return verdict


def main():
    """CLI entry point: gate one record file and exit 0 on PASS, 1 on FAIL."""
    p = argparse.ArgumentParser()
    p.add_argument("record")
    p.add_argument("--signal-type", dest="signal_type", choices=["funding", "hiring"],
                   help="What pulled this account into the run. NOT the GTM motion.")
    # The 1.9.3-and-earlier spelling. Kept working rather than broken: a logged command in
    # somebody's audit trail should still run. It is confusing, not wrong, so it warns.
    p.add_argument("--motion", dest="motion", choices=["funding", "hiring"],
                   help=argparse.SUPPRESS)
    p.add_argument("--config", default=None)
    args = p.parse_args()

    if args.signal_type and args.motion and args.signal_type != args.motion:
        print("--signal-type and the deprecated --motion disagree; pass one.", file=sys.stderr)
        sys.exit(2)
    signal_type = args.signal_type or args.motion
    if not signal_type:
        print("--signal-type is required (funding|hiring).", file=sys.stderr)
        sys.exit(2)
    if args.motion and not args.signal_type:
        print("NOTE: --motion is the old name for --signal-type and will keep working. "
              "The GTM motion is a different axis: it is one of the five shapes in "
              "references/motion-templates.md and it decides the plan and the closer.",
              file=sys.stderr)

    try:
        with open(args.record) as f:
            record = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read record: {e}", file=sys.stderr)
        sys.exit(2)

    config = EXAMPLE_CONFIG
    if args.config:
        # Unguarded until 1.9.4: a malformed or empty config raised a traceback rather than
        # exiting 2, so a typo in the path read as a crash in the gate itself.
        try:
            with open(args.config) as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Cannot read gate config {args.config}: {e}", file=sys.stderr)
            sys.exit(2)
        if not isinstance(config, dict) or not isinstance(config.get("custom_fields"), dict):
            print(f"Gate config {args.config} has no `custom_fields` object; see "
                  "references/instance-config.md.", file=sys.stderr)
            sys.exit(2)
    else:
        print(
            "WARNING: no --config given, using EXAMPLE_CONFIG. Its keys are "
            "placeholders, not real field IDs, so this record will fail closed "
            "regardless of its contents. See references/instance-config.md.",
            file=sys.stderr,
        )

    verdict = run_gate(record, config, signal_type)
    print(json.dumps(verdict, indent=2))
    sys.exit(0 if verdict["gate"] == "PASS" else 1)


if __name__ == "__main__":
    main()
