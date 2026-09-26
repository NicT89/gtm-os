"""Tests for scripts/demo.py, the offline demo.

Three things are pinned here, each one a way the demo could quietly stop being honest:

1. **The committed report is the generator's output**, byte for byte. A hand-edited
   examples/demo-report.md would show behavior the engine does not have.
2. **Every table row carries a run-mode label.** The labels are the difference between a
   demo and a claim about a real account (references/run-manifest.md).
3. **Every planted hold produces its reason**, and each check is proved able to fail by
   mutating the fixture or the reference it reads, in memory.

Run: python3 -m unittest discover -s tests -v
"""
import copy
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("demo", ROOT / "scripts" / "demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)

FX = json.loads(demo.FIXTURES.read_text("utf-8"))
SCORING = json.loads(demo.DEMO_SCORING.read_text("utf-8"))
PLAYS = json.loads(demo.DEMO_PLAYS.read_text("utf-8"))
COSTS_TEXT = demo.COSTS.read_text("utf-8")
REPORT, SHAPE, _ = demo.build()


def run(fx=None, scoring=None, costs_text=None, label="SIMULATED", plays=None):
    """Run the pipeline in memory over (possibly mutated) inputs; return (result, markdown)."""
    text = costs_text or COSTS_TEXT
    result = demo.run_pipeline(copy.deepcopy(fx or FX), copy.deepcopy(scoring or SCORING),
                               copy.deepcopy(plays or PLAYS),
                               demo.credit_costs(text), demo.rank_people.parse_reachability(text),
                               label)
    return result, demo.render(result)


def unlabeled_rows(markdown):
    """Table body rows whose last cell is not one of the four labels."""
    bad = []
    for line in markdown.splitlines():
        if not line.startswith("|") or re.fullmatch(r"\|(---\|)+", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[-1] == "Label":
            continue  # header row
        if cells[-1] not in demo.LABELS:
            bad.append(line)
    return bad


def held_reason(markdown, name):
    """The status cell for a contact in the pre-send queue table."""
    section = markdown[markdown.index("## 10. Pre-send review queue"):]
    for line in section.splitlines():
        if line.startswith(f"| {name} |"):
            return line
    return ""


class CommittedReport(unittest.TestCase):
    def test_the_example_is_the_generators_output(self):
        committed = (ROOT / "examples" / "demo-report.md").read_text("utf-8")
        self.assertEqual(committed, REPORT + "\n",
                         "examples/demo-report.md drifted; regenerate it with "
                         "`python3 scripts/demo.py --stdout > examples/demo-report.md`")

    def test_two_runs_are_identical(self):
        """The clock is never read, so a replay is byte-identical."""
        self.assertEqual(demo.build()[0], REPORT)


class Labels(unittest.TestCase):
    def test_every_row_is_labeled(self):
        self.assertEqual(unlabeled_rows(REPORT), [])

    def test_the_label_check_can_fail(self):
        planted = REPORT.replace("| Sent | 0 | SIMULATED |", "| Sent | 0 |  |")
        self.assertEqual(len(unlabeled_rows(planted)), 1)

    def test_banner_and_run_shape_name_the_mode(self):
        self.assertIn("**Run mode: SIMULATED.**", REPORT)
        self.assertEqual(SHAPE["run_mode"], "SIMULATED")
        self.assertEqual(SHAPE["credits"]["spent"], 0)
        self.assertEqual(SHAPE["counts"]["sent"], 0)

    def test_illustrative_parameters_are_declared(self):
        self.assertIn("ILLUSTRATIVE demo parameters", REPORT)
        self.assertEqual(SCORING["provenance"], "illustrative")

    def test_openers_are_marked_fixture(self):
        for name in ("A. Reyes", "M. Duarte"):
            self.assertIn(f"**{name}**", REPORT)
            self.assertRegex(REPORT, rf"\*\*{re.escape(name)}\*\* \([^)]+\), FIXTURE:")


class PlantedHolds(unittest.TestCase):
    def test_duplicate_domain_merges_and_keeps_both_signals(self):
        self.assertIn("| Cobalt Systems | cobalt.example | hiring (2026-08-28) + funding (2026-06-30) |", REPORT)

    def test_intake_rejects_and_routes(self):
        self.assertIn("rejected: no domain", REPORT)
        self.assertIn("| Northwind Analytics | northwind.example | hiring (2026-08-25) | in CRM: update, never create |", REPORT)

    def test_exclusions_before_spend(self):
        for text in ("excluded: category: competitor", "excluded: category: staffing_firm",
                     "excluded: established GTM team of 3"):
            self.assertIn(text, REPORT)

    def test_unknown_team_state_is_held_not_routed(self):
        self.assertRegex(REPORT, r"\| Lumen Freight \| none \| held: team state unknown")

    def test_play_assignment_is_labeled_as_the_models_judgment(self):
        """Assignment is a model judgment against free-form criteria; the demo must never
        present its stand-in as engine logic."""
        section = REPORT[REPORT.index("## 3. Play assignment"):REPORT.index("## 4.")]
        rows = [l for l in section.splitlines() if l.startswith("| ") and "---" not in l][1:]
        self.assertTrue(rows)
        self.assertTrue(all(r.rstrip().endswith("| FIXTURE |") for r in rows), rows)

    def test_score_floors(self):
        self.assertRegex(REPORT, r"\| Quarry Works \|.*account record only, no spend")
        self.assertRegex(REPORT, r"\| Meridian Retail \|.*\| Below Fair \|")
        self.assertNotIn("| Meridian Retail | ", REPORT[REPORT.index("## 7."):REPORT.index("## 8.")])

    def test_people_holds(self):
        self.assertRegex(REPORT, r"\| L\. Chen \|.*\| T4 \|.*hold: T4: no match credit")
        self.assertRegex(REPORT, r"\| E\. Walsh \|.*hold: T3: role fit below")
        self.assertIn("held: catch-all enrollment gate", held_reason(REPORT, "S. Lindqvist"))
        self.assertIn("held: field gate FAIL", held_reason(REPORT, "P. Anand"))
        self.assertIn("the number '40' appears in no named source", held_reason(REPORT, "R. Singh"))

    def test_every_planted_case_is_named_in_the_fixture(self):
        """The fixture's _planted map is the contract these tests enforce."""
        for key in ("L. Chen", "S. Lindqvist", "E. Walsh", "P. Anand", "R. Singh",
                    "lumen.example", "vantage.example", "meridian.example"):
            self.assertIn(key, FX["_planted"])


class ChecksCanFail(unittest.TestCase):
    """Each check broken on purpose, per CLAUDE.md: a check that cannot fail is decoration."""

    def test_sourcing_the_number_clears_the_composition_hold(self):
        fx = copy.deepcopy(FX)
        fx["openers"]["R. Singh"]["facts"].append("Carries 40 accounts (territory plan)")
        _, md = run(fx)
        self.assertIn("ready for pre-send review", held_reason(md, "R. Singh"))

    def test_a_bare_merge_token_is_caught(self):
        fx = copy.deepcopy(FX)
        fx["openers"]["A. Reyes"]["text"] += " {{First Name}}"
        _, md = run(fx)
        self.assertIn("bare merge token", held_reason(md, "A. Reyes"))

    def test_filling_the_missing_field_clears_the_gate(self):
        fx = copy.deepcopy(FX)
        fx["contact_fields"]["P. Anand"]["DEMO_CF_PROFILE_SUMMARY"] = "VP Marketing since 2025."
        fx["openers"]["P. Anand"] = {"text": "A question about the GTM Engineer req.", "facts": []}
        _, md = run(fx)
        self.assertIn("ready for pre-send review", held_reason(md, "P. Anand"))

    def test_a_recorded_catch_all_policy_changes_the_outcome(self):
        scoring = copy.deepcopy(SCORING)
        scoring["catch_all_policy"]["decision"] = "enroll"
        _, md = run(scoring=scoring)
        self.assertNotIn("held: catch-all", held_reason(md, "S. Lindqvist"))

    def test_credit_costs_are_read_from_the_reference(self):
        base, _ = run()
        doubled = COSTS_TEXT.replace("| Organization enrichment (`organizations/enrich`) | 1 credit per company",
                                     "| Organization enrichment (`organizations/enrich`) | 2 credits per company")
        self.assertNotEqual(doubled, COSTS_TEXT, "the cost row this test edits has moved")
        changed, _ = run(costs_text=doubled)
        self.assertEqual(changed["planned"], base["planned"] + len(base["to_enrich"]))

    def test_a_missing_cost_row_refuses_to_estimate(self):
        broken = "\n".join(line for line in COSTS_TEXT.splitlines() if not line.startswith("| Job postings"))
        with self.assertRaises(ValueError):
            demo.credit_costs(broken)

    def test_an_assigned_play_missing_from_the_plays_file_is_held(self):
        """The one deterministic part of assignment: the chosen play must exist."""
        plays = copy.deepcopy(PLAYS)
        plays["plays"] = [p for p in plays["plays"] if p["id"] != "new-leader"]
        result, md = run(plays=plays)
        self.assertIn("Tidewater AI", [a["name"] for a in result["unassigned"]])
        self.assertIn("'new-leader' is not in the plays file", md)

    def test_dedupe_is_what_merges_the_duplicate(self):
        fx = copy.deepcopy(FX)
        fx["search_response"]["organizations"][1]["domain"] = "cobalt-two.example"
        result, _ = run(fx)
        self.assertEqual(len(result["accounts"]), len(demo.intake(FX["search_response"])[0]) + 1)


class PreviewMode(unittest.TestCase):
    def instance(self, directory, scoring=None, plays=None):
        schema = json.loads((ROOT / "instance-config.example.json").read_text("utf-8"))
        config = {}
        for key, shipped in schema.items():
            if key.startswith("_"):
                continue
            if key.startswith("AIRTABLE_") and key.endswith("_BASE_ID"):
                config[key] = "app" + "a" * 14
            elif key.startswith("AIRTABLE_TBL_"):
                config[key] = "tbl" + "a" * 14
            elif key.startswith("AIRTABLE_FLD_"):
                config[key] = "fld" + "a" * 14
            elif key.startswith("APOLLO_CF_"):
                config[key] = "0" * 24
            else:
                config[key] = shipped or "chosen"
        path = Path(directory) / "instance-config.json"
        path.write_text(json.dumps(config), "utf-8")
        if scoring is not None:
            (Path(directory) / config["SCORING_CONFIG_FILE"]).write_text(json.dumps(scoring), "utf-8")
        if plays is not None:
            (Path(directory) / config["PLAYS_FILE"]).write_text(json.dumps(plays), "utf-8")
        return path

    def test_missing_scoring_config_is_a_blocking_finding(self):
        with tempfile.TemporaryDirectory() as d:
            report, shape, findings = demo.build(self.instance(d))
        self.assertTrue(any(s == "blocks" and "no scoring config" in t for s, t, _ in findings))
        self.assertIn("**Run mode: PREVIEW.**", report)
        self.assertEqual(shape["run_mode"], "PREVIEW")
        self.assertEqual(unlabeled_rows(report), [])
        self.assertIn("ILLUSTRATIVE demo parameters", report)

    def test_an_illustrative_scoring_config_is_flagged_and_used(self):
        with tempfile.TemporaryDirectory() as d:
            report, _, findings = demo.build(self.instance(d, SCORING))
        texts = [t for _, t, _ in findings]
        self.assertTrue(any("provenance is 'illustrative'" in t for t in texts))
        self.assertTrue(any("catch-all" in t for t in texts))
        self.assertIn("your scoring config", report)

    def test_a_decided_config_leaves_no_scoring_findings(self):
        decided = copy.deepcopy(SCORING)
        decided["provenance"] = "deployment"
        decided["catch_all_policy"] = {"decision": "exclude", "decided_on": "2026-09-01",
                                       "reason": "small-company domains", "bounce_threshold": "2%"}
        plays = copy.deepcopy(PLAYS)
        plays["provenance"] = "deployment"
        with tempfile.TemporaryDirectory() as d:
            _, _, findings = demo.build(self.instance(d, decided, plays))
        self.assertFalse(any(s == "blocks" for s, _, _ in findings), findings)

    def test_a_missing_plays_file_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            _, _, findings = demo.build(self.instance(d, SCORING))
        self.assertTrue(any(s == "blocks" and "no plays file" in t for s, t, _ in findings))

    def test_a_play_without_play_fit_points_blocks(self):
        """Your plays and your scoring config must agree, or a play scores 0 by accident."""
        plays = copy.deepcopy(PLAYS)
        plays["plays"][0]["id"] = "brand-new-play"
        with tempfile.TemporaryDirectory() as d:
            _, _, findings = demo.build(self.instance(d, SCORING, plays))
        self.assertTrue(any("'brand-new-play'" in t for _, t, _ in findings), findings)

    def test_an_invalid_scoring_config_falls_back_and_says_so(self):
        bad = copy.deepcopy(SCORING)
        bad["tiers"]["excellent"] = 150
        with tempfile.TemporaryDirectory() as d:
            report, _, findings = demo.build(self.instance(d, bad))
        self.assertTrue(any("scoring config:" in t for _, t, _ in findings))
        self.assertIn("ILLUSTRATIVE demo parameters", report)


if __name__ == "__main__":
    unittest.main()
