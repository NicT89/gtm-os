#!/usr/bin/env python3
"""The offline demo: the engine's real decision logic over synthetic accounts.

No connector is called, no credit is spent, nothing is written anywhere but the output
folder, and nothing is sent. What runs is the same code a live scan runs: exclusions and
two-pass scoring (score.py), reachability ranking (rank_people.py, which
reads the tiers out of references/apollo-credit-costs.md), the credit arithmetic from that
same file, the field completeness gate (field_gate.py) and the run-cost tally
(run_cost.py). The inputs a live run would get from Apollo, enrichment and composition are
FIXTURES in examples/demo/fixtures.json, and the report labels them as such.

Two modes:

  default          Synthetic accounts, ILLUSTRATIVE demo scoring parameters. Every row is
                   labeled SIMULATED or FIXTURE. This is the "see it think" run.
  --config PATH    The same synthetic accounts through YOUR instance: your
                   instance-config.json is validated, your scoring config (named by its
                   SCORING_CONFIG_FILE key) drives exclusions, scoring and tiers, your
                   plays file (PLAYS_FILE) is shape-checked,
                   and every gap found becomes a finding. Rows are labeled PREVIEW. Still
                   no API calls: this checks the shape of your setup, not connectivity.

The four labels are defined in references/run-manifest.md, not restated here.

Usage:
    python3 scripts/demo.py [--config instance-config.json] [--out DIR] [--stdout]

Writes DIR/report.md and DIR/run-shape.json (DIR defaults to ./gtm-os-demo). The clock is
never read: the as-of date comes from the fixtures, so two runs produce identical bytes and
examples/demo-report.md can be checked against the generator.

Exit code 0 = demo ran, 1 = ran with blocking findings (config mode), 2 = usage error.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("scripts", "skills/gtm-signal-scan/scripts", "skills/gtm-blueprint/scripts",
            "skills/play-builder/scripts"):
    sys.path.insert(0, str(ROOT / sub))

import check_plays  # noqa: E402
import field_gate  # noqa: E402
import rank_people  # noqa: E402
import run_cost  # noqa: E402
import score  # noqa: E402
import setup_status  # noqa: E402
import validate_instance_config  # noqa: E402

FIXTURES = ROOT / "examples" / "demo" / "fixtures.json"
DEMO_SCORING = ROOT / "examples" / "demo" / "scoring.demo.json"
DEMO_PLAYS = ROOT / "examples" / "demo" / "plays.demo.json"
COSTS = ROOT / "references" / "apollo-credit-costs.md"
LABELS = ("SIMULATED", "FIXTURE", "PREVIEW", "LIVE")

# Waterfall precedence when one account carries two signals: postings before funding,
# per references/signals-doctrine.md ("2/3 postings by age, then 1 funding").
SIGNAL_PRECEDENCE = {"hiring": 0, "funding": 1}


def load(path):
    """Read a JSON file."""
    return json.loads(Path(path).read_text("utf-8"))


def normalize_domain(value):
    """Lowercase, drop scheme, path and a leading www. Empty stays empty."""
    d = (value or "").strip().lower()
    d = re.sub(r"^[a-z]+://", "", d).split("/")[0]
    return d[4:] if d.startswith("www.") else d


# ------------------------------------------------------------------------ credit costs


def credit_costs(text):
    """Per-unit costs parsed from the cost table in apollo-credit-costs.md.

    Read at run time so the estimate follows the reference when it changes. A cell that
    reads Free is 0; a leading integer is the cost. Raises ValueError on a missing row,
    because an estimate silently missing a line item under-states the ask.
    """
    wanted = {"company_search": "company search", "org_enrichment": "organization enrichment",
              "job_postings": "job postings", "people_match": "people enrichment"}
    costs = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        action = cells[0].lower()
        for key, prefix in wanted.items():
            if action.startswith(prefix) and key not in costs:
                if "free" in cells[1].lower():
                    costs[key] = 0
                else:
                    m = re.match(r"\D*(\d+)", cells[1])
                    if m:
                        costs[key] = int(m.group(1))
    missing = sorted(set(wanted) - set(costs))
    if missing:
        raise ValueError(f"cost table has no row for: {', '.join(missing)}")
    return costs


# ---------------------------------------------------------------------------- stages


def intake(response):
    """Dedupe the search response. Returns (accounts, rejected, source_count).

    The response's `accounts` array is already in the CRM (update, never create); its
    `organizations` array is net new. A domain seen twice becomes one account with both
    signals kept, and the higher-precedence signal becomes the account's signal type.
    """
    merged, rejected, count = {}, [], 0
    for in_crm, rows in ((True, response.get("accounts", [])),
                         (False, response.get("organizations", []))):
        for row in rows:
            count += 1
            domain = normalize_domain(row.get("domain"))
            if not domain:
                rejected.append({"name": row.get("name") or row.get("id"),
                                 "reason": "no domain: identity cannot be resolved"})
                continue
            signal = {"type": row.get("signal_type"), "observed_on": row.get("signal_observed_on")}
            if domain in merged:
                acct = merged[domain]
                acct["signals"].append(signal)
                acct["in_crm"] = acct["in_crm"] or in_crm
                continue
            acct = dict(row, domain=domain, in_crm=in_crm, signals=[signal])
            merged[domain] = acct
    accounts = []
    for acct in merged.values():
        acct["signals"].sort(key=lambda s: SIGNAL_PRECEDENCE.get(s["type"], 9))
        primary = acct["signals"][0]
        acct["signal_type"], acct["signal_observed_on"] = primary["type"], primary["observed_on"]
        accounts.append(acct)
    return accounts, rejected, count


def number_tokens(text):
    """Numbers as written: 2026-08-25, 40, 2.5, 30%. Used to trace each to a source."""
    return re.findall(r"\d[\d,.\-/%]*\d|\d", text)


def composition_checks(opener):
    """The deterministic half of outreach-audit's rules. Returns a list of failures.

    1. No bare {{Field Name}} token: without the contact./account. prefix it renders as
       literal text (outreach-audit, merge token rules).
    2. Every number in the copy appears in a named source (CLAUDE.md: a number with no
       source is invented). Necessary, not sufficient: a human still reads the facts.
    """
    failures = []
    for token in re.findall(r"\{\{\s*([^}]+?)\s*\}\}", opener["text"]):
        if not token.startswith(("contact.", "account.")):
            failures.append(f"bare merge token {{{{{token}}}}} renders as literal text")
    sources = " ".join(opener.get("facts", []))
    for n in number_tokens(opener["text"]):
        if n not in sources:
            failures.append(f"the number '{n}' appears in no named source")
    return failures


def run_pipeline(fx, config, plays, costs, reach_tiers, row_label):
    """Run every stage over the fixtures. Pure: returns a result dict, writes nothing."""
    as_of = date.fromisoformat(fx["run"]["as_of_date"])
    accounts, rejected, source_count = intake(fx["search_response"])
    play_index = {pl["id"]: pl for pl in plays["plays"]}

    # Stage 2a: exclusions, deterministic, off the free people search.
    # Stage 2b: play assignment. In a live run the model judges each play's free-form entry
    # criteria against the evidence (references/plays.md); here that judgment is a FIXTURE.
    # What stays deterministic is checked: the play must exist, and none means a hold.
    routed, excluded, unassigned = [], [], []
    for a in accounts:
        reason = score.exclusion(a, config)
        if reason:
            excluded.append((a, reason))
            continue
        assigned = dict(fx["play_assignments"].get(a["domain"]) or
                        {"play": None, "reasoning": "no assignment recorded", "evidence": ""})
        if assigned.get("play") and assigned["play"] not in play_index:
            assigned.update(reasoning=f"assigned play {assigned['play']!r} is not in the plays file",
                            play=None)
        a["_assign"], a["play"] = assigned, assigned.get("play")
        (routed if a["play"] else unassigned).append(a)

    # Stage 3: the free pre-score decides who is worth enriching.
    for a in routed:
        a["_pre"] = score.score_account(a, config, as_of, "1")
    to_enrich = [a for a in routed if a["_pre"]["tier"] in ("Excellent", "Good")]
    record_only = [a for a in routed if a["_pre"]["tier"] == "Fair"]
    below = [a for a in routed if a["_pre"]["tier"] == score.BELOW]

    # Stage 4: the credit statement, made BEFORE any spend. People matches are capped at
    # the quota each account could draw at its pre-score tier; ranking later spends less.
    hiring_enriched = [a for a in to_enrich if a["signal_type"] == "hiring"]
    people_cap = sum(rank_people.quota(a["_pre"]["tier"], a.get("employees"), config["people"])
                     for a in to_enrich)
    estimate = [
        ("Company search", 1, costs["company_search"]),
        ("Organization enrichment (pre-score Excellent + Good)", len(to_enrich), costs["org_enrichment"]),
        ("Job postings (hiring accounts being enriched)", len(hiring_enriched), costs["job_postings"]),
        ("People match (quota cap at pre-score tier)", people_cap, costs["people_match"]),
    ]
    planned = sum(n * c for _, n, c in estimate)

    # Stage 5: enrichment (FIXTURE values) and the full score.
    for a in to_enrich:
        a.update({k: v for k, v in fx["enrichment"].get(a["domain"], {}).items()})
        a["_full"] = score.score_account(a, config, as_of, "full")

    # Stage 6: people ranking at accounts whose FULL tier warrants people spend.
    policy = (config.get("catch_all_policy") or {}).get("decision", "unset")
    people_rows = []
    for a in to_enrich:
        tier = a["_full"]["tier"]
        if tier not in ("Excellent", "Good"):
            continue
        ranked = rank_people.rank(fx["people"].get(a["domain"], []), tier, a.get("employees"),
                                  config["people"], reach_tiers)
        a["_people"] = ranked
        for p in ranked["people"]:
            p["account"], p["account_tier"], p["domain"] = a["name"], tier, a["domain"]
            p["signal_type"] = a["signal_type"]
            if p["decision"] == "match" and p["email_status"] == "catch_all":
                if policy == "enroll":
                    p["post"] = "send-risk: catch-all, enrolled under the recorded policy"
                elif policy == "exclude":
                    p["post"] = "held: catch-all excluded by the recorded policy; LinkedIn path"
                else:
                    p["post"] = "held: catch-all enrollment gate (no policy recorded)"
            people_rows.append(p)
    matched = [p for p in people_rows if p["decision"] == "match"]
    would_spend = (costs["company_search"] + len(to_enrich) * costs["org_enrichment"]
                   + len(hiring_enriched) * costs["job_postings"]
                   + len(matched) * costs["people_match"])

    # Stage 7: the field gate on Excellent contacts (the only tier that gets composition).
    gate_rows = []
    for p in matched:
        if p["account_tier"] != "Excellent":
            continue
        acct = fx["account_records"].get(p["domain"], {})
        record = {"name": p["name"], "organization_name": p["account"],
                  "typed_custom_fields": fx["contact_fields"].get(p["name"], {}),
                  "organization": dict(acct.get("system", {}),
                                       typed_custom_fields=acct.get("typed_custom_fields", {}))}
        verdict = field_gate.run_gate(record, fx["gate_config"], p["signal_type"])
        p["gate"] = verdict
        gate_rows.append(p)

    # Stage 8: composition checks on FIXTURE openers for contacts the gate passed.
    comp_rows = []
    for p in gate_rows:
        if p["gate"]["gate"] != "PASS" or p.get("post", "").startswith("held"):
            continue
        opener = fx["openers"].get(p["name"])
        p["opener"] = opener
        p["composition"] = (["no opener fixture"] if opener is None
                            else composition_checks(opener))
        comp_rows.append(p)

    # Stage 9: the pre-send queue. Nothing here is sent; enrollment is a human gate.
    queue, held = [], []
    for p in people_rows:
        if p["decision"] != "match":
            continue
        if p.get("post", "").startswith("held"):
            held.append((p, p["post"]))
        elif p["account_tier"] == "Good":
            queue.append((p, "ready for pre-send review; Good tier composes no personalization fields"))
        elif p["gate"]["gate"] != "PASS":
            held.append((p, "held: field gate FAIL, " + "; ".join(p["gate"]["missing_required"])))
        elif p["composition"]:
            held.append((p, "held: composition check, " + "; ".join(p["composition"])))
        else:
            queue.append((p, "ready for pre-send review"))

    tally_problems, tally = run_cost.tally({
        "run_id": fx["run"]["run_id"],
        "meters": {"apollo": {"spent": 0, "cap": planned, "unit": "credits"}},
        "complete": True, "fields_filled": 0, "fields_proposed": 0})

    return {
        "as_of": fx["run"]["as_of_date"], "run_id": fx["run"]["run_id"], "label": row_label,
        "source_count": source_count, "accounts": accounts, "rejected": rejected,
        "excluded": excluded, "unassigned": unassigned, "routed": routed,
        "to_enrich": to_enrich, "record_only": record_only, "below": below,
        "estimate": estimate, "planned": planned, "would_spend": would_spend,
        "people_rows": people_rows, "matched": matched, "gate_rows": gate_rows,
        "comp_rows": comp_rows, "queue": queue, "held": held, "policy": policy,
        "plays": play_index, "tally": tally if not tally_problems else None,
        "pre_max": score.PASS1_MAX, "full_max": score.FULL_MAX,
    }


# ---------------------------------------------------------------------------- config


def preview_config(instance_path):
    """Validate an instance, its plays file and its scoring config. Returns (scoring, findings).

    `scoring` is None when the instance has no usable scoring config, in which case the
    demo falls back to the ILLUSTRATIVE parameters and says so. Findings are
    (severity, text, fix) with severity "blocks" or "review".
    """
    findings, instance = [], {}
    path = Path(instance_path)
    if not path.exists():
        findings.append(("blocks", f"no instance config at {path}",
                         "Copy instance-config.example.json to instance-config.json and run the "
                         "environment-setup skill."))
    else:
        keys, _ = validate_instance_config.load_schema()
        for problem in validate_instance_config.check_config(path, keys):
            if "required but empty" in problem or problem.startswith("missing key"):
                continue  # counted once, below, by setup_status
            findings.append(("blocks", f"instance config: {problem}",
                             "Fix the value; see references/instance-config.md."))
        report, _ = setup_status.build_report(path)
        if "error" in report:
            findings.append(("blocks", report["error"], "Fix the file's JSON."))
        else:
            open_keys = report["required_still_open"]
            if open_keys:
                findings.append(("blocks", f"{len(open_keys)} required instance key(s) still unset, "
                                 f"first: {open_keys[0]}",
                                 "Run `python3 scripts/setup_status.py` for the full list and "
                                 "what each gap blocks."))
            if report["unreviewed_defaults"]:
                findings.append(("review", f"{len(report['unreviewed_defaults'])} key(s) still hold "
                                 "their shipped default: " + ", ".join(report["unreviewed_defaults"]),
                                 "Confirm each is right for this workspace."))
        try:
            instance = load(path)
        except (OSError, json.JSONDecodeError):
            instance = {}

    user_play_ids = check_plays_file(instance, path, findings)

    name = (instance.get("SCORING_CONFIG_FILE") or "").strip() or "scoring-config.json"
    scoring_path = (path.parent / name) if path.exists() else Path(name)
    if not scoring_path.exists():
        findings.append(("blocks", f"no scoring config at {scoring_path}; this preview scored with "
                         "the ILLUSTRATIVE demo parameters instead",
                         "Decide your exclusions, scoring rules, play points and tier cutoffs at "
                         "provisioning (provision-gtm-engine Phase 1) and save them in the "
                         "score.py schema. examples/demo/scoring.demo.json shows the shape."))
        return None, findings
    try:
        scoring = load(scoring_path)
    except (OSError, json.JSONDecodeError) as e:
        findings.append(("blocks", f"cannot read {scoring_path}: {e}", "Fix the file's JSON."))
        return None, findings
    problems = score.validate_config(scoring, user_play_ids)
    if problems:
        for problem in problems:
            findings.append(("blocks", f"scoring config: {problem}",
                             "Fix it; `python3 skills/gtm-signal-scan/scripts/score.py "
                             "--check-config <file>` re-checks."))
        return None, findings
    if scoring.get("provenance") != "deployment":
        findings.append(("review", "scoring config provenance is "
                         f"{scoring.get('provenance')!r}, not 'deployment'",
                         "Set provenance to 'deployment' once the rules are decisions rather "
                         "than placeholders."))
    if not isinstance(scoring.get("people"), dict):
        findings.append(("blocks", "scoring config has no `people` section",
                         "Add role priority, size bands and the T3 threshold."))
        return None, findings
    if (scoring.get("catch_all_policy") or {}).get("decision", "unset") not in ("enroll", "exclude"):
        findings.append(("blocks", "no catch-all enrollment policy recorded",
                         "This is a named human gate: choose exclude or enroll, with a date, a "
                         "reason and a bounce threshold, before the first send."))
    return scoring, findings


def check_plays_file(instance, instance_path, findings):
    """Shape-check the instance's plays file, appending findings. Returns its play ids or None.

    Only the shape is checked (check_plays.py). Whether each play's free-form criteria are
    GOOD is the model's job against the guidance, and the operator's at review.
    """
    name = (instance.get("PLAYS_FILE") or "").strip() or "plays.json"
    plays_path = (instance_path.parent / name) if instance_path.exists() else Path(name)
    if not plays_path.exists():
        findings.append(("blocks", f"no plays file at {plays_path}; the scan cannot assign plays",
                         "Define your plays with the play-builder skill. "
                         "examples/demo/plays.demo.json shows the shape."))
        return None
    try:
        doc = load(plays_path)
    except (OSError, json.JSONDecodeError) as e:
        findings.append(("blocks", f"cannot read {plays_path}: {e}", "Fix the file's JSON."))
        return None
    problems, warnings = check_plays.check(doc, check_plays.apollo_field_keys())
    for problem in problems:
        findings.append(("blocks", f"plays: {problem}",
                         "Fix it; `python3 skills/play-builder/scripts/check_plays.py <file>` re-checks."))
    for warning in warnings:
        findings.append(("review", f"plays: {warning}",
                         "Name it, or build it with the play-builder skill."))
    if problems:
        return None
    return [pl["id"] for pl in doc["plays"]]


# ---------------------------------------------------------------------------- render


def table(header, rows, label):
    """A markdown table whose last column is the label. Every row carries one."""
    out = ["| " + " | ".join(header + ["Label"]) + " |",
           "|" + "---|" * (len(header) + 1)]
    for row in rows:
        cells = list(row)
        lab = cells.pop() if len(cells) == len(header) + 1 else label
        out.append("| " + " | ".join(str(c) for c in cells + [lab]) + " |")
    return "\n".join(out)


def render(r, findings=None, scoring_source="ILLUSTRATIVE demo parameters"):
    """Render the report as markdown. Deterministic for the same result."""
    L = r["label"]
    queue_n = len(r["queue"])
    mode_line = ("**Run mode: PREVIEW.** Synthetic accounts through your instance's config. "
                 if L == "PREVIEW" else
                 "**Run mode: SIMULATED.** Synthetic accounts, real decision logic. ")
    lines = [
        "# GTM OS demo run",
        "",
        f"> {mode_line}No connector was called, no credit was spent, nothing was written to a "
        "CRM or a base, and nothing was sent. Companies and people are invented, on `.example` "
        f"domains. Scoring used: **{scoring_source}**. As of {r['as_of']}.",
        "",
        "Every table row carries a label. The four labels are defined in the plugin root's "
        "`references/run-manifest.md`:",
        "",
        table(["What the row is"], [
            ["Synthetic input, real engine logic", "SIMULATED"],
            ["A hand-written stand-in for an API or model response", "FIXTURE"],
            ["Your real config over synthetic input, no spend", "PREVIEW"],
            ["Real calls against your own tools", "LIVE"]], L),
        "",
        "## Headline",
        "",
        f"{r['source_count']} source records became {len(r['accounts'])} accounts; "
        f"{len(r['to_enrich'])} earned enrichment, {len(r['matched'])} people earned a match "
        f"credit, and **{queue_n} contact(s) reached the pre-send review queue**. "
        f"**0 sent. 0 credits spent.** The same run live would state a cap of "
        f"**{r['planned']} Apollo credits** before spending and, at this ranking, spend "
        f"**{r['would_spend']}**.",
        "",
        table(["Stage", "Count"], [
            ["Source records", r["source_count"]],
            ["Rejected at intake", len(r["rejected"])],
            ["Unique accounts", len(r["accounts"])],
            ["Excluded before any spend", len(r["excluded"])],
            ["Held: no play fits yet", len(r["unassigned"])],
            ["Pre-scored", len(r["routed"])],
            ["Enriched (pre-score Excellent + Good)", len(r["to_enrich"])],
            ["People ranked", len(r["people_rows"])],
            ["People matched", len(r["matched"])],
            ["Passed the field gate", sum(1 for p in r["gate_rows"] if p["gate"]["gate"] == "PASS")],
            ["Ready for pre-send review", queue_n],
            ["Sent", 0]], L),
        "",
    ]

    lines += ["## 1. Intake and dedupe", "",
              table(["Account", "Domain", "Signals", "Route"], [
                  [a["name"], a["domain"],
                   " + ".join(f"{s['type']} ({s['observed_on'] or 'date unknown'})" for s in a["signals"]),
                   "in CRM: update, never create" if a["in_crm"] else "net new: create"]
                  for a in r["accounts"]] +
                  [[x["name"], "(none)", "", f"rejected: {x['reason']}"] for x in r["rejected"]], L),
              "",
              "*Live:* the company search costs one credit; its `accounts` array is what is already "
              "in the CRM and its `organizations` array is net new. Account creation does not "
              "dedupe, so this split is the only thing standing between a run and duplicate records.",
              ""]

    lines += ["## 2. Exclusions (free, deterministic)", "",
              table(["Account", "GTM team", "Decision"], [
                  [a["name"], a.get("gtm_team_size") if a.get("gtm_team_size") is not None else "unknown",
                   f"excluded: {reason}"] for a, reason in r["excluded"]] + [
                  [a["name"], "unknown" if a.get("gtm_team_size") is None else a["gtm_team_size"],
                   "not excluded"] for a in r["unassigned"] + r["routed"]], L),
              "",
              "*Live:* one free people search per account answers the exclusion and gathers the "
              "evidence play assignment needs, which is why both run before enrichment.",
              "",
              "## 3. Play assignment (the model's judgment)", "",
              "Plays differ between organizations, so their entry criteria are free text and the "
              "model judges them against the evidence. In this demo that judgment is a FIXTURE; the "
              "check that the chosen play exists, and the hold when none fits, are real.",
              "",
              table(["Account", "Play", "Reasoning", "Evidence"], [
                  [a["name"], f"{a['play']} ({r['plays'][a['play']]['code']})",
                   a["_assign"]["reasoning"], a["_assign"].get("evidence") or "", "FIXTURE"]
                  for a in r["routed"]] + [
                  [a["name"], "none", f"held: {a['_assign']['reasoning']}",
                   a["_assign"].get("evidence") or "", "FIXTURE"] for a in r["unassigned"]], L),
              ""]

    lines += [f"## 4. Pre-score, pass 1 (free, out of {r['pre_max']})", "",
              table(["Account", "Play", "Pre-score", "Pre-tier", "Unknown inputs", "Next"], [
                  [a["name"], a["_pre"]["play"], a["_pre"]["points"], a["_pre"]["tier"],
                   ", ".join(a["_pre"]["unknown"]) or "none",
                   {"Excellent": "enrich", "Good": "enrich", "Fair": "account record only, no spend"}
                   .get(a["_pre"]["tier"], "held: below the pre-score floor, no spend")]
                  for a in r["routed"]], L),
              "",
              "A pre-score is never reported as a final score. An unknown input scores 0 and is "
              "named, so a gap is visible instead of reading as a weak account.",
              ""]

    lines += ["## 5. Credit statement, made before any spend", "",
              table(["Line item", "Units", "Credits each", "Subtotal"],
                    [[name, n, c, n * c] for name, n, c in r["estimate"]] +
                    [["**Cap stated to the operator**", "", "", f"**{r['planned']}**"],
                     ["Would spend at this ranking", "", "", r["would_spend"]],
                     ["Actually spent", "", "", 0]], L),
              "",
              "Per-unit costs are read from the plugin root's `references/apollo-credit-costs.md` "
              "at run time. The people line is capped at each account's quota; ranking then spends "
              "less. " + (f"Run-cost tally: `{r['tally']['cost_summary']}`." if r["tally"] else ""),
              "",
              "*Live:* the run stops here and asks. Credit spend is a named human gate.",
              ""]

    dims = [n for n, _, _ in score.DIMENSIONS]
    lines += [f"## 6. Enrichment and the full score (out of {r['full_max']})", "",
              "Enrichment values are FIXTURES standing in for org enrichment and the job postings "
              "call; the scoring over them is real.",
              "",
              table(["Account"] + dims + ["Score", "Tier"], [
                  [a["name"]] + [d["points"] if not d["unknown"] else f"0 (unknown)"
                                 for d in a["_full"]["dimensions"]] +
                  [a["_full"]["points"], a["_full"]["tier"]] for a in r["to_enrich"]], L),
              ""]

    lines += ["## 7. People: rank on reachability before spending", "",
              table(["Account", "Person", "Title", "Email flag", "Reach", "Role", "Decision"], [
                  [p["account"], p["name"], p["title"], p["email_status"] or "absent", p["tier"],
                   p["role_basis"], ("skip" if p["decision"] == "skip"
                                     else f"{p['decision']}: {p['reason']}") +
                   (f"; then {p['post']}" if p.get("post") else "")]
                  for p in r["people_rows"]], L),
              "",
              "Reachability tiers are parsed from `references/apollo-credit-costs.md`, not copied. "
              "A T4 contact never gets a match credit; a shortfall is taken rather than filled "
              f"from T4. Catch-all enrollment policy on record: **{r['policy']}**.",
              ""]
    shortfalls = [(a["name"], a["_people"]) for a in r["to_enrich"]
                  if a.get("_people") and a["_people"]["shortfall"]]
    for name, ranked in shortfalls:
        lines += [f"{name} could draw {ranked['quota']} and yielded {ranked['selected']} reachable; "
                  "the shortfall was taken.", ""]

    lines += ["## 8. Field gate (Excellent contacts)", "",
              table(["Contact", "Gate", "Fact-bearing sources", "Missing"], [
                  [p["name"], p["gate"]["gate"], p["gate"]["fact_floor"]["count"],
                   "; ".join(p["gate"]["missing_required"]) or "none"] for p in r["gate_rows"]], L),
              "",
              "The contact and account records are FIXTURES; the gate is `field_gate.py`, unchanged. "
              "A FAIL names its remediation instead of composing around the gap.",
              ""]

    lines += ["## 9. Composition checks", "",
              "The opener text below is a FIXTURE. The demo does not call a model; it runs the "
              "deterministic checks a live opener must also pass: no bare merge tokens, and every "
              "number traceable to a named source.", ""]
    for p in r["comp_rows"]:
        if p.get("opener"):
            lines += [f"**{p['name']}** ({p['account']}), FIXTURE:", "",
                      f"> {p['opener']['text']}", ""]
    lines += [table(["Contact", "Checks"], [
        [p["name"], "pass" if not p["composition"] else "; ".join(p["composition"])]
        for p in r["comp_rows"]], L), ""]

    lines += ["## 10. Pre-send review queue", "",
              table(["Contact", "Account", "Status"],
                    [[p["name"], p["account"], why] for p, why in r["queue"]] +
                    [[p["name"], p["account"], why] for p, why in r["held"]], L),
              "",
              "Nothing is enrolled. Pre-send review and enrollment are human gates, in the demo "
              "and in a live run.",
              ""]

    if findings is not None:
        lines += ["## Findings in your setup", ""]
        if findings:
            lines += [table(["Severity", "Finding", "Fix"],
                            [[s, t, f] for s, t, f in findings], L), ""]
        else:
            lines += ["None. Your config is complete in shape; the next step is a live run.", ""]
    else:
        lines += ["## Next step", "",
                  "Run the same accounts through your own setup. Nothing is spent:",
                  "",
                  "```",
                  "python3 scripts/demo.py --config instance-config.json",
                  "```",
                  "",
                  "Every gap it finds (an unset key, a missing plays file or scoring config, a "
                  "play with no list, an unrecorded catch-all policy) comes back as a finding.",
                  ""]
    return "\n".join(lines)


def run_shape(r, mode, scoring_source):
    """The Step 7 run artifact, with run_mode so it is never mistaken for a live run."""
    return {
        "run_mode": mode, "run_id": r["run_id"], "run_date": r["as_of"],
        "scoring_parameters": scoring_source, "filters_used": "examples/demo/fixtures.json",
        "counts": {"searched": r["source_count"], "rejected": len(r["rejected"]),
                   "accounts": len(r["accounts"]), "excluded": len(r["excluded"]),
                   "unassigned": len(r["unassigned"]), "scored": len(r["routed"]),
                   "enriched": len(r["to_enrich"]), "people_ranked": len(r["people_rows"]),
                   "people_matched": len(r["matched"]), "ready_for_review": len(r["queue"]),
                   "sent": 0},
        "credits": {"planned": r["planned"], "would_spend": r["would_spend"], "spent": 0,
                    "by_category": {name: n * c for name, n, c in r["estimate"]}},
        "held": [{"contact": p["name"], "reason": why} for p, why in r["held"]],
    }


def build(config_path=None):
    """Run the demo end to end. Returns (report_markdown, run_shape, findings or None)."""
    fx = load(FIXTURES)
    costs_text = COSTS.read_text("utf-8")
    costs = credit_costs(costs_text)
    tiers = rank_people.parse_reachability(costs_text)
    demo_scoring, plays = load(DEMO_SCORING), load(DEMO_PLAYS)
    findings, scoring, source = None, None, "ILLUSTRATIVE demo parameters"
    if config_path is not None:
        scoring, findings = preview_config(config_path)
        if scoring is not None:
            # The synthetic accounts' play assignments are fixtures against the DEMO plays, so
            # play_fit is scored on the demo's points; every other rule is yours. Your own
            # plays file is shape-checked separately and reported as findings.
            scoring = json.loads(json.dumps(scoring))
            scoring["dimensions"]["play_fit"] = demo_scoring["dimensions"]["play_fit"]
            source = (f"your scoring config (provenance: {scoring.get('provenance')}), with "
                      "play_fit from the demo plays")
    if scoring is None:
        scoring = demo_scoring
    label = "PREVIEW" if config_path is not None else "SIMULATED"
    result = run_pipeline(fx, scoring, plays, costs, tiers, label)
    return render(result, findings, source), run_shape(result, label, source), findings


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser()
    p.add_argument("--config", help="Your instance-config.json. Omit for the synthetic run.")
    p.add_argument("--out", default="gtm-os-demo", help="Output folder (default ./gtm-os-demo).")
    p.add_argument("--stdout", action="store_true", help="Print the report instead of writing it.")
    args = p.parse_args()
    try:
        report, shape, findings = build(args.config)
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"The demo could not run: {e}", file=sys.stderr)
        sys.exit(2)
    if args.stdout:
        print(report)
    else:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(report + "\n", "utf-8")
        (out / "run-shape.json").write_text(json.dumps(shape, indent=2) + "\n", "utf-8")
        c = shape["counts"]
        print(f"{shape['run_mode']}: {c['searched']} source records -> {c['accounts']} accounts -> "
              f"{c['people_matched']} matched -> {c['ready_for_review']} ready for review. "
              f"0 sent, 0 credits spent. Report: {out / 'report.md'}")
    blocking = findings and any(s == "blocks" for s, _, _ in findings)
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
