#!/usr/bin/env python3
"""Render the Project instructions block a deployment pastes into its Claude Project.

The instructions a Project carries are the same for every deployment except for a handful
of values (the company, the field prefix, which connectors are on, which fallbacks are
active) and one free-text block the organization writes in its own words. The universal
part is rendered here from references/project-instructions-template.md so no two
deployments drift; the organization-specific block is passed in as text and only
shape-checked (present, a few sentences, not a keyword).

The output is a human gate, not an API call: the skill shows it, the user pastes it into the
Project's instructions field, and project_info confirms the field is no longer empty before
onboarding continues. Nothing here writes to a Project.

Input JSON:
    {
      "company": "Acme",
      "instance_name": "acme",
      "field_prefix": "ACME",
      "crm_provider": "apollo" | "hubspot",
      "connectors": {"apollo": "on", "hubspot": "declined", "airtable": "on",
                     "apify": "on", "firecrawl": "on", "brand-kit-os": "absent"},
      "brand_context": "brand-kit-os" | "files",
      "brand_context_dir": "brand",
      "instance_config_path": "/path/on/the/filesystem/instance-config.json",
      "organization_rules": "Free text the organization wrote: names, spellings, what never gets said."
    }

Usage:
    python3 scripts/render_project_instructions.py --input onboarding.json [--json]

Exit code 0 = rendered, 1 = input rejected, 2 = usage error.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "references" / "project-instructions-template.md"

CONNECTORS = ("apollo", "hubspot", "airtable", "apify", "firecrawl", "brand-kit-os")
CONNECTOR_STATES = {"on", "declined", "absent"}
FALLBACKS = {
    "apollo": "no sourcing or enrichment; the engine works lists the user supplies",
    "hubspot": "no CRM write to HubSpot; Apollo is the CRM, or deliverables stay in chat",
    "airtable": "no posts base and no Research Vault; research reports are produced and nothing persists",
    "apify": "no LinkedIn post scraping; the posts digest field stays empty and is never faked",
    "firecrawl": "web extraction falls back to the host's fetch tool, which fails on ATS pages",
    "brand-kit-os": "brand context is read from the files in the brand folder",
}
PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{1,11}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


def validate(data):
    """Return (problems, cleaned)."""
    problems = []
    if not isinstance(data, dict):
        return ["input must be a JSON object"], None
    out = {}
    for key in ("company", "instance_name", "field_prefix", "crm_provider",
                "brand_context", "brand_context_dir", "instance_config_path",
                "organization_rules"):
        v = data.get(key)
        if not isinstance(v, str) or not v.strip():
            problems.append(f"{key} is required")
        out[key] = v.strip() if isinstance(v, str) else v
    if out.get("field_prefix") and not PREFIX_RE.match(out["field_prefix"]):
        problems.append("field_prefix must be 2 to 12 upper-case letters or digits")
    if out.get("instance_name") and not SLUG_RE.match(out["instance_name"]):
        problems.append("instance_name must be a lower-case slug")
    if out.get("crm_provider") not in ("apollo", "hubspot"):
        problems.append("crm_provider must be apollo or hubspot")
    if out.get("brand_context") not in ("brand-kit-os", "files"):
        problems.append("brand_context must be brand-kit-os or files")
    rules = out.get("organization_rules") or ""
    sentences = [s for s in re.split(r"[.!?]\s", rules) if s.strip()]
    if rules and (len(sentences) < 2 or len(rules) < 60):
        problems.append("organization_rules must be a few sentences in the organization's own "
                        "words, not a keyword; see the template's guidance")
    connectors = data.get("connectors")
    if not isinstance(connectors, dict):
        problems.append("connectors must be an object of name: on|declined|absent")
        connectors = {}
    out["connectors"] = {}
    for name in CONNECTORS:
        state = connectors.get(name, "absent")
        if state not in CONNECTOR_STATES:
            problems.append(f"connector {name} has invalid state {state!r}")
        out["connectors"][name] = state
    extra = set(connectors) - set(CONNECTORS)
    if extra:
        problems.append(f"unknown connector(s): {sorted(extra)}")
    if out.get("brand_context") == "brand-kit-os" and out["connectors"].get("brand-kit-os") != "on":
        problems.append("brand_context is brand-kit-os but the connector is not on")
    return problems, out


def render(cleaned):
    """Fill the template. Pure formatting."""
    template = TEMPLATE.read_text("utf-8")
    on = [n for n, s in cleaned["connectors"].items() if s == "on"]
    off = [(n, s) for n, s in cleaned["connectors"].items() if s != "on"]
    connector_lines = [f"- {n}: connected" for n in on]
    for n, s in off:
        connector_lines.append(f"- {n}: {s}; fallback: {FALLBACKS[n]}")
    if cleaned["brand_context"] == "brand-kit-os":
        brand = ("Brand context lives in Brand Kit OS. Pull it live through the connector at the "
                 "start of a task; never cache a kit dump here.")
    else:
        brand = (f"Brand context lives in the `{cleaned['brand_context_dir']}/` folder of the "
                 "workspace, one file per entity with provenance on every fact. Read only the "
                 "files a task needs. The live version is the Brand Kit OS connector; these files "
                 "are the fallback until it is connected.")
    fields = {
        "COMPANY": cleaned["company"],
        "INSTANCE_NAME": cleaned["instance_name"],
        "FIELD_PREFIX": cleaned["field_prefix"],
        "CRM_PROVIDER": cleaned["crm_provider"],
        "CONNECTOR_LINES": "\n".join(connector_lines),
        "BRAND_CONTEXT_PARAGRAPH": brand,
        "INSTANCE_CONFIG_PATH": cleaned["instance_config_path"],
        "ORGANIZATION_RULES": cleaned["organization_rules"],
    }
    # Only the paste block is output: everything above the marker is guidance for maintainers
    # and may mention placeholders by name, so the fill and the leftover check run on the
    # block alone.
    marker = "<!-- paste-block -->"
    body = template.split(marker, 1)[1] if marker in template else template
    # One pass over the TEMPLATE's placeholders only. A value is never re-scanned, so a
    # company called "{{X}}" or an organization rule that quotes a merge token of its own
    # ("{{FIRST_NAME}}" in an outbound template) is preserved verbatim rather than filled
    # or rejected. The leftover check therefore runs on the template, before substitution.
    leftover = [m.group(0) for m in PLACEHOLDER_RE.finditer(body) if m.group(1) not in fields]
    assert not leftover, f"template placeholders not filled: {leftover}"
    body = PLACEHOLDER_RE.sub(lambda m: fields[m.group(1)], body)
    return body.strip()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the onboarding JSON, or - for stdin.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text("utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read input: {e}", file=sys.stderr)
        sys.exit(2)
    problems, cleaned = validate(data)
    if problems:
        if args.json:
            print(json.dumps({"verdict": "REJECTED", "problems": problems}, indent=2))
        else:
            print("REJECTED:")
            for p in problems:
                print(f"  - {p}")
        sys.exit(1)
    text = render(cleaned)
    if args.json:
        print(json.dumps({"verdict": "RENDERED", "instructions": text,
                          "chars": len(text)}, indent=2))
    else:
        print(text)
    sys.exit(0)


if __name__ == "__main__":
    main()
