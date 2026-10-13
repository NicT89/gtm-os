#!/usr/bin/env python3
"""Check planned HubSpot writes against the portal map BEFORE anything is sent.

HubSpot portals differ: custom properties, custom objects, picklist options, required
fields. A write shaped for one portal can fail on another, or worse, succeed and store the
wrong thing. This script is the pre-sync gate in references/hubspot-adapter.md. It reads
two files and calls nothing:

- the portal map ({HUBSPOT_PORTAL_MAP_FILE}), built from the HubSpot MCP's schema and
  property tools (discover_hubspot_schema, search_properties, get_properties);
- the planned writes, exactly as they would be passed to manage_crm_objects.

Every check is universal (the same for every portal), which is why it is code and not
prose. What each property MEANS for an organization stays in the portal map, decided by the
operator; this script only checks that a write fits the shape the portal declares.

Checks, per write:
  1. the object type is in the map and the map says the connected user can write it;
  2. every property exists on that object in the map;
  3. no property the map marks `owner: human` is changed on an existing record (a create
     may set one, since it is the record's first value: the dedupe key, usually);
  4. values are strings, as manage_crm_objects takes them;
  5. the value fits the property's type: number, bool, date (YYYY-MM-DD), datetime (ISO
     8601), enumeration (a declared option; multi-select values separated by ";");
  6. `max_length`, when the map declares one;
  7. a create carries the object's dedupe key and every required property, except on an
     object the map marks `append_only` (activity records such as notes, which are always
     new rows and have no natural key);
  8. association targets are object types in the map.
Batches over manage_crm_objects' 10-object limit are a warning: split them.

It does not replace the read-back. After the write, read the property out of HubSpot and
compare the value, per CLAUDE.md: a write that returns success can still store nothing.

Usage:
    python3 hubspot_presync.py portal-map.json planned-writes.json [--json]

Exit code 0 = every write passes (warnings allowed), 1 = problems, 2 = usage error.
Prose by default; --json for machines.
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

BATCH_LIMIT = 10  # manage_crm_objects: "a MAXIMUM of 10 objects per request"
TYPES = ("string", "number", "bool", "date", "datetime", "enumeration")
OWNERS = ("engine", "human")


def number_ok(value):
    """A decimal number as HubSpot stores it in a string."""
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", value))


def date_ok(value):
    """A bare calendar date."""
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def datetime_ok(value):
    """An ISO 8601 timestamp."""
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return "T" in value
    except ValueError:
        return False


def check_value(where, prop, spec, value):
    """Return problems for one property value against its portal-map spec."""
    if not isinstance(value, str):
        return [f"{where}: {prop} is {type(value).__name__}; send every value as a string"]
    kind = spec.get("type")
    problems = []
    if kind == "number" and not number_ok(value):
        problems.append(f"{where}: {prop}={value!r} is not a number")
    elif kind == "bool" and value not in ("true", "false"):
        problems.append(f"{where}: {prop}={value!r} must be 'true' or 'false'")
    elif kind == "date" and not date_ok(value):
        problems.append(f"{where}: {prop}={value!r} is not a YYYY-MM-DD date")
    elif kind == "datetime" and not datetime_ok(value):
        problems.append(f"{where}: {prop}={value!r} is not an ISO 8601 timestamp")
    elif kind == "enumeration":
        options = spec.get("options") or []
        chosen = value.split(";") if spec.get("multiple") else [value]
        for item in chosen:
            if item not in options:
                problems.append(f"{where}: {prop}={item!r} is not an option "
                                f"(portal allows {', '.join(options) or 'none'})")
    limit = spec.get("max_length")
    if isinstance(limit, int) and len(value) > limit:
        problems.append(f"{where}: {prop} is {len(value)} characters; the portal allows {limit}")
    return problems


def check_map(portal):
    """Return problems with the portal map itself, so a bad map cannot pass writes."""
    if not isinstance(portal, dict) or not isinstance(portal.get("objects"), dict):
        return ["the portal map must be an object with an `objects` object"]
    problems = []
    for obj, spec in portal["objects"].items():
        if not isinstance(spec, dict) or not isinstance(spec.get("properties"), dict):
            problems.append(f"objects.{obj} needs a `properties` object")
            continue
        for prop, pspec in spec["properties"].items():
            where = f"objects.{obj}.properties.{prop}"
            if not isinstance(pspec, dict) or pspec.get("type") not in TYPES:
                problems.append(f"{where}: `type` must be one of {', '.join(TYPES)}")
                continue
            if pspec.get("owner") not in OWNERS:
                problems.append(f"{where}: `owner` must be engine or human; a property with "
                                "no owner could be a human-managed one written by mistake")
            options = pspec.get("options")
            if pspec["type"] == "enumeration" and not (
                    isinstance(options, list) and options
                    and all(isinstance(o, str) for o in options)):
                problems.append(f"{where}: an enumeration needs its `options` as a "
                                "non-empty list of strings")
    return problems


def check(portal, plan):
    """Return (problems, warnings). Pure, so every rule is directly testable."""
    problems = check_map(portal)
    if problems:
        return problems, []
    writes = plan.get("writes") if isinstance(plan, dict) else None
    if not isinstance(writes, list):
        return ["the planned writes must be an object with a `writes` list"], []
    warnings = []
    per_object = {}
    objects = portal["objects"]
    for i, write in enumerate(writes):
        where = f"writes[{i}]"
        if not isinstance(write, dict):
            problems.append(f"{where} is not an object")
            continue
        obj = write.get("object")
        spec = objects.get(obj)
        if spec is None:
            problems.append(f"{where}: object type {obj!r} is not in the portal map; run "
                            "discovery first (references/hubspot-adapter.md)")
            continue
        if spec.get("write_access") is not True:
            problems.append(f"{where}: the connected HubSpot user cannot write {obj}")
            continue
        per_object[obj] = per_object.get(obj, 0) + 1
        props = write.get("properties") or {}
        for prop, value in props.items():
            pspec = spec["properties"].get(prop)
            if pspec is None:
                problems.append(f"{where}: {prop} is not a property of {obj} in this portal")
                continue
            if pspec["owner"] == "human" and write.get("id") not in (None, ""):
                problems.append(f"{where}: {prop} is human-managed; the engine never edits it")
                continue
            problems.extend(check_value(where, prop, pspec, value))
        if write.get("id") in (None, "") and not spec.get("append_only"):
            key = spec.get("dedupe_key")
            if not key:
                problems.append(f"{where}: creating {obj} but the map names no dedupe_key, "
                                "so a duplicate cannot be ruled out")
            elif not props.get(key):
                problems.append(f"{where}: creating {obj} without its dedupe key {key}")
            for req in spec.get("required") or []:
                if not props.get(req):
                    problems.append(f"{where}: creating {obj} without required property {req}")
        for assoc in write.get("associations") or []:
            target = assoc.get("object") if isinstance(assoc, dict) else None
            if target not in objects:
                problems.append(f"{where}: association target {target!r} is not in the "
                                "portal map")
    for obj, count in sorted(per_object.items()):
        if count > BATCH_LIMIT:
            warnings.append(f"{count} writes to {obj}; manage_crm_objects takes at most "
                            f"{BATCH_LIMIT} per request, so split them")
    return problems, warnings


def main():
    """CLI entry point."""
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv[1:]
    if len(args) != 2:
        print("usage: hubspot_presync.py portal-map.json planned-writes.json [--json]",
              file=sys.stderr)
        sys.exit(2)
    docs = []
    for path in args:
        try:
            docs.append(json.loads(Path(path).read_text("utf-8")))
        except (OSError, json.JSONDecodeError) as e:
            print(f"Cannot read {path}: {e}", file=sys.stderr)
            sys.exit(2)
    problems, warnings = check(*docs)
    if as_json:
        print(json.dumps({"portal_map": args[0], "writes": args[1], "pass": not problems,
                          "problems": problems, "warnings": warnings}, indent=2))
    else:
        print(f"{'PASS' if not problems else 'BLOCKED'}: {args[1]} against {args[0]}")
        for problem in problems:
            print(f"  - {problem}")
        for warning in warnings:
            print(f"  warning: {warning}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
