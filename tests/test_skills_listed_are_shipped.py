"""Every skill the README lists must be a file the repo actually ships.

Observed on the 1.10.0 PR: `.gitignore` carried `gtm-os-demo/` to ignore the demo's output
folder, and the unanchored pattern also matched `skills/gtm-os-demo/`. The skill existed on
the author's disk, `validate_skills.py` passed there, and the pushed branch did not contain
it: every doc pointing users at "the gtm-os-demo skill" pointed at nothing.
`validate_skills.py` cannot see this, because it validates the files present, and a missing
file is not present.

So this compares the README's skill table (the claim) against git's index (what ships),
two different surfaces. Without a .git directory it falls back to the filesystem, which
still catches a skill that was never written.

To confirm it can fail: add an unanchored `gtm-os-demo/` line to .gitignore and run
`git rm --cached skills/gtm-os-demo/SKILL.md`.

Run: python3 -m unittest discover -s tests -v
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def listed_skills():
    """Skill names in README.md's `| `name` | ... |` table rows."""
    text = (ROOT / "README.md").read_text("utf-8")
    return sorted(set(re.findall(r"^\|\s*`([a-z0-9-]+)`\s*\|", text, re.M)))


def shipped():
    """Paths git tracks, or None when this is not a git checkout."""
    try:
        out = subprocess.run(["git", "ls-files", "skills"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return set(out.split())


class SkillsListedAreShipped(unittest.TestCase):
    def test_the_readme_table_is_parsed(self):
        self.assertIn("gtm-signal-scan", listed_skills())

    def test_every_listed_skill_is_shipped(self):
        tracked = shipped()
        for name in listed_skills():
            path = f"skills/{name}/SKILL.md"
            with self.subTest(skill=name):
                self.assertTrue((ROOT / path).exists(), f"{path} does not exist")
                if tracked is not None:
                    self.assertIn(path, tracked, f"{path} exists but git does not track it; "
                                  "check .gitignore (`git check-ignore -v " + path + "`)")

    def test_no_skill_file_is_ignored(self):
        """The direct form of the defect: nothing under skills/ may match an ignore rule."""
        files = [str(p.relative_to(ROOT)) for p in (ROOT / "skills").rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts]
        try:
            out = subprocess.run(["git", "check-ignore", "--no-index", *files], cwd=ROOT,
                                 capture_output=True, text=True)
        except OSError:
            self.skipTest("git is not available")
        self.assertEqual(out.stdout.split(), [], "files under skills/ match an ignore rule")


if __name__ == "__main__":
    unittest.main()
