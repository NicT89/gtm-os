# GTM MCP: the hosted service GTM OS runs on

GTM OS is two parts. This plugin is the open part: the skills, the human gates, connector
setup, and the data contracts your own systems have to match. **GTM MCP** is the hosted part,
run by Launch99: the scraping service, the scoring and ranking engine, persona scores, the
learning loop's analysis, and the link to your brand kit in Brand Kit OS. You connect to it
the way you connect to any other MCP server.

This file is the plugin's side of that boundary: what GTM MCP is for, how you connect, what
it keeps, and what happens without it. It does not describe how the service works inside;
that is not part of the plugin.

## Status

GTM MCP is not live yet. Until it is, everything in this plugin keeps running as it did in
1.11.0: scoring and ranking run locally from `skills/gtm-signal-scan/scripts/`, scraping runs
on your own Apify and Firecrawl connectors, and the offline demo needs no key. When it
launches, a release adds the connector to the plugin manifest and says so in the changelog.

## What it does for you

| Capability | Returns | What you still own |
|---|---|---|
| Scraping (LinkedIn posts and comments, web pages) | Rows that match the posts base 1:1 (`references/scrape-delivery.md`) | Where they are stored. Your Airtable connector writes them; GTM MCP never does |
| Account scoring and people ranking | Scores, tiers and a spend list, with every unknown input flagged | The scoring config and plays file that define what counts |
| Persona scores | A score per contact and a persona-coverage view per company (`references/persona-scores.md`) | Your persona definitions, written in your own words |
| Learning-loop analysis | Proposed changes with their evidence, never applied (`references/outcomes.md`) | Every decision to change anything |
| Brand kit context | Your seller-side voice and positioning, read from Brand Kit OS | Your brand kit itself |

## Connecting

Access is by a key issued during GTM OS onboarding. It is yours alone and identifies your
organization to the service.

- **In Claude Code**, the plugin asks for the key once, when it is enabled, and stores it in
  your system keychain. It is sent as an `Authorization` header on every call and never
  written to a file. The exact connector block is in `examples/gtm-mcp/plugin-connector.json`.
- **Never put the key in a URL.** URLs end up in logs, and the MCP specification forbids
  tokens in the query string.
- **claude.ai web, the Desktop chat app and Cowork** accept a static header on a custom
  connector only in a limited beta, and on Team and Enterprise plans one key is shared by
  the whole organization. Claude Code is the supported surface for GTM OS.

## Your identity references

Three keys in your `instance-config.json` hold copies of your onboarding identifiers, so your
agent knows which records are yours:

- `{GTM_ORG_ID}`: your organization in the GTM MCP.
- `{GTM_MCP_CUSTOMER_ID}`: your GTM MCP account.
- `{BRAND_KIT_OS_ID}`: the brand kit GTM MCP reads for you.

**They are references, not credentials.** The service decides who you are from the key
alone and looks up your brand kit itself; it never acts on an id sent in a request. Editing
these values changes what your agent believes, not what the service will return.

## What GTM MCP keeps

Stated here because you should know before you connect, not after:

- your account, organization and key (the key stored hashed);
- a log of your calls to the service;
- a copy of the data it scrapes for you, kept for auditing and to understand how you use
  the service;
- business context about your organization gathered while serving you.

It holds **none of your credentials**: not for Airtable, Apollo or HubSpot. Every write to
your systems goes through your own connectors.

## What works without it, once it is live

| Without GTM MCP | Effect |
|---|---|
| Scraping | Unavailable through GTM OS. The posts base keeps what it has |
| Scoring, ranking, persona scores | Unavailable. The scan stops at play assignment and says so |
| Learning loop | Outcomes are still recorded to your CRM; no proposals are made |
| Everything else | Unchanged: the gates, blueprints, audits and setup all run |

The offline demo (`gtm-os-demo`) always runs without a key: it is how you see the engine
before you have one.
