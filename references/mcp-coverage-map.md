# MCP Coverage Map

The integration-layer decision table for GTM stacks. Any provisioning or architecture engagement starts by intersecting the client's tool stack with this map. MCP availability changes monthly: every row carries a verified date, and a row older than a quarter gets re-verified before it is cited to a client.

## Decision rule

- **MCP for agent workflows** (Claude reading, deciding, writing single records).
- **API for bulk data movement** (warehouse sync, backfills, webhooks); n8n is the default transport.
- **The warehouse stays queryable** (over MCP) rather than syncing everything into the CRM; the CRM gets the operational subset (scores, summaries), the warehouse remains the analytical source of truth.

## Coverage table

"Used in production" means a deployment of this engine has exercised the connector end to end, not that the vendor claims support.

| Tool | Status (verified) | Path |
|---|---|---|
| Salesforce | Official MCP support, hosted server (2026-08) | MCP for agents; Bulk/REST API for sync |
| HubSpot | Official MCP (2026-08, used in production) | MCP |
| Apollo | Official MCP (2026-08, used in production) | MCP |
| Clay | Official MCP (2026-08, used in production) | MCP |
| Slack | Official MCP (2026-08, used in production) | MCP |
| Supabase | Official MCP (2026-08, used in production) | MCP |
| Airtable | Official MCP (2026-08, used in production) | MCP |
| n8n | MCP server + MCP client nodes; also an MCP host (2026-08) | MCP plus native nodes |
| BigQuery | Google MCP Toolbox for Databases + managed remote BigQuery MCP server (2026-08) | MCP for agent queries; scheduled SQL for pipelines |
| Zapier | Zapier MCP, thousands of actions (2026-08) | MCP; prefer n8n for stateful flows |
| Lovable | Official MCP (2026-08, used in production) | MCP for micro-app builds |
| Firecrawl | Official MCP (2026-08, used in production) | MCP |
| Apify | Official MCP (2026-08, used in production) | MCP |
| Google Workspace (Gmail/Drive/Calendar) | Official MCPs (2026-08, used in production) | MCP |
| Metabase | No official MCP; REST API; community servers unvetted (2026-08) | API |
| Qualified | No MCP; REST API + webhooks (2026-08) | API via n8n |
| NetSuite | No official MCP; SuiteTalk/REST (2026-08) | API via n8n, read-mostly |
| Gainsight | Not verified; check before citing | Verify |
| OpenAI / Gemini | Model APIs, not MCP targets | Direct API inside workflows |

## Maintenance

When a run discovers a coverage change (new official server, deprecation, auth change), update the row, refresh the date, and log the observation in `references/dependency-observations.md`.
