# Security

GTM OS is a plugin that runs with the user's own connector credentials and writes into
the user's own CRM and bases. Its security surface is therefore mostly what it can be made
to write, and what it could leak from one instance to the public repo.

## Report privately

Email **nthatcher@realblockai.com** with "GTM OS security" in the subject. Do not open a
public issue for any of these:

- A credential, token or key anywhere in this repository or its history.
- A resolved instance value (an Apollo, Airtable or HubSpot ID, a portal number, a
  customer or prospect name) in this repository, in an example, or in an issue someone
  else filed.
- A skill, script or workflow that can be made to write outside the records it was asked
  to touch, send a message without the pre-send review gate, spend credits without the
  credit-spend gate, or edit a human-managed asset.
- A redaction gap: a value that `scripts/scan_secrets.py`, `scripts/setup_feedback.py`
  or `scripts/feedback.py` should have stripped and did not.
- Prompt injection: content fetched from the web or a CRM record that a skill then obeys
  as an instruction.

Say what you found, where, and how to reproduce it with synthetic values. You will get a
reply within five business days, and the fix ships as a patch release that every fork or
private copy receives through its upstream sync.

## What is in scope

The files in this repository and the behavior of the skills and scripts they define,
when installed as the plugin. Not in scope: the vendors' own MCP servers (Apollo, HubSpot,
Airtable, Apify, Firecrawl, Brand Kit OS), which are declared in `.mcp.json` but operated
by their vendors, and any change a fork has made to its own copy.

## What the repo does to protect itself

- No credential is ever stored: every connector in `.mcp.json` is the vendor's own OAuth
  server, and `tests/test_plugin_connectors.py` fails if a key or header appears there.
- `scripts/scan_secrets.py` runs in CI against the tree and, before each release, against
  the full history (`--history`).
- Every deployment value in a skill is a `{KEY}` resolved from an `instance-config.json`
  that is gitignored here and lives only in the user's workspace.
- Outbound reports (`setup_feedback.py`, `feedback.py`) strip IDs, emails, credentials
  and private links, show the result, and file only a body the user has seen, bound by a
  digest token.
