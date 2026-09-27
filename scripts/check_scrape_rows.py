#!/usr/bin/env python3
"""Check scraped rows from the GTM MCP against the Airtable posts-base schema, 1:1.

The GTM MCP runs the scrape; the customer's own Airtable connector does the write
(references/scrape-delivery.md). Between the two, this is the gate: a row that does not
match the base exactly is caught here, before a write that Airtable might accept and
mangle.

The schema is read at run time from references/airtable-posts-base.md, the same way
rank_people.py reads the reachability tiers, so there is one schema and no copy of it to
drift. The rows are the evidence; the schema doc is the rule they are checked against.

Checks, per row:
  1. the table is one the posts base defines;
  2. every field is a field of that table (no invented columns);
  3. no link field: the service cannot know the customer's record ids, so links are
     filled by the plugin after it finds or creates the parent row;
  4. the table's dedupe key fields are present and non-empty;
  5. single selects use a declared option; dates are bare YYYY-MM-DD; integers are
     integers; URLs are http(s).

Usage:
    python3 check_scrape_rows.py delivery.json [--json]

delivery.json: {"deliveries": [{"table": "Person Post", "rows": [{...}, ...]}, ...]}

Exit code 0 = every row matches, 1 = problems, 2 = usage error. Prose by default; --json
for machines.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

SCHEMA_DOC = Path(__file__).resolve().parents[1] / "references" / "airtable-posts-base.md"


def load_schema(text=None):
    """{table: {field: {"type", "purpose", "options", "dedupe"}}} from the schema doc."""
    text = SCHEMA_DOC.read_text("utf-8") if text is None else text
    body = text.split("\n## Tables", 1)[1].split("\n## ", 1)[0]
    tables = {}
    for chunk in re.split(r"\n### \d+\. ", body)[1:]:
        name = chunk.splitlines()[0].strip()
        fields = {}
        for line in chunk.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 3 or cells[0] in ("Field", "") or set(cells[0]) <= {"-"}:
                continue
            field, ftype, purpose = cells
            options = []
            if ftype.startswith("Single select"):
                options = re.findall(r"`([^`]+)`", purpose)
            fields[field] = {"type": ftype, "purpose": purpose, "options": options,
                             "dedupe": "dedupe key" in purpose.lower()}
        tables[name] = fields
    return tables


def check(delivery, schema):
    """Return problems. Pure, so every rule is directly testable."""
    batches = delivery.get("deliveries") if isinstance(delivery, dict) else None
    if not isinstance(batches, list):
        return ["the delivery must be an object with a `deliveries` list"]
    problems = []
    for b, batch in enumerate(batches):
        if not isinstance(batch, dict):
            problems.append(f"deliveries[{b}] is not an object")
            continue
        table, rows = batch.get("table"), batch.get("rows")
        fields = schema.get(table) if isinstance(table, str) else None
        if fields is None:
            problems.append(f"deliveries[{b}]: {table!r} is not a posts-base table "
                            f"({', '.join(schema)})")
            continue
        if not isinstance(rows, list):
            problems.append(f"deliveries[{b}]: `rows` must be a list")
            continue
        dedupe = [f for f, spec in fields.items() if spec["dedupe"]]
        for r, row in enumerate(rows):
            where = f"{table} row {r}"
            if not isinstance(row, dict):
                problems.append(f"{where} is not an object")
                continue
            for key in dedupe:
                if row.get(key) in (None, ""):
                    problems.append(f"{where}: dedupe key {key!r} is missing")
            for field, value in row.items():
                spec = fields.get(field)
                if spec is None:
                    problems.append(f"{where}: {field!r} is not a field of {table}")
                    continue
                kind = spec["type"]
                if kind.startswith("Link to"):
                    problems.append(f"{where}: {field!r} is a link; the plugin fills links "
                                    "after it finds the parent row")
                elif value is None:
                    continue
                elif kind.startswith("Single select") and spec["options"] \
                        and value not in spec["options"]:
                    problems.append(f"{where}: {field}={value!r} is not an option "
                                    f"({', '.join(spec['options'])})")
                elif kind == "Date" and not bare_date(value):
                    problems.append(f"{where}: {field}={value!r} is not a bare YYYY-MM-DD date")
                elif kind.startswith("Number (integer)") and (
                        not isinstance(value, int) or isinstance(value, bool)):
                    problems.append(f"{where}: {field}={value!r} is not an integer")
                elif kind.startswith(("Single line text", "Long text")) \
                        and not isinstance(value, str):
                    problems.append(f"{where}: {field} must be text, not "
                                    f"{type(value).__name__}")
                elif kind == "URL" and not str(value).startswith(("http://", "https://")):
                    problems.append(f"{where}: {field}={value!r} is not an http(s) URL")
    return problems


def bare_date(value):
    """True for a YYYY-MM-DD string and nothing else."""
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def main():
    """CLI entry point."""
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv[1:]
    if len(args) != 1:
        print("usage: check_scrape_rows.py delivery.json [--json]", file=sys.stderr)
        sys.exit(2)
    try:
        delivery = json.loads(Path(args[0]).read_text("utf-8"))
        schema = load_schema()
    except (OSError, json.JSONDecodeError, IndexError) as e:
        print(f"Cannot read input: {e}", file=sys.stderr)
        sys.exit(2)
    problems = check(delivery, schema)
    if as_json:
        print(json.dumps({"file": args[0], "valid": not problems, "problems": problems},
                         indent=2))
    else:
        print(f"{'VALID' if not problems else 'INVALID'}: {args[0]}")
        for problem in problems:
            print(f"  - {problem}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
