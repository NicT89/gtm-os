"""Tests for scripts/check_scrape_rows.py: scraped rows against the posts-base schema.

The schema is parsed from references/airtable-posts-base.md at run time. The parser tests
come first so the rule tests cannot pass on an empty schema.

Run: python3 -m unittest discover -s tests -v
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_scrape_rows.py"
spec = importlib.util.spec_from_file_location("check_scrape_rows", SCRIPT)
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

SCHEMA = cs.load_schema()
POST = {"Name": "Ada Example", "Post ID": "7300000000000000001",
        "Person LinkedIn URL": "https://www.linkedin.com/in/ada-example",
        "Post URL": "https://www.linkedin.com/posts/ada-example_1", "Post Content": "Hello",
        "Post Type": "Post", "Posted Date": "2026-09-20", "Likes": 12, "Comments Count": 3,
        "Shares": 1, "Scraped At": "2026-09-27"}


def problems_for(row, table="Person Post"):
    return cs.check({"deliveries": [{"table": table, "rows": [row]}]}, SCHEMA)


class TheSchemaParses(unittest.TestCase):
    def test_all_five_tables(self):
        self.assertEqual(set(SCHEMA), {"Contacts", "Company", "Person Post", "Company Posts",
                                       "Post Comments"})

    def test_dedupe_keys_and_options_are_found(self):
        dedupe = {t: [f for f, s in fs.items() if s["dedupe"]] for t, fs in SCHEMA.items()}
        self.assertEqual(dedupe["Person Post"], ["Post ID"])
        self.assertEqual(dedupe["Post Comments"], ["Comment ID"])
        self.assertEqual(SCHEMA["Person Post"]["Post Type"]["options"],
                         ["Post", "Repost", "No Content"])

    def test_a_schema_doc_without_the_tables_section_fails_loudly(self):
        with self.assertRaises(IndexError):
            cs.load_schema("# nothing here")


class Rows(unittest.TestCase):
    def test_a_good_row_passes(self):
        self.assertEqual(problems_for(POST), [])

    def test_each_rule_fires(self):
        cases = {
            "is not a posts-base table": (POST, "Posts"),
            "is not a field": (dict(POST, Sentiment="positive"), "Person Post"),
            "is a link": (dict(POST, Contact="rec123"), "Person Post"),
            "dedupe key 'Post ID'": ({k: v for k, v in POST.items() if k != "Post ID"},
                                     "Person Post"),
            "is not an option": (dict(POST, **{"Post Type": "Article"}), "Person Post"),
            "bare YYYY-MM-DD": (dict(POST, **{"Posted Date": "2026-09-20T10:00:00Z"}),
                                "Person Post"),
            "not an integer": (dict(POST, Likes="12"), "Person Post"),
            "http(s) URL": (dict(POST, **{"Post URL": "linkedin.com/x"}), "Person Post"),
        }
        for text, (row, table) in cases.items():
            with self.subTest(text):
                problems = problems_for(row, table)
                self.assertTrue(any(text in p for p in problems), problems)


class Cli(unittest.TestCase):
    def test_exit_codes(self):
        def run(obj):
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
                json.dump(obj, f)
            return subprocess.run([sys.executable, str(SCRIPT), f.name],
                                  capture_output=True).returncode
        good = {"deliveries": [{"table": "Person Post", "rows": [POST]}]}
        self.assertEqual(run(good), 0)
        bad = copy.deepcopy(good)
        bad["deliveries"][0]["rows"][0]["Likes"] = "many"
        self.assertEqual(run(bad), 1)
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT)],
                                        capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
