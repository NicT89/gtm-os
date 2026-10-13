"""Guards on the GTM MCP connector block in examples/gtm-mcp/plugin-connector.json.

The block is merged into .claude-plugin/plugin.json when GTM MCP launches. Plugin userConfig
options are strict (an unknown key stops the plugin loading), and the key must travel in a
header from secure storage, never in a URL. These tests hold the block to both rules now,
so launch day is a copy, not a debugging session.

Run: python3 -m unittest discover -s tests -v
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCK = json.loads((ROOT / "examples/gtm-mcp/plugin-connector.json").read_text("utf-8"))
MANIFEST = json.loads((ROOT / ".claude-plugin/plugin.json").read_text("utf-8"))

# The userConfig option keys the plugin manifest reference documents
# (https://code.claude.com/docs/en/plugins-reference, "User configuration").
ALLOWED_OPTION_KEYS = {"type", "title", "description", "required", "default", "options",
                       "multiple", "sensitive", "min", "max"}


class TheBlock(unittest.TestCase):
    def test_user_config_options_use_only_documented_keys(self):
        for name, option in BLOCK["userConfig"].items():
            with self.subTest(name):
                self.assertTrue(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))
                self.assertLessEqual(set(option), ALLOWED_OPTION_KEYS)
                self.assertTrue({"title", "description"} <= set(option))

    def test_the_key_is_sensitive_and_sent_as_a_header(self):
        server = BLOCK["mcpServers"]["gtm-mcp"]
        header = server["headers"]["Authorization"]
        used = re.findall(r"\$\{user_config\.([A-Za-z0-9_]+)\}", header)
        self.assertEqual(len(used), 1)
        self.assertIs(BLOCK["userConfig"][used[0]]["sensitive"], True)

    def test_the_key_never_appears_in_the_url(self):
        self.assertNotIn("user_config", BLOCK["mcpServers"]["gtm-mcp"]["url"])
        self.assertNotIn("?", BLOCK["mcpServers"]["gtm-mcp"]["url"])


class NotShippedBeforeLaunch(unittest.TestCase):
    def test_the_manifest_declares_no_gtm_mcp_yet(self):
        """Until the server exists, shipping the connector would prompt every install for a
        key it cannot use. At launch, merge the block and delete this test in the same PR."""
        self.assertNotIn("gtm-mcp", json.dumps(MANIFEST.get("mcpServers", {})))
        self.assertNotIn("gtm_mcp_key", json.dumps(MANIFEST.get("userConfig", {})))


if __name__ == "__main__":
    unittest.main()
