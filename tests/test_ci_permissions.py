"""Assert ci.yml gives its token read-only access to contents and nothing more.

Without a top-level `permissions:` block, every job gets the repository's default
token permissions, which can include write access. ci.yml only checks out code and
runs local scripts, so a token that can push is pure exposure: one compromised
action in the chain and it can write to the repo. CodeRabbit's zizmor pass flagged
the missing block on NicT89/gtm-os#23.

release.yml is deliberately out of scope: it needs `contents: write` to tag,
publish, and push its sync commit.

The check reads every `permissions:` block in the file, top-level and job-level,
since a job's own block applies to that job whatever the top level says.
`ReadOnlyScanner` proves on in-memory copies that a missing block, any write, any
extra read scope, `read-all`, `write-all` and the inline `{ scope: level }` form
each fail, at either level.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


POLICY = {"contents": "read"}


def permission_blocks(text):
    """Every `permissions:` key in a workflow, as (line_no, indent, grant).

    `grant` is a {scope: level} dict for the block form, or the raw string for the
    scalar and flow forms (`read-all`, `write-all`, `{}`, `{ issues: read }`).
    Top-level and job-level blocks are both returned: GitHub applies a job's own
    block to that job, so a job can widen the token whatever the top level says.
    """
    lines = text.split("\n")
    found = []
    for i, line in enumerate(lines):
        m = re.match(r"^(?P<indent>[ ]*)permissions:\s*(?P<value>[^#]*?)\s*(#.*)?$", line)
        if not m:
            continue
        indent = len(m.group("indent"))
        if m.group("value"):
            found.append((i + 1, indent, m.group("value")))
            continue
        grant = {}
        for body in lines[i + 1:]:
            if not body.strip() or body.strip().startswith("#"):
                continue
            entry = re.match(r"^(?P<indent>[ ]*)([a-z-]+):\s*(\S+)\s*(#.*)?$", body)
            if not entry or len(entry.group("indent")) <= indent:
                break
            grant[entry.group(2)] = entry.group(3)
        found.append((i + 1, indent, grant))
    return found


def problems(text):
    """Every way the file's token permissions differ from contents: read.

    The top-level block must exist and equal the policy. Any other block (a job's)
    may only restate the policy or grant nothing (`{}`); anything else, a read
    scope included, widens that job's token and fails.
    """
    blocks = permission_blocks(text)
    top = [b for b in blocks if b[1] == 0]
    if not top:
        return ["no top-level permissions block"]
    out = []
    for line_no, indent, grant in blocks:
        where = "top-level" if indent == 0 else f"line {line_no} (job-level)"
        if grant == POLICY or (indent > 0 and grant == "{}"):
            continue
        out.append(f"{where} permissions are {grant!r}, expected {POLICY!r}")
    return out


class ReadOnlyScanner(unittest.TestCase):
    """The scanner must catch each widening, or the repo assertion below is vacuous."""

    GOOD = "on:\n  push:\n\npermissions:\n  contents: read\n\njobs:\n  a:\n    steps: []\n"

    def test_the_good_shape_passes(self):
        """contents: read at the top and nothing else is the policy."""
        self.assertEqual(problems(self.GOOD), [])

    def test_missing_block_fails(self):
        """No block means the repo's default token permissions."""
        self.assertTrue(problems(self.GOOD.replace("permissions:\n  contents: read\n", "")))

    def test_write_grant_fails(self):
        """contents: write at the top fails."""
        self.assertTrue(problems(self.GOOD.replace("contents: read", "contents: write")))

    def test_write_all_fails(self):
        """The scalar write-all form fails."""
        self.assertTrue(problems(self.GOOD.replace("permissions:\n  contents: read",
                                                   "permissions: write-all")))

    def test_extra_scope_fails(self):
        """A second scope at the top fails, even a read one."""
        self.assertTrue(problems(self.GOOD.replace("contents: read",
                                                   "contents: read\n  issues: read")))

    def test_job_level_write_fails(self):
        """A job's own block can widen its token past the top level."""
        widened = self.GOOD + "    permissions:\n      pull-requests: write\n"
        self.assertTrue(problems(widened))

    def test_job_level_read_scope_fails(self):
        """Read is still wider than the policy: found by CodeRabbit on PR 27."""
        widened = self.GOOD + "    permissions:\n      issues: read\n"
        self.assertTrue(problems(widened))

    def test_job_level_read_all_fails(self):
        """The scalar form grants every read scope."""
        self.assertTrue(problems(self.GOOD + "    permissions: read-all\n"))

    def test_job_level_flow_mapping_fails(self):
        """The inline `{ scope: level }` form is checked, not skipped."""
        self.assertTrue(problems(self.GOOD + "    permissions: { issues: read }\n"))

    def test_job_level_empty_grant_passes(self):
        """`{}` grants nothing, which is narrower than the policy."""
        self.assertEqual(problems(self.GOOD + "    permissions: {}\n"), [])

    def test_job_level_restating_the_policy_passes(self):
        """A job that repeats contents: read widens nothing."""
        self.assertEqual(problems(self.GOOD + "    permissions:\n      contents: read\n"), [])


class CiTokenIsReadOnly(unittest.TestCase):
    """The assertion that matters: ci.yml as shipped."""

    def test_ci_yml_is_contents_read_only(self):
        """The real ci.yml matches the policy at every level."""
        found = problems(CI.read_text("utf-8"))
        self.assertEqual(found, [], "ci.yml token permissions widened: " + "; ".join(found))


if __name__ == "__main__":
    unittest.main()
