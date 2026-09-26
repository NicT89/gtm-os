#!/usr/bin/env python3
"""Deterministic motion assignment, two-pass scoring and tiering for gtm-signal-scan.

Until 1.10.0 the scan's rubric lived only as prose tables in SKILL.md Step 2, and the model
did the arithmetic. Two runs over the same accounts could score them differently, and a
missing input scored as a low value rather than as a gap, because nothing distinguished
"0 points" from "not known yet". This script is the arithmetic; SKILL.md stays the doctrine.

**What is fixed here and what is per-deployment.** The DIMENSIONS below (names, which pass,
maximum points) are engine doctrine and must equal the tables in SKILL.md Step 2; the test
suite compares them. Everything that says HOW a dimension earns its points, the motion
definitions, the exclusion thresholds and the tier cutoffs are per-deployment, and live in a
scoring config file (`{SCORING_CONFIG_FILE}` in instance-config.json). This script ships
no default rules: a score is only as honest as the rules someone decided on, and a
plausible-looking default is how an invented threshold reaches a live run. The demo's
config (examples/demo/scoring.demo.json) is labeled ILLUSTRATIVE for exactly that reason.

**Unknown is not zero.** A dimension whose input is absent scores 0 AND carries an
`unknown` flag, and a motion criterion whose input is absent is unmet rather than false.
An account whose team state is unknown gets no motion, and is held with the free call that
would resolve it named, instead of being routed on a guess.

Usage:
    python3 score.py accounts.json --config scoring-config.json --as-of YYYY-MM-DD \
        [--pass 1|full]
    python3 score.py --check-config scoring-config.json

`accounts.json` is a list of normalized account objects; see ACCOUNT_FIELDS. The clock is
never read: `--as-of` is required, so a replay produces the same scores.

Exit code 0 = scored (or config valid), 1 = the config failed validation, 2 = usage error.
JSON on stdout, so the result is loggable to the audit trail verbatim.
"""
import argparse
import json
import sys
from datetime import date

# Engine doctrine: must equal SKILL.md Step 2's two tables (tests/test_score_passes.py).
DIMENSIONS = (
    ("motion_fit", 1, 15),
    ("signal_age", 1, 15),
    ("budget_signal", 1, 15),
    ("geography", 1, 10),
    ("stage_and_funding", 2, 20),
    ("archetype_fit", 2, 10),
    ("stack_overlap", 2, 10),
    ("warm_path", 2, 5),
)
PASS1_MAX = sum(m for _, p, m in DIMENSIONS if p == 1)
FULL_MAX = sum(m for _, _, m in DIMENSIONS)

TIER_NAMES = ("Excellent", "Good", "Fair")
BELOW = "Below Fair"

# The normalized, platform-neutral account shape. A CRM adapter maps its own payload into
# this; the scorer never reads a vendor field name.
ACCOUNT_FIELDS = {
    "id": "stable identifier",
    "name": "company name",
    "domain": "normalized company domain",
    "signal_type": "hiring | funding (what sourced the account; NOT the motion)",
    "signal_observed_on": "YYYY-MM-DD the signal happened, or null if unknown",
    "gtm_team_size": "int from the free people search, or null if not yet searched",
    "hiring_gtm": "bool, or null; defaults to signal_type == 'hiring'",
    "gtm_leader_tenure_months": "int, or null",
    "category": "null, or an exclusion category such as competitor / staffing_firm",
    "headcount_growth_pct": "number, or null",
    "hq_country": "ISO-ish country code, or null (absent on net-new search results)",
    "latest_funding_stage": "from org enrichment (pass 2)",
    "role_archetype": "from the JD (pass 2)",
    "technologies": "list, from org enrichment (pass 2)",
    "warm_path": "bool, from the contact set (pass 2)",
}


def parse_day(value):
    """Return a date for YYYY-MM-DD, or None. Never raises on a bad value."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def is_number(value):
    """True for real ints and floats; bools are ints in Python and are rejected."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------- config


def validate_config(config):
    """Return a list of problems with a scoring config. Empty means usable.

    Checks shape, that no rule can award more than its dimension's doctrinal maximum
    (which would silently turn a 0-100 score into something else), and that tier cutoffs
    are descending and inside their pass's range.
    """
    problems = []
    if not isinstance(config, dict):
        return ["the scoring config must be a JSON object"]

    motions = config.get("motions")
    if not isinstance(motions, list) or not motions:
        problems.append("`motions` must be a non-empty list")
        motions = []
    seen = set()
    for i, m in enumerate(motions):
        if not isinstance(m, dict) or not m.get("id"):
            problems.append(f"motions[{i}] needs an `id`")
            continue
        if m["id"] in seen:
            problems.append(f"motion id {m['id']!r} is defined twice")
        seen.add(m["id"])
        if not isinstance(m.get("criteria"), dict) or not m["criteria"]:
            problems.append(f"motion {m['id']!r} needs non-empty `criteria`")
        if not is_number(m.get("priority")):
            problems.append(f"motion {m['id']!r} needs a numeric `priority`")

    dims = config.get("dimensions")
    if not isinstance(dims, dict):
        problems.append("`dimensions` must be an object")
        dims = {}
    for name, _, cap in DIMENSIONS:
        rule = dims.get(name)
        if not isinstance(rule, dict):
            problems.append(f"dimensions.{name} is missing")
            continue
        for label, points in rule_point_values(name, rule):
            if not is_number(points) or points < 0 or points > cap:
                problems.append(f"dimensions.{name}: {label} awards {points!r}; "
                                f"the dimension's maximum is {cap}")
    motion_rule = dims.get("motion_fit")
    motion_points = motion_rule.get("points_by_motion") if isinstance(motion_rule, dict) else None
    if isinstance(motion_points, dict):
        for mid in seen - set(motion_points):
            problems.append(f"dimensions.motion_fit.points_by_motion has no entry for "
                            f"motion {mid!r}")

    for key, ceiling in (("pre_tiers", PASS1_MAX), ("tiers", FULL_MAX)):
        cut = config.get(key)
        if not isinstance(cut, dict):
            problems.append(f"`{key}` must be an object with excellent/good/fair")
            continue
        values = [cut.get(t.lower()) for t in TIER_NAMES]
        if not all(is_number(v) for v in values):
            problems.append(f"`{key}` needs numeric excellent, good and fair cutoffs")
            continue
        if not values[0] > values[1] > values[2] >= 0:
            problems.append(f"`{key}` cutoffs must descend: excellent > good > fair >= 0")
        if values[0] > ceiling:
            problems.append(f"`{key}.excellent` is {values[0]}, above the pass maximum "
                            f"of {ceiling}")
    return problems


def rule_point_values(name, rule):
    """Yield (label, points) for every point value a dimension rule can award."""
    if name in ("motion_fit", "stage_and_funding", "archetype_fit"):
        key = {"motion_fit": "points_by_motion", "stage_and_funding": "points_by_stage",
               "archetype_fit": "points_by_archetype"}[name]
        table = rule.get(key)
        if not isinstance(table, dict):
            yield f"`{key}` (missing)", None
            return
        for k, v in table.items():
            yield f"{k!r}", v
        if "default" in rule:
            yield "default", rule["default"]
    elif name == "signal_age":
        for signal, window in (rule.get("windows") or {}).items():
            if not isinstance(window, dict):
                yield f"windows.{signal} (not an object)", None
                continue
            full, zero = window.get("full_points_within_days"), window.get("zero_points_after_days")
            if not (is_number(full) and is_number(zero) and 0 <= full < zero):
                yield f"windows.{signal} (needs 0 <= full_points_within_days < zero_points_after_days)", None
        yield "full credit", dict(DIMENSIONS_BY_NAME)[name]
    elif name == "budget_signal":
        steps = rule.get("steps")
        if not isinstance(steps, list) or not steps:
            yield "`steps` (missing)", None
            return
        for step in steps:
            if not (isinstance(step, list) and len(step) == 2 and is_number(step[0])):
                yield f"step {step!r} (needs [min_value, points])", None
            else:
                yield f"step >= {step[0]}", step[1]
    elif name == "stack_overlap":
        yield "points_each", rule.get("points_each")
    elif name in ("geography", "warm_path"):
        yield "full credit", dict(DIMENSIONS_BY_NAME)[name]


DIMENSIONS_BY_NAME = tuple((n, m) for n, _, m in DIMENSIONS)


# ---------------------------------------------------------------------------- motion


def axes(account):
    """Resolve the motion axes from an account. None means unknown, never False."""
    team = account.get("gtm_team_size")
    hiring = account.get("hiring_gtm")
    if hiring is None and account.get("signal_type") in ("hiring", "funding"):
        hiring = account["signal_type"] == "hiring"
    tenure = account.get("gtm_leader_tenure_months")
    return {
        "has_gtm_team": None if not is_number(team) else team >= 1,
        "hiring_gtm": hiring if isinstance(hiring, bool) else None,
        "gtm_leader_tenure_months": tenure if is_number(tenure) else None,
    }


def criterion_met(key, expected, ax):
    """Return True, False, or None (input unknown) for one motion criterion."""
    if key == "gtm_leader_tenure_months_max":
        value = ax["gtm_leader_tenure_months"]
        return None if value is None else value <= expected
    value = ax.get(key)
    if value is None:
        return None
    return value == expected


def assign_motion(account, motions):
    """Pick the highest-priority motion whose every criterion is met.

    Returns {"motion": id or None, "axes": ..., "reason": ...}. An override (a recency
    motion that outranks a quadrant, the way a new-leader motion outranks expansion) is
    just a higher priority, so the 2x2-plus-override shape needs no special case.
    """
    ax = axes(account)
    matched, blocked_on = [], set()
    for m in motions:
        results = {k: criterion_met(k, v, ax) for k, v in m["criteria"].items()}
        if all(r is True for r in results.values()):
            matched.append(m)
        elif not any(r is False for r in results.values()):
            blocked_on.update(k for k, r in results.items() if r is None)
    if matched:
        best = max(matched, key=lambda m: (m["priority"], m["id"]))
        crit = ", ".join(f"{k}={v}" for k, v in sorted(best["criteria"].items()))
        return {"motion": best["id"], "axes": ax, "reason": f"criteria met: {crit}"}
    if blocked_on:
        return {"motion": None, "axes": ax,
                "reason": "unknown input: " + ", ".join(sorted(blocked_on))}
    return {"motion": None, "axes": ax, "reason": "no motion's criteria match"}


def exclusion(account, config):
    """Return an exclusion reason string, or None. Runs before any spend."""
    rules = config.get("exclusions") or {}
    category = account.get("category")
    if category and category in (rules.get("categories") or []):
        return f"category: {category}"
    ceiling = (rules.get("max_gtm_team") or {}).get(account.get("signal_type"))
    team = account.get("gtm_team_size")
    if is_number(ceiling) and is_number(team) and team > ceiling:
        return (f"established GTM team of {team} (this signal type excludes above "
                f"{ceiling})")
    return None


# ---------------------------------------------------------------------------- score


def score_dimension(name, rule, account, motion, as_of):
    """Return {"points", "max", "basis", "unknown"} for one dimension."""
    cap = dict(DIMENSIONS_BY_NAME)[name]
    out = {"dimension": name, "points": 0, "max": cap, "unknown": False, "basis": ""}

    def unknown(what):
        out.update(unknown=True, basis=f"unknown: {what}")
        return out

    if name == "motion_fit":
        if motion is None:
            return unknown("no motion assigned")
        pts = rule["points_by_motion"].get(motion, 0)
        out.update(points=pts, basis=f"motion {motion}")
    elif name == "signal_age":
        seen = parse_day(account.get("signal_observed_on"))
        window = (rule.get("windows") or {}).get(account.get("signal_type"))
        if seen is None:
            return unknown("signal date (never treated as fresh)")
        if not isinstance(window, dict):
            return unknown(f"no decay window for signal type {account.get('signal_type')!r}")
        age = (as_of - seen).days
        full, zero = window["full_points_within_days"], window["zero_points_after_days"]
        if age < 0:
            return unknown(f"signal dated after as-of ({age} days)")
        if age <= full:
            pts = cap
        elif age >= zero:
            pts = 0
        else:
            pts = round(cap * (zero - age) / (zero - full))
        out.update(points=pts, basis=f"{age} days old (full <= {full}, zero >= {zero})")
    elif name == "budget_signal":
        value = account.get(rule.get("field", "headcount_growth_pct"))
        if not is_number(value):
            return unknown(rule.get("field", "headcount_growth_pct"))
        pts = max([p for floor, p in rule["steps"] if value >= floor], default=0)
        out.update(points=pts, basis=f"{rule.get('field', 'headcount_growth_pct')} = {value}")
    elif name == "geography":
        country = account.get("hq_country")
        if not country:
            return unknown("HQ country (absent on net-new search results)")
        pts = cap if country in (rule.get("countries") or []) else 0
        out.update(points=pts, basis=f"HQ {country}")
    elif name in ("stage_and_funding", "archetype_fit"):
        field = "latest_funding_stage" if name == "stage_and_funding" else "role_archetype"
        key = "points_by_stage" if name == "stage_and_funding" else "points_by_archetype"
        value = account.get(field)
        if not value:
            return unknown(field)
        pts = rule[key].get(value, rule.get("default", 0))
        out.update(points=pts, basis=f"{field} = {value}")
    elif name == "stack_overlap":
        techs = account.get("technologies")
        if not isinstance(techs, list):
            return unknown("technologies")
        wanted = {t.lower() for t in rule.get("technologies") or []}
        hits = sorted(t for t in techs if isinstance(t, str) and t.lower() in wanted)
        pts = min(cap, len(hits) * rule["points_each"])
        out.update(points=pts, basis=("overlap: " + ", ".join(hits)) if hits else "no overlap")
    elif name == "warm_path":
        warm = account.get("warm_path")
        if not isinstance(warm, bool):
            return unknown("warm path (needs the contact set)")
        out.update(points=cap if warm else 0, basis="warm path" if warm else "none found")
    return out


def tier(points, cutoffs):
    """Map a score to Excellent / Good / Fair / Below Fair."""
    for name in TIER_NAMES:
        if points >= cutoffs[name.lower()]:
            return name
    return BELOW


def score_account(account, config, as_of, which="full", motion=None):
    """Score one account. `which` is "1" (free pre-score) or "full" (all eight).

    A pass-1 result is labeled `pre-score` and tiered on `pre_tiers`; it is never a final
    score. `motion` may be passed in when it was already assigned; otherwise it is assigned
    here from the config's motion definitions.
    """
    if motion is None:
        motion = assign_motion(account, config["motions"])["motion"]
    dims = [score_dimension(n, config["dimensions"][n], account, motion, as_of)
            for n, p, _ in DIMENSIONS if which == "full" or p == 1]
    total = sum(d["points"] for d in dims)
    cutoffs = config["pre_tiers"] if which == "1" else config["tiers"]
    return {
        "id": account.get("id"),
        "kind": "pre-score" if which == "1" else "score",
        "points": total,
        "out_of": PASS1_MAX if which == "1" else FULL_MAX,
        "tier": tier(total, cutoffs),
        "motion": motion,
        "dimensions": dims,
        "unknown": [d["dimension"] for d in dims if d["unknown"]],
    }


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser()
    p.add_argument("accounts", nargs="?")
    p.add_argument("--config")
    p.add_argument("--as-of", dest="as_of")
    p.add_argument("--pass", dest="which", choices=["1", "full"], default="full")
    p.add_argument("--check-config", dest="check")
    args = p.parse_args()

    path = args.check or args.config
    if not path:
        print("--config (or --check-config) is required.", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path) as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read scoring config {path}: {e}", file=sys.stderr)
        sys.exit(2)
    problems = validate_config(config)
    if args.check or problems:
        print(json.dumps({"config": path, "valid": not problems, "problems": problems},
                         indent=2))
        sys.exit(1 if problems else 0)

    as_of = parse_day(args.as_of)
    if not args.accounts or as_of is None:
        print("accounts.json and --as-of YYYY-MM-DD are required; the clock is never read.",
              file=sys.stderr)
        sys.exit(2)
    try:
        with open(args.accounts) as f:
            accounts = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read accounts: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(accounts, list):
        print("accounts.json must be a JSON list.", file=sys.stderr)
        sys.exit(2)

    results = []
    for account in accounts:
        excluded = exclusion(account, config)
        assigned = assign_motion(account, config["motions"])
        entry = {"id": account.get("id"), "excluded": excluded, "motion": assigned}
        if not excluded and assigned["motion"] is None:
            # A tier here would read as enrichment-eligible for an account whose routing
            # is not known yet. Hold it with the reason instead of scoring it.
            entry["held"] = f"no motion assigned ({assigned['reason']})"
        elif not excluded:
            entry["score"] = score_account(account, config, as_of, args.which,
                                           assigned["motion"])
        results.append(entry)
    print(json.dumps({"as_of": args.as_of, "pass": args.which, "results": results},
                     indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
