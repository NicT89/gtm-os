"""Tests for skills/gtm-signal-scan/scripts/rank_people.py.

The defect this script exists to prevent already happened once: a restated tier table lost
`unverified` from T4, so unverified candidates read as spendable. So the tiers are parsed
from references/apollo-credit-costs.md, and these tests read that same file.

Run: python3 -m unittest discover -s tests -v
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "rank_people", ROOT / "skills" / "gtm-signal-scan" / "scripts" / "rank_people.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

COSTS = (ROOT / "references" / "apollo-credit-costs.md").read_text("utf-8")
TIERS = rp.parse_reachability(COSTS)
PEOPLE = json.loads((ROOT / "examples" / "demo" / "scoring.demo.json").read_text("utf-8"))["people"]


def person(name, title, status, phone=False):
    return {"name": name, "title": title, "email_status": status, "phone_available": phone}


class Reachability(unittest.TestCase):
    def tier_of(self, status, phone=False):
        return rp.reachability({"email_status": status, "phone_available": phone}, TIERS)["tier"]

    def test_the_historically_dropped_flags_are_where_they_belong(self):
        self.assertEqual(self.tier_of("unverified"), "T4")
        self.assertEqual(self.tier_of("likely"), "T3")

    def test_phone_separates_t1_from_t2(self):
        self.assertEqual(self.tier_of("verified", True), "T1")
        self.assertEqual(self.tier_of("verified"), "T2")

    def test_absent_and_unrecognized_flags_fail_closed(self):
        self.assertEqual(self.tier_of(None), "T4")
        self.assertEqual(self.tier_of("someday"), "T4")

    def test_a_missing_section_raises_instead_of_ranking_everyone_t4(self):
        with self.assertRaises(ValueError):
            rp.parse_reachability(COSTS.replace("## Reachability tiers", "## Tiers"))

    def test_editing_the_reference_changes_the_ranking(self):
        """Proves the table is read, not remembered."""
        edited = COSTS.replace("| `unavailable`, `unverified`, absent | T4",
                               "| `unavailable`, absent | T4").replace(
            "| `catch_all`, `guessed`, `likely` | T3", "| `catch_all`, `guessed`, `likely`, `unverified` | T3")
        tier = rp.reachability({"email_status": "unverified"}, rp.parse_reachability(edited))
        self.assertEqual(tier["tier"], "T3")


class RoleFit(unittest.TestCase):
    def test_founding_commercial_titles_are_ics_not_founders(self):
        rank, _, basis = rp.role_fit("Founding Account Executive", PEOPLE)
        self.assertEqual(rank, 3)
        self.assertIn("not a founder", basis)

    def test_founding_engineer_is_skipped(self):
        self.assertIsNone(rp.role_fit("Founding Engineer", PEOPLE)[0])

    def test_skip_terms_match_words_not_substrings(self):
        """'board' must not skip an Onboarding lead."""
        rank, _, basis = rp.role_fit("Head of Onboarding Operations", PEOPLE)
        self.assertNotIn("board", basis)

    def test_co_founder_is_priority_one(self):
        self.assertEqual(rp.role_fit("Co-founder & COO", PEOPLE)[0], 1)


class Ranking(unittest.TestCase):
    def test_t4_is_never_matched_even_with_quota_to_spare(self):
        out = rp.rank([person("A", "CEO", "unavailable")], "Excellent", 20, PEOPLE, TIERS)
        self.assertEqual(out["selected"], 0)
        self.assertEqual(out["shortfall"], 3)
        self.assertEqual(out["people"][0]["decision"], "hold")

    def test_weak_t3_is_held_strong_t3_is_matched(self):
        out = rp.rank([person("A", "Head of Marketing", "guessed"),
                       person("B", "Founder", "catch_all")], "Excellent", 20, PEOPLE, TIERS)
        decisions = {p["name"]: p["decision"] for p in out["people"]}
        self.assertEqual(decisions, {"A": "hold", "B": "match"})

    def test_quota_follows_tier_and_size(self):
        self.assertEqual(rp.quota("Excellent", 15, PEOPLE), 3)
        self.assertEqual(rp.quota("Excellent", 50, PEOPLE), 5)
        self.assertEqual(rp.quota("Excellent", 400, PEOPLE), 7)
        self.assertEqual(rp.quota("Good", 400, PEOPLE), 2)
        self.assertEqual(rp.quota("Fair", 50, PEOPLE), 0)

    def test_over_quota_is_held_in_rank_order(self):
        people = [person(n, "CEO", "verified") for n in ("A", "B", "C")]
        out = rp.rank(people, "Good", 20, PEOPLE, TIERS)
        self.assertEqual(out["selected"], 2)
        self.assertEqual([p["decision"] for p in out["people"]], ["match", "match", "hold"])


if __name__ == "__main__":
    unittest.main()
