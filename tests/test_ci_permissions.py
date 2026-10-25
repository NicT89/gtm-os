"""Assert ci.yml gives its token read-only access to contents and nothing more.

Without a top-level `permissions:` block, every job gets the repository's default
token permissions, which can include write access. ci.yml only checks out code and
runs local scripts, so a token that can push is pure exposure: one compromised
action in the chain and it can write to the repo. CodeRabbit's zizmor pass flagged
the missing block on NicT89/gtm-os#23.

release.yml is deliberately out of scope: it needs `contents: write` to tag,
publish, and push its sync commit.

The check reads the workflow's own top-level block and every job's block, and
`ReadOnlyScanner` proves on in-memory copies that a missing block, a write grant,
and `write-all` each fail.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def top_level_permissions(text):
    """{scope: level} from the top-level `permissions:` block, or None if absent.

    A scalar form (`permissions: write-all`) returns {"*": "write-all"}.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^permissions:\s*(\S*)\s*$", line)
        if not m:
            continue
        if m.group(1):
            return {"*": m.group(1)}
        found = {}
        for body in lines[i + 1:]:
            if body.strip().startswith("#") or not body.strip():
                continue
            entry = re.match(r"^  ([a-z-]+):\s*(\S+)\s*$", body)
            if not entry:
                break
            found[entry.group(1)] = entry.group(2)
        return found
    return None


def problems(text):
    """Every way the file's token permissions exceed contents: read."""
    perms = top_level_permissions(text)
    if perms is None:
        return ["no top-level permissions block"]
    out = []
    if perms != {"contents": "read"}:
        out.append(f"top-level permissions are {perms}, expected {{'contents': 'read'}}")
    for line in text.split("\n"):
        if re.search(r"\b(write|write-all)\b", line.split("#", 1)[0]) and ":" in line:
            out.append(f"write grant: {line.strip()}")
    return out


class ReadOnlyScanner(unittest.TestCase):
    """The scanner must catch each widening, or the repo assertion below is vacuous."""

    GOOD = "on:\n  push:\n\npermissions:\n  contents: read\n\njobs:\n  a:\n    steps: []\n"

    def test_the_good_shape_passes(self):
        self.assertEqual(problems(self.GOOD), [])

    def test_missing_block_fails(self):
        self.assertTrue(problems(self.GOOD.replace("permissions:\n  contents: read\n", "")))

    def test_write_grant_fails(self):
        self.assertTrue(problems(self.GOOD.replace("contents: read", "contents: write")))

    def test_write_all_fails(self):
        self.assertTrue(problems(self.GOOD.replace("permissions:\n  contents: read",
                                                   "permissions: write-all")))

    def test_extra_scope_fails(self):
        self.assertTrue(problems(self.GOOD.replace("contents: read",
                                                   "contents: read\n  issues: read")))

    def test_job_level_write_fails(self):
        widened = self.GOOD + "    permissions:\n      pull-requests: write\n"
        self.assertTrue(problems(widened))


class CiTokenIsReadOnly(unittest.TestCase):
    def test_ci_yml_is_contents_read_only(self):
        found = problems(CI.read_text("utf-8"))
        self.assertEqual(found, [], "ci.yml token permissions widened: " + "; ".join(found))


if __name__ == "__main__":
    unittest.main()
