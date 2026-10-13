#!/usr/bin/env python3
"""Check the SHAPE of a plays file. Never its content.

This is the repo's rule for fields that differ between organizations, applied to plays:
**universal things are deterministic, organization-specific things are guided.** A play's
entry criteria, persona and angle are free text, because plays differ completely from one
company to the next; what belongs in each is defined by guidance (description, examples,
a good-vs-weak bar) in references/play-fields.md, and the model applies it. What IS the same
everywhere gets checked here, by code:

- the file parses, has a provenance, and has at least one play;
- every play has an id, a unique code, a label, a numeric priority, a persona, and entry
  criteria written as a sentence rather than a keyword (a keyword like "hiring" is the
  failure the guidance exists to prevent; a word-count floor is how a shape check can see it);
- `exclusive_with` names plays that exist;
- Apollo list and sequence names follow the naming rule: the play's code at the front in
  parentheses. A name without "[Claude]" is allowed but warned about: it marks an asset a
  human created, which a play may route to but which play-builder never creates or edits
  (CLAUDE.md, convention 4). Found by running this checker on a real deployment's plays,
  whose live account list predates the plugin and is human-managed;
- `fields.standard` names real Apollo field keys from instance-config.example.json, so a
  typo cannot claim a field that setup never creates.

It does not decide whether the criteria are GOOD. That is the model's job against the
guidance, and the operator's at review.

Usage:
    python3 check_plays.py plays.json

Exit code 0 = valid (warnings allowed), 1 = shape problems, 2 = usage error.
JSON on stdout.
"""
import json
import re
import sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[3] / "instance-config.example.json"
PROVENANCE = ("illustrative", "deployment")
MIN_CRITERIA_WORDS = 8  # a shape floor, not a content rule: "hiring" is not a criterion
APOLLO_NAMES = ("account_list", "contact_list", "sequence")
OBJECTS = ("account", "contact")


def apollo_field_keys():
    """The Apollo custom-field keys the instance schema defines."""
    try:
        schema = json.loads(SCHEMA.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return {k for k in schema if k.startswith("APOLLO_CF_")}


def nonempty(value):
    """A non-blank string."""
    return isinstance(value, str) and value.strip() != ""


def check(doc, field_keys=None):
    """Return (problems, warnings). Pure, so every rule is directly testable."""
    problems, warnings = [], []
    if not isinstance(doc, dict):
        return ["the plays file must be a JSON object"], []
    if doc.get("provenance") not in PROVENANCE:
        problems.append(f"`provenance` must be one of {', '.join(PROVENANCE)}")
    elif doc["provenance"] == "illustrative":
        warnings.append("provenance is 'illustrative': these plays are placeholders, not decisions")
    plays = doc.get("plays")
    if not isinstance(plays, list) or not plays:
        return problems + ["`plays` must be a non-empty list"], warnings

    ids, codes = set(), set()
    for i, play in enumerate(plays):
        where = f"plays[{i}]"
        if not isinstance(play, dict):
            problems.append(f"{where} is not an object")
            continue
        pid = play.get("id")
        if not nonempty(pid) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pid):
            problems.append(f"{where}: `id` must be a lowercase slug")
        else:
            where = f"play {pid!r}"
            if pid in ids:
                problems.append(f"{where} is defined twice")
            ids.add(pid)
        code = play.get("code")
        if not nonempty(code):
            problems.append(f"{where}: `code` is required; it prefixes every Apollo object the play owns")
        elif code in codes:
            problems.append(f"{where}: code {code!r} is used by another play")
        else:
            codes.add(code)
        for key in ("label", "persona"):
            if not nonempty(play.get(key)):
                problems.append(f"{where}: `{key}` is required")
        if isinstance(play.get("priority"), bool) or not isinstance(play.get("priority"), (int, float)):
            problems.append(f"{where}: `priority` must be a number (it breaks ties and lets an override outrank)")
        criteria = play.get("entry_criteria")
        if not nonempty(criteria):
            problems.append(f"{where}: `entry_criteria` is required")
        elif len(criteria.split()) < MIN_CRITERIA_WORDS:
            problems.append(f"{where}: `entry_criteria` reads as a keyword, not a criterion; "
                            "write the situation in a sentence (see references/play-fields.md)")

        apollo = play.get("apollo") if isinstance(play.get("apollo"), dict) else {}
        for key in APOLLO_NAMES:
            name = apollo.get(key, "")
            if not nonempty(name):
                warnings.append(f"{where}: no Apollo {key.replace('_', ' ')} named yet")
                continue
            if nonempty(code) and not name.startswith(f"({code})"):
                problems.append(f"{where}: {key} {name!r} must start with ({code})")
            if "[Claude]" not in name:
                warnings.append(f"{where}: {key} {name!r} has no [Claude], so it is treated as "
                                "human-managed: play-builder will route to it but never create "
                                "or edit it")

        fields = play.get("fields") if isinstance(play.get("fields"), dict) else {}
        for key in fields.get("standard", []) or []:
            if field_keys is not None and key not in field_keys:
                problems.append(f"{where}: standard field {key!r} is not an Apollo key in "
                                "instance-config.example.json")
        for j, custom in enumerate(fields.get("custom", []) or []):
            if not isinstance(custom, dict):
                problems.append(f"{where}: fields.custom[{j}] is not an object")
                continue
            for key in ("label", "type", "purpose"):
                if not nonempty(custom.get(key)):
                    problems.append(f"{where}: fields.custom[{j}] needs `{key}`")
            if custom.get("object") not in OBJECTS:
                problems.append(f"{where}: fields.custom[{j}].object must be account or contact")

    for play in plays:
        if not isinstance(play, dict):
            continue
        for other in play.get("exclusive_with", []) or []:
            if other == play.get("id"):
                problems.append(f"play {play.get('id')!r} lists itself in exclusive_with")
            elif other not in ids:
                problems.append(f"play {play.get('id')!r}: exclusive_with names unknown play {other!r}")
    return problems, warnings


def main():
    """CLI entry point."""
    if len(sys.argv) != 2:
        print("usage: check_plays.py plays.json", file=sys.stderr)
        sys.exit(2)
    try:
        doc = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read plays file: {e}", file=sys.stderr)
        sys.exit(2)
    problems, warnings = check(doc, apollo_field_keys())
    print(json.dumps({"file": sys.argv[1], "valid": not problems, "problems": problems,
                      "warnings": warnings}, indent=2))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
