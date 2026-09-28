"""Assert every GitHub Actions job runs on public repositories only.

GitHub-hosted runners are free on public repositories and metered on private ones.
This repo is public on the maintainer's personal account, where Actions cost nothing.
The workflows must not start spending if they are ever copied into a private
repository, such as one in a paid organization. So every job carries the guard
`if: ${{ !github.event.repository.private }}`, which skips the job there.

A guard that one new job forgets is a bill nobody notices until it arrives, so the
check is per job, not per file: a file where two jobs are guarded and a third is not
fails.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
GUARD = re.compile(r"^\s*if:\s*\$\{\{\s*!\s*github\.event\.repository\.private\s*\}\}\s*$")


def jobs(text):
    """{job name: [lines of that job's body]} for a workflow file's `jobs:` block."""
    lines = text.split("\n")
    try:
        start = lines.index("jobs:")
    except ValueError:
        return {}
    found, current = {}, None
    for line in lines[start + 1:]:
        if line and not line.startswith(" "):
            break  # the next top-level key ends the jobs block
        name = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if name:
            current = name.group(1)
            found[current] = []
        elif current and line.startswith("    "):
            found[current].append(line)
    return found


def unguarded(text):
    """Names of jobs whose own top-level keys do not include the public-only guard."""
    missing = []
    for name, body in jobs(text).items():
        own_keys = [ln for ln in body if re.match(r"^    [A-Za-z]", ln)]
        if not any(GUARD.match(ln) for ln in own_keys):
            missing.append(name)
    return missing


class WorkflowsArePublicOnly(unittest.TestCase):
    def test_every_job_is_guarded(self):
        files = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
        self.assertTrue(files, "no workflow files found")
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(jobs(text), f"{path.name}: no jobs parsed")
            self.assertEqual(unguarded(text), [], f"{path.name}: jobs without the guard")

    def test_an_unguarded_job_is_caught(self):
        text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        stripped = text.replace("    if: ${{ !github.event.repository.private }}\n", "", 1)
        self.assertNotEqual(stripped, text, "guard not found to remove")
        self.assertEqual(len(unguarded(stripped)), 1)

    def test_a_guard_on_a_step_does_not_count(self):
        text = (
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - name: x\n"
            "        if: ${{ !github.event.repository.private }}\n"
            "        run: echo\n"
        )
        self.assertEqual(unguarded(text), ["build"])


if __name__ == "__main__":
    unittest.main()
