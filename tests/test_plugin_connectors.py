"""Guards on .mcp.json, the connectors the plugin declares for its Connectors tab.

Every entry must be a remote HTTP server at the vendor's own host with no credential in
the file: a key in a URL or header would ship to every installed copy. The set of hosts
is the engine's Native and Generic platforms from references/platform-support.md; a new
connector is added here and in that file together.

Run: python3 -m unittest discover -s tests -v
"""
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MCP = json.loads((ROOT / ".mcp.json").read_text("utf-8"))

EXPECTED_HOSTS = {
    "apollo": "mcp.apollo.io",
    "hubspot": "mcp.hubspot.com",
    "airtable": "mcp.airtable.com",
    "apify": "mcp.apify.com",
    "firecrawl": "mcp.firecrawl.dev",
}


class Connectors(unittest.TestCase):
    def test_every_required_connector_is_declared(self):
        self.assertEqual(set(EXPECTED_HOSTS), set(MCP["mcpServers"]))

    def test_each_is_remote_http_at_the_vendor_host(self):
        for name, server in MCP["mcpServers"].items():
            with self.subTest(name):
                self.assertEqual(server.get("type"), "http")
                url = urlparse(server["url"])
                self.assertEqual(url.scheme, "https")
                self.assertEqual(url.hostname, EXPECTED_HOSTS[name])

    def test_no_credential_travels_in_the_file(self):
        for name, server in MCP["mcpServers"].items():
            with self.subTest(name):
                self.assertNotIn("headers", server)
                self.assertNotIn("?", server["url"])
                self.assertNotIn("user_config", json.dumps(server))
        self.assertNotIn("userConfig", MCP)

    def test_gtm_mcp_is_still_not_shipped(self):
        self.assertNotIn("gtm-mcp", MCP["mcpServers"])


if __name__ == "__main__":
    unittest.main()
