#!/usr/bin/env python3
"""Rank people on role fit x reachability BEFORE any match credit is spent (Step 4b).

The rule is "search is free, reveals are not": people search returns the email-status and
phone flags without charging, so the whole field can be ranked before a credit moves. This
script is that ranking, so it is the same every run.

It does NOT carry its own copy of the reachability tiers. It parses them out of the plugin
root's references/apollo-credit-costs.md at run time, because a restated tier table is how
`unverified` once went missing from T4 and every unverified candidate bought a match credit
to learn the address was never sendable. Change the table there and this follows.

Role priority, the title terms, the size bands and the T3 spend threshold are per-deployment
and come from the `people` section of the scoring config (see score.py). One rule is engine
doctrine and lives here: a `Founding <commercial role>` title is a GTM individual
contributor, never a founder (SKILL.md Step 4b, observed on a live run).

Usage:
    python3 rank_people.py people.json --config scoring-config.json \
        --tier Excellent --employees 48 [--costs path/to/apollo-credit-costs.md]

Exit code 0 = ranked, 1 = the reachability table could not be parsed, 2 = usage error.
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_COSTS = Path(__file__).resolve().parents[3] / "references" / "apollo-credit-costs.md"


def parse_reachability(text):
    """Parse the Reachability tiers table into a list of tier dicts.

    Each row becomes {"tier", "flags", "needs_phone", "absent", "multiplier", "spend"},
    where spend is "yes", "conditional" or "no". Raises ValueError when the section or a
    usable row is missing, so a renamed heading fails loudly instead of ranking everyone T4.
    """
    start = text.find("## Reachability tiers")
    if start < 0:
        raise ValueError("no '## Reachability tiers' section")
    section = text[start:]
    nxt = section.find("\n## ", 3)
    section = section if nxt < 0 else section[:nxt]
    tiers = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not re.fullmatch(r"T\d", cells[1]):
            continue
        flag_cell, name, mult, spend = cells
        try:
            multiplier = float(mult)
        except ValueError:
            raise ValueError(f"multiplier {mult!r} for {name} is not a number")
        s = spend.lower()
        tiers.append({
            "tier": name,
            "flags": re.findall(r"`([a-z_]+)`", flag_cell),
            "needs_phone": "phone" in flag_cell.lower(),
            "absent": "absent" in flag_cell.lower(),
            "multiplier": multiplier,
            "spend": "yes" if s.startswith("yes") else "no" if s.startswith("no") else "conditional",
        })
    if not tiers:
        raise ValueError("the Reachability tiers table has no parseable rows")
    return tiers


def reachability(person, tiers):
    """Return the tier dict for one person. An unrecognized flag fails closed to the
    lowest tier, because an unknown status is not evidence the mailbox exists."""
    status = person.get("email_status")
    phone = person.get("phone_available") is True
    for t in tiers:
        if status is None and t["absent"]:
            return t
        if status in t["flags"] and (phone or not t["needs_phone"]):
            return t
    return min(tiers, key=lambda t: t["multiplier"])


def words(title):
    """Lowercased title for word-boundary matching."""
    return " " + re.sub(r"[^a-z0-9]+", " ", (title or "").lower()) + " "


def role_fit(title, people_cfg):
    """Return (rank or None, weight, basis). None means: not a selection target."""
    t = words(title)
    for term in people_cfg.get("skip_terms", []):
        if f" {term} " in t:
            return None, 0.0, f"skipped: '{term}' is not a selection target"
    ranks = people_cfg.get("role_priority", [])
    if t.startswith(" founding ") and ranks:
        # Engine doctrine, not config: the provider reads "Founding" as founder seniority.
        lowest = max(ranks, key=lambda r: r["rank"])
        return lowest["rank"], lowest["weight"], "Founding <role>: GTM individual contributor, not a founder"
    for r in sorted(ranks, key=lambda r: r["rank"]):
        for term in r["title_terms"]:
            if f" {term} " in t:
                return r["rank"], r["weight"], f"priority {r['rank']} ('{term}')"
    return None, 0.0, "skipped: not in the selection priority"


def quota(account_tier, employees, people_cfg):
    """How many people this account gets. Fair and below get none (account record only)."""
    if account_tier == "Good":
        return people_cfg["good_tier_max"]
    if account_tier != "Excellent":
        return 0
    for ceiling, n in people_cfg["size_bands"]:
        if ceiling is None or (isinstance(employees, (int, float)) and employees <= ceiling):
            return n
    return 0


def rank(people, account_tier, employees, people_cfg, tiers):
    """Rank one account's candidates and decide who gets a match credit.

    Returns {"quota", "selected", "shortfall", "people": [...]}; every person carries a
    decision and a reason. A shortfall is taken rather than filled from T4.
    """
    n = quota(account_tier, employees, people_cfg)
    rows = []
    for person in people:
        r, weight, basis = role_fit(person.get("title"), people_cfg)
        t = reachability(person, tiers)
        row = {"name": person.get("name"), "title": person.get("title"),
               "email_status": person.get("email_status"), "tier": t["tier"],
               "multiplier": t["multiplier"], "rank": r, "role_basis": basis,
               "score": round(weight * t["multiplier"], 4), "decision": None, "reason": ""}
        if r is None:
            row.update(decision="skip", reason=basis)
        elif t["spend"] == "no":
            row.update(decision="hold", reason=f"{t['tier']}: no match credit; LinkedIn-only or referral path")
        elif t["spend"] == "conditional" and r > people_cfg.get("t3_max_rank", 1):
            row.update(decision="hold", reason=f"{t['tier']}: role fit below the T3 spend threshold")
        rows.append(row)

    eligible = sorted((x for x in rows if x["decision"] is None),
                      key=lambda x: (-x["score"], x["rank"], x["name"] or ""))
    for i, x in enumerate(eligible):
        if i < n:
            x.update(decision="match", reason=f"ranked {i + 1} of quota {n}")
        else:
            x.update(decision="hold", reason=f"outside the quota of {n}")
    selected = sum(1 for x in rows if x["decision"] == "match")
    order = {"match": 0, "hold": 1, "skip": 2}
    rows.sort(key=lambda x: (order[x["decision"]], -x["score"], x["name"] or ""))
    return {"quota": n, "selected": selected, "shortfall": max(0, n - selected), "people": rows}


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser()
    p.add_argument("people")
    p.add_argument("--config", required=True)
    p.add_argument("--tier", required=True, choices=["Excellent", "Good", "Fair", "Below Fair"])
    p.add_argument("--employees", type=float)
    p.add_argument("--costs", default=str(DEFAULT_COSTS))
    args = p.parse_args()
    try:
        people = json.loads(Path(args.people).read_text("utf-8"))
        config = json.loads(Path(args.config).read_text("utf-8"))
        costs = Path(args.costs).read_text("utf-8")
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read input: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(config.get("people"), dict):
        print("The scoring config has no `people` section.", file=sys.stderr)
        sys.exit(2)
    try:
        tiers = parse_reachability(costs)
    except ValueError as e:
        print(f"Cannot parse the reachability table: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(rank(people, args.tier, args.employees, config["people"], tiers), indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
