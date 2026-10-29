# HubSpot reverse-ICP lookup (blueprint)

How to read a customer's existing customer base out of their HubSpot through the HubSpot MCP and turn it into customer profiles for the reverse ICP (`pmf-five-gate-playbook`, step 1). Tested end to end on a live portal on 2026-10-09; the observations below are from that run. This file holds no portal IDs, customer names or run output, by design (CLAUDE.md: nothing from an instance goes in this repo).

## Install-time question

When GTM OS is first connected to a user's Claude environment, ask once:

> Do you use HubSpot as your CRM? If yes, connect the HubSpot connector now so I can read your current customers and fill in your ideal customer profile from them. This step only reads.

- Yes and connected: run the lookup below.
- Yes but not connected: route to `environment-setup`; do not improvise another path. Not set up does not mean not owned.
- No, or the user declines: use the fallback (website logos) and say so in the report.

## Tool calls, in order (all read-only)

Tools are deferred in some clients: load them first with a single ToolSearch `select:` call naming all of them.

| Step | Tool and input | What it returns and what to check |
|---|---|---|
| 1. Identity and access | `get_user_details` with `include: ["USER_INFORMATION","TOOL_INFORMATION"]` | account ID, owner ID, and per object type `read` and `write` availability. Require `read: AVAILABLE` on COMPANY, DEAL, CONTACT. Record any `REQUIRES_REAUTHORIZATION` or `REQUIRES_PERMISSION_MODIFICATION` for the user; a write status does not block this lookup |
| 2. Pipelines | `discover_hubspot_schema` with `query: {"_queryType":"GET_PIPELINES","objectType":"DEAL"}` | every pipeline and stage with a win probability. Closed-won stages are the ones with probability 1.0; closed-lost 0.0. Stage IDs are portal-specific: never hard-code `closedwon` for a portal you have not read |
| 3. Property discovery | `search_properties` with `objectType` and up to 5 `keywords`; `get_properties` for enumeration options | which standard fields exist and which custom fields the portal added (search keywords such as `icp`, `segment`, `plan`, `source`, `tier`). Custom properties often hold the best ICP signal |
| 4. Customer set | `search_crm_objects` as below | the customers, with `total` so paging is complete |
| 5. Buyer roles | `search_crm_objects` on CONTACT with `associatedWith` the companies | job titles of contacts associated to won deals: evidence for who buys |
| 6. Aggregates (optional) | `query_crm_data` with SQL | counts and sums by industry or size band |

### Step 4: choose the customer set, best source first

1. **Won deals.** `search_crm_objects`, `objectType: "DEAL"`, filter `dealstage IN [closed-won stage IDs from step 2]`, properties `dealname, amount, deal_currency_code, closedate, createdate, dealtype, dealstage, pipeline, closed_won_reason, hubspot_owner_id`. Then fetch each deal's company with `associatedWith`.
2. **Customer companies.** `objectType: "COMPANY"`, filter `lifecyclestage EQ customer`, properties `name, domain, industry, numberofemployees, annualrevenue, city, state, country, hs_ideal_customer_profile, lifecyclestage, createdate, num_associated_deals, hs_total_deal_value`.
3. **Open deals as seeds.** A deal that is not closed can be included as a `seed` when the owner says to treat it as part of the ICP. Mark it `seed`, weight it below won customers, and exclude it from conversion metrics.

Always read `total` and page with `offset` until every record is read. Never substitute a sample for the set. Currency: request `deal_currency_code` with `amount`; never sum raw amounts across currencies; for aggregates use `amount_in_home_currency`.

### Field mapping to the ICP card

| HubSpot field | ICP card field | Note |
|---|---|---|
| `industry` (enumeration, about 150 values) | category, sub_category | map the enumeration label, keep the raw value |
| `numberofemployees` | employee_min / employee_max, company_size | store the number; derive the band |
| `annualrevenue` | revenue_range | often empty: leave unscored, do not infer |
| `country`, `state`, `city` | geography, hq_country, hq_state | |
| `hs_ideal_customer_profile` (tier_1 to tier_3) | the owner's own fit rating | compare it with the computed overlap; disagreement is a finding |
| contact `jobtitle` on won deals | decision_makers | role that paid versus role that approved needs the interview |
| `closed_won_reason` | buying_triggers, pain_points | free text, quote person-neutrally |
| `closedate` | cohort | split before and after any pricing change |
| `dealtype` | new versus existing business | |

Fields HubSpot cannot answer (objections, signals, anti-ICP, usage) come from interviews and product data. Mark each profile field with its source.

## Writing a record (test run, for operators and for onboarding a sandbox)

`manage_crm_objects` creates and updates. Its own rules apply and stay on: check write availability first (step 1), show the proposed values in a table, and get explicit approval before every write.

```json
{"confirmationStatus":"CONFIRMED",
 "createRequest":{"objects":[{"objectType":"DEAL",
   "properties":{"dealname":"<Company> | <Offer>","pipeline":"<pipeline id>","dealstage":"<stage id>","dealtype":"newbusiness",
     "hs_priority":"high","amount":"<number>","deal_currency_code":"USD","closedate":"YYYY-MM-DD",
     "hubspot_owner_id":"<owner id>","hs_next_step":"<text>","description":"<text>"},
   "associations":[{"targetObjectId":"<company id>","targetObjectType":"COMPANY"},{"targetObjectId":"<contact id>","targetObjectType":"CONTACT"}]}]}}
```

Create the company and contact first (one call can create both), then the deal with associations. Then read back with `get_crm_objects` and compare every value. Observed behavior:

- The create response returns an empty `properties` object. It is not proof of storage. Read the record back.
- `hs_mrr` and `hs_arr` are calculated properties: writing them fails the whole create ("cannot be set"). They derive from recurring line items or subscriptions. To record a monthly price without line items, put it in `amount` (state the basis in `description`) and say so in the run notes.
- `amount` is one free number with no term. Decide the convention per portal (one month, annualized, or contract total) and write it in the description; do not mix conventions across deals.
- `closedate` is stored as midnight UTC of the date given.
- Enumerations take the internal value (`COMPUTER_SOFTWARE`, `tier_1`, `qualifiedtobuy`), not the label.
- When a create fails validation the tool instructs not to retry with partial properties and to surface the error. Remove only properties the error names as non-writable, tell the user exactly which, and keep every other approved value.
- Deal stage probability is set by the pipeline stage, not by the writer.
- `query_crm_data` takes one object type per query; cross-object columns use `OBJECT.property`; an empty dataset returns a message, not an error.
- A portal with no closed-won deals and no `customer` companies returns `total: 0`. That is a valid result: use the fallback and say the CRM held no customers.

## Fallback: logos from the customer's website

Use when HubSpot is absent, unreachable or empty. Good enough to build a first reverse ICP; weaker evidence.

1. Scrape the customer's home, customers, case-studies and pricing pages (`references/scraping-playbook.md`); collect logo names and any named case studies.
2. Resolve each name to a company domain; enrich size, industry, geography with the enrichment tool the user has (Apollo organizations enrich, or the Firecrawl search).
3. Mark every profile `source: site-logos`. A logo wall is not confirmation of a current contract, and logo counts disagree with customer counts stated on calls: record both and flag the conflict.
4. Treat the result as lower confidence than a CRM read, and schedule the customer interviews to confirm which logos are active paying customers.

## Output

Customer profiles in Brand Kit OS (`create_customer_profile`, preview before write), an overlap table (`pmf-five-gate-playbook/references/gate-scorecard.md`), and the source of the customer set stated in the report: `crm`, `crm+seed`, or `site-logos`. The run record (counts, IDs, dates) stays in the engagement's own storage, never in this repo.
