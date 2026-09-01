"""Assert the documented check lists match what CI actually runs.

This test exists because the three lists drifted the moment CI gained a check.
`scan_secrets.py` and `check_workflow_script.py` were added to `ci.yml` in the
v1.5.0 PR, and neither was added to the PR template's checklist. Anyone working
that template would have ticked four boxes believing they had run everything CI
runs, while missing the two newest checks — including the credential scan.

A checklist that silently omits a check is the same failure this repo already
fixed twice: a check nobody runs and an audit that cannot fail. The fix is not to
be more careful, it is to make the drift fail the build.

Comparison is on the tool invoked, not the exact command string, so adding a flag
(`-v`, `--history`) does not fail the test. Adding or removing a check does.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
PR_TEMPLATE = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"


def canonical(text):
    """Reduce a blob of shell to the set of checks it invokes.

    Normalizes to the tool being run so flags and argument order do not matter:
    a repo script becomes its path, the test runner becomes "unittest", and the
    manifest check becomes "jq".
    """
    found = set()
    found.update(re.findall(r"scripts/[a-z_]+\.py", text))
    if re.search(r"\bunittest\b", text):
        found.add("unittest")
    if re.search(r"\bjq\b", text):
        found.add("jq")
    return found


def ci_checks():
    """Every check ci.yml runs, canonicalized."""
    return canonical(CI.read_text(encoding="utf-8"))


def claude_md_checks():
    """The checks listed in CLAUDE.md's PR-loop fenced block."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    # The loop's command block is the fenced bash block in the PR-loop section.
    section = text.split("## Shipping a change: the PR loop", 1)[-1]
    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
    return canonical("\n".join(blocks))


def pr_template_checks():
    """The checks listed under the PR template's "## Checks" heading."""
    text = PR_TEMPLATE.read_text(encoding="utf-8")
    section = text.split("## Checks", 1)[-1].split("\n## ", 1)[0]
    return canonical(section)


class DocumentedChecksMatchCI(unittest.TestCase):
    """CI is the source of truth; the docs must not understate it."""

    def test_ci_runs_something(self):
        """A guard on the parser itself: an empty CI set would pass everything."""
        self.assertGreaterEqual(len(ci_checks()), 4,
                                "parsed too few checks from ci.yml; the parser is wrong")

    def test_claude_md_lists_every_ci_check(self):
        """An agent following CLAUDE.md must run what CI will run."""
        missing = ci_checks() - claude_md_checks()
        self.assertEqual(missing, set(),
                         f"CLAUDE.md's PR loop omits CI checks: {sorted(missing)}")

    def test_pr_template_lists_every_ci_check(self):
        """This is the list that actually drifted, and how it was found."""
        missing = ci_checks() - pr_template_checks()
        self.assertEqual(missing, set(),
                         f"PR template omits CI checks: {sorted(missing)}")

    def test_docs_do_not_invent_checks_ci_does_not_run(self):
        """Drift in the other direction: a documented check nobody enforces."""
        for name, documented in (("CLAUDE.md", claude_md_checks()),
                                 ("PR template", pr_template_checks())):
            extra = {c for c in documented - ci_checks() if c.startswith("scripts/")}
            self.assertEqual(extra, set(),
                             f"{name} lists checks CI does not run: {sorted(extra)}")

    def test_every_documented_script_exists(self):
        """A checklist entry pointing at a deleted script is worse than none."""
        for check in claude_md_checks() | pr_template_checks():
            if check.startswith("scripts/"):
                self.assertTrue((REPO_ROOT / check).is_file(),
                                f"documented check {check} does not exist")


if __name__ == "__main__":
    unittest.main()
