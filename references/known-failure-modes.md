# Known failure modes

Every row here was found the expensive way. The register exists so the next person finds it the
cheap way.

**The pattern that repeats:** a provider field looks authoritative, is wrong in a consistent
direction, and fails silently. Not one of these throws an error. Each returns a well-formed
answer that happens to be false, which is why they survived so long — a wrong answer and a
right answer are the same shape.

**Direction matters more than the defect.** A field that *under*-reports and a field that
*over*-reports need opposite compensations, and knowing which way a tool leans is most of
knowing how to use it. `UNDER` = says no when the answer is yes. `OVER` = says yes when the
answer is no. `STALE` = was true once.

---

| # | Where | Direction | What actually happens | How to detect it, cheaply |
|---|---|---|---|---|
| 1 | Provider freshness timestamp on a person record | STALE | The timestamp records when the vendor last wrote the row, not when anyone verified it. A record stamped today carried a job title six months out of date, while the CRM's own copy was newer than the index it came from. | Compare against the person's own dated statements — an announcement post beats an index entry. Treat a searched title as a hypothesis. |
| 2 | Title-similarity flag on people search | OVER | Defaults to TRUE. A query for three specific "Founding <commercial>" titles returned Founding Engineer, Founding SWE and Founding Software Engineer. A qualification field set from this marks a company as having staff in a function nobody there works in. | Set it to false whenever the result decides a field. Fuzzy is for prospecting only. |
| 3 | Job-posting index | UNDER | Not a complete record of a company's postings. Returned zero go-to-market postings for a company whose own record in our instance listed one across six URLs that we had scraped ourselves. | Check our own scraped posting fields first, then the company's ATS, then the index. A zero means unindexed, not absent. |
| 4 | Cached record count on a list write | STALE | The count returned by an add/remove call is not recomputed. Removing nine contacts returned the pre-removal count. | Read the list back. Never report a count from a write response. |
| 5 | List names passed to bulk contact creation | UNDER | Silently ignored. Every created contact came back with an empty label set and the call reported success. | Add to lists in a separate call, then read `label_ids` on the record. |
| 6 | Any asynchronous enrichment workflow | UNDER | Workflow-fired success is not field population. Records sat in a cascade for weeks with the trigger satisfied and the output field empty. | Verify by reading the OUTPUT field, never by asking whether the workflow ran. |
| 7 | Any filtered search returning zero | UNDER | A zero result and a silently-ignored filter are byte-identical. | Run the same query once with a value nothing could match. If that also returns zero, the filter constrains and the real zero is trustworthy. |
| 8 | Stored employment vs the provider's own job-change event | STALE | The event sits on the contact payload and nothing reads it. A record still naming an old employer and an old function reached an enrollment list three days after the provider reported the move. | Read the job-change event before enrolling. Fold cosmetic spelling first, or a hyphen reads as a job change. |
| 9 | Seniority-filtered people search | OVER | Reads "Founding <anything>" as founder-level. One company returned five c-suite matches, all individual contributors. | Treat "Founding <commercial function>" as an IC. Never conclude seniority from this filter alone. |
| 10 | Title-filtered people search | UNDER | Misses "Founding <function>" staff entirely. Returned zero go-to-market people at two companies that both had them. | Run title AND seniority shapes, read together. Neither is safe alone, and they fail in opposite directions. |
| 11 | Post-scraper returning implausibly fast | UNDER | A run finishing in ~4 seconds has almost certainly misfired rather than found nothing. A real multi-profile run takes ~7s and returns dozens of items. | Check runtime and item count together. Retry a zero once before believing it. |
| 12 | AI field whose prompt references an unresolvable variable | — | Fails on EVERY write to the record, not once at generation time, so it appears in responses to unrelated updates long after the cause and trains everyone to skim past it. Neighbouring fields populate normally, so the record looks healthy. | Read the error block on write responses. Populating the referenced field does not necessarily clear it — the prompt itself may need fixing where the API cannot reach. |
| 13 | Bulk record creation | UNDER | Reports success after step one of four. Creation is not list membership, is not enrichment, and is not post capture. | Treat a created record as incomplete until its output fields are populated. |

---

## How to use this

**Before trusting any single field that decides a route**, check whether its source appears
above. If it does, apply the compensation in the last column — all of them are free.

**When a new defect is found, add a row.** The required shape is: where, direction, what
actually happens with the observed evidence, and a detection method that costs nothing. A row
without a detection method is a complaint, not an entry, and `scripts/check_failure_register.py`
will reject it.

**The asymmetry that justifies the whole register:** verification here is free and a bad send
costs a sending domain. That ratio means the right posture is cheap systematic doubt rather
than calibrated trust — the goal is not to trust tooling more, it is to make distrust so cheap
that trust stops being the question.
