"""Pin the ways the version-sync check is supposed to fail.

Per CLAUDE.md, a new check earns trust by being broken on purpose and observed failing.
So these tests do not merely assert that the repo currently passes — they rewrite VERSION
and plugin.json in a temporary copy and assert each disagreement is caught. A check that
only ever passes is the failure mode this repo has shipped four times.

Run: python3 -m unittest discover -s tests -v
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_version_sync.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_version_sync import check  # noqa: E402


class SandboxedRepo:
    """A throwaway copy of the two files the check reads, plus the script itself."""

    def __init__(self, version, plugin_version):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "scripts").mkdir()
        (self.dir / ".claude-plugin").mkdir()
        shutil.copy(SCRIPT, self.dir / "scripts" / SCRIPT.name)
        (self.dir / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (self.dir / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "gtm-os", "version": plugin_version}, indent=2),
            encoding="utf-8")

    def run(self):
        return subprocess.run(
            [sys.executable, str(self.dir / "scripts" / SCRIPT.name), "--json"],
            capture_output=True, text=True)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class TheRepoItselfPasses(unittest.TestCase):
    """The live check, which is what CI runs."""

    def test_this_repo_is_in_sync(self):
        problems = check()
        self.assertEqual(problems, [], f"VERSION and plugin.json disagree: {problems}")


class ItCatchesEachWayTheyCanDisagree(unittest.TestCase):
    """Break it on purpose; watch it fail. This is the point of the file."""

    def assert_verdict(self, version, plugin_version, expected):
        repo = SandboxedRepo(version, plugin_version)
        try:
            proc = repo.run()
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["verdict"], expected,
                             f"VERSION={version} plugin={plugin_version}: {payload}")
            self.assertEqual(proc.returncode, 0 if expected == "PASS" else 1)
        finally:
            repo.cleanup()

    def test_matching_versions_pass(self):
        """The guard on the guard: if this fails, every FAIL case below proves nothing."""
        self.assert_verdict("1.7.1", "1.7.1", "PASS")

    def test_a_stale_plugin_json_fails(self):
        """The common case: VERSION bumped, manifest forgotten."""
        self.assert_verdict("1.7.1", "1.7.0", "FAIL")

    def test_a_stale_version_file_fails(self):
        """The older trap: editing only the manifest used to do nothing, silently."""
        self.assert_verdict("1.7.0", "1.7.1", "FAIL")

    def test_a_non_semver_version_fails(self):
        self.assert_verdict("latest", "latest", "FAIL")

    def test_a_prerelease_suffix_mismatch_fails(self):
        self.assert_verdict("1.7.1", "1.7.1-rc1", "FAIL")


class ItFailsLoudlyOnBrokenInputs(unittest.TestCase):
    """A missing or malformed file must fail, never pass by default."""

    def test_a_missing_version_field_fails(self):
        repo = SandboxedRepo("1.7.1", "1.7.1")
        try:
            (repo.dir / ".claude-plugin" / "plugin.json").write_text(
                json.dumps({"name": "gtm-os"}), encoding="utf-8")
            proc = repo.run()
            self.assertEqual(proc.returncode, 1)
            self.assertIn("no `version` field", proc.stdout)
        finally:
            repo.cleanup()

    def test_unparseable_plugin_json_fails(self):
        repo = SandboxedRepo("1.7.1", "1.7.1")
        try:
            (repo.dir / ".claude-plugin" / "plugin.json").write_text("{", encoding="utf-8")
            proc = repo.run()
            self.assertEqual(proc.returncode, 1)
            self.assertIn("does not parse", proc.stdout)
        finally:
            repo.cleanup()

    def test_a_missing_version_file_fails(self):
        repo = SandboxedRepo("1.7.1", "1.7.1")
        try:
            (repo.dir / "VERSION").unlink()
            proc = repo.run()
            self.assertEqual(proc.returncode, 1)
        finally:
            repo.cleanup()


if __name__ == "__main__":
    unittest.main()
