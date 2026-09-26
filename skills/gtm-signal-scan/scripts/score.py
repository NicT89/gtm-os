#!/usr/bin/env python3
"""Deterministic two-pass scoring and tiering for gtm-signal-scan.

Until 1.10.0 the scan's rubric lived only as prose tables in SKILL.md Step 2, and the model
did the arithmetic. Two runs over the same accounts could score them differently, and a
missing input scored as a low value rather than as a gap, because nothing distinguished
"0 points" from "not known yet". This script is the arithmetic; SKILL.md stays the doctrine.

**What is fixed here and what is per-deployment.** The DIMENSIONS below (names, which pass,
maximum points) are engine doctrine and must equal the tables in SKILL.md Step 2; the test
suite compares them. Everything that says HOW a dimension earns its points, the exclusion
thresholds and the tier cutoffs are per-deployment, and live in a
scoring config file (`{SCORING_CONFIG_FILE}` in instance-config.json). This script ships
no default rules: a score is only as honest as the rules someone decided on, and a
plausible-looking default is how an invented threshold reaches a live run. The demo's
config (examples/demo/scoring.demo.json) is labeled ILLUSTRATIVE for exactly that reason.

**Unknown is not zero.** A dimension whose input is absent scores 0 AND carries an
`unknown` flag, so a gap is visible instead of reading as a weak account.

**Play assignment is not done here, on purpose.** Which play an account belongs to is judged
by the model against each play's free-form entry criteria (references/plays.md): plays
differ completely between organizations, so they are guided rather than enumerated, and a
fixed criteria vocabulary here would force every company onto one company's axes. This
script takes the assigned play as an input (`account["play"]`) and does the deterministic
part only: `play_fit` points for it, and a hold for an account that has none.

Usage:
    python3 score.py accounts.json --config scoring-config.json --as-of YYYY-MM-DD \
        [--pass 1|full]
    python3 score.py --check-config scoring-config.json [--plays plays.json]

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
    ("play_fit", 1, 15),
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
    "signal_type": "hiring | funding (what sourced the account; NOT the play or GTM motion)",
    "play": "the play id the model assigned from the plays file, or null if held",
    "signal_observed_on": "YYYY-MM-DD the signal happened, or null if unknown",
    "gtm_team_size": "int from the free people search, or null if not yet searched",
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


def validate_config(config, play_ids=None):
    """Return a list of problems with a scoring config. Empty means usable.

    Checks shape, that no rule can award more than its dimension's doctrinal maximum
    (which would silently turn a 0-100 score into something else), and that tier cutoffs
    are descending and inside their pass's range. With `play_ids` (from the plays file), it
    also checks that every play earns an explicit play_fit value, so a new play cannot
    silently score 0.
    """
    problems = []
    if not isinstance(config, dict):
        return ["the scoring config must be a JSON object"]

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
    play_rule = dims.get("play_fit")
    play_points = play_rule.get("points_by_play") if isinstance(play_rule, dict) else None
    if isinstance(play_points, dict) and play_ids is not None:
        for pid in sorted(set(play_ids) - set(play_points)):
            problems.append(f"dimensions.play_fit.points_by_play has no entry for play {pid!r}")

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
    if name in ("play_fit", "stage_and_funding", "archetype_fit"):
        key = {"play_fit": "points_by_play", "stage_and_funding": "points_by_stage",
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


# ---------------------------------------------------------------------------- exclusion


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


def score_dimension(name, rule, account, play, as_of):
    """Return {"points", "max", "basis", "unknown"} for one dimension."""
    cap = dict(DIMENSIONS_BY_NAME)[name]
    out = {"dimension": name, "points": 0, "max": cap, "unknown": False, "basis": ""}

    def unknown(what):
        out.update(unknown=True, basis=f"unknown: {what}")
        return out

    if name == "play_fit":
        if not play:
            return unknown("no play assigned")
        pts = rule["points_by_play"].get(play, 0)
        out.update(points=pts, basis=f"play {play}")
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


def score_account(account, config, as_of, which="full"):
    """Score one account. `which` is "1" (free pre-score) or "full" (all eight).

    A pass-1 result is labeled `pre-score` and tiered on `pre_tiers`; it is never a final
    score. The play comes from `account["play"]`, assigned before scoring.
    """
    play = account.get("play")
    dims = [score_dimension(n, config["dimensions"][n], account, play, as_of)
            for n, p, _ in DIMENSIONS if which == "full" or p == 1]
    total = sum(d["points"] for d in dims)
    cutoffs = config["pre_tiers"] if which == "1" else config["tiers"]
    return {
        "id": account.get("id"),
        "kind": "pre-score" if which == "1" else "score",
        "points": total,
        "out_of": PASS1_MAX if which == "1" else FULL_MAX,
        "tier": tier(total, cutoffs),
        "play": play,
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
    p.add_argument("--plays", help="The plays file; checks every play has play_fit points.")
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
    play_ids = None
    if args.plays:
        try:
            with open(args.plays) as f:
                play_ids = [pl.get("id") for pl in json.load(f).get("plays", [])
                            if isinstance(pl, dict)]
        except (OSError, json.JSONDecodeError, AttributeError) as e:
            print(f"Cannot read plays file {args.plays}: {e}", file=sys.stderr)
            sys.exit(2)
    problems = validate_config(config, play_ids)
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
        entry = {"id": account.get("id"), "excluded": excluded, "play": account.get("play")}
        if not excluded and not account.get("play"):
            # A tier here would read as enrichment-eligible for an account whose routing
            # is not known yet. Hold it instead of scoring it.
            entry["held"] = "no play assigned; assign one against the plays file first"
        elif not excluded:
            entry["score"] = score_account(account, config, as_of, args.which)
        results.append(entry)
    print(json.dumps({"as_of": args.as_of, "pass": args.which, "results": results},
                     indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
