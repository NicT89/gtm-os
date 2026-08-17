# Apollo credit costs and the score-before-you-reveal rule

Canonical cost table for the engine. Every skill that spends cites this file rather
than restating numbers inline, so there is one place to correct when Apollo changes
its pricing or the account changes plan.

## The rule that matters most

**Search is free. Reveals are not. So rank the whole field for free, then pay only
for the people you actually want.**

People search returns `email_status` and phone-availability *flags* without returning
the email or phone itself, and without charging. That is enough to know who is
reachable before spending anything. The engine's default failure mode is paying to
enrich a contact whose email turns out to be catch-all or unavailable — money spent
to learn the contact was never sendable.

Rank on the flags first, spend second. See "Reachability tiers" below.

## Cost table

| Action | Cost | What you get |
|---|---|---|
| Company search (`mixed_companies/search`) | 1 credit per search | Matching organizations |
| People search (`mixed_people/api_search`) | **Free** | Names, titles, `email_status` flag, phone-availability flag — no actual email or phone |
| Contact search (records already in the CRM) | **Free** | Existing contact records and their fields |
| Organization enrichment (`organizations/enrich`) | 1 credit per company | Funding, department sizes, technologies, growth — lands in Apollo system fields |
| Job postings (`organizations/job_postings`) | 1 credit per company | Open roles with URLs and posted dates |
| People enrichment / `people/bulk_match` | 1 credit per **matched** person | The actual email address |
| Mobile / direct-dial reveal | Separate mobile credit pool | Direct-dial number |

Unmatched people in a bulk match are not charged. Batch matches in groups of 10.

**Never set phone-reveal or waterfall-enrichment flags without separate approval** —
they draw on a different credit pool and can multiply the cost of a run silently.

### Verify this table against the live account

Apollo meters differently across plan tiers, and at least one endpoint here is
plan-dependent: `organizations/enrich` is billed as 1 credit on some accounts
but is documented as free on flat-rate plans. Before quoting costs to a client,
confirm against their own account rather than assuming these numbers transfer. The
free-vs-paid *boundary* (search free, reveal paid) holds across plans; the per-call
numbers do not necessarily.

## Reachability tiers

Derived from the free `email_status` flag returned by people search. Use as a
multiplier against role fit, then spend match credits top-down.

| Flag | Tier | Multiplier | Spend? |
|---|---|---|---|
| `verified` + phone available | T1 | 1.0 | Yes |
| `verified` | T2 | 0.85 | Yes |
| `catch_all`, `guessed`, `likely` | T3 | 0.6 | Only if the role fit is strong and the tier justifies it |
| `unavailable`, `unverified`, absent | T4 | 0.3 | No — do not spend a match credit |

Catch-all domains accept mail for any address, so a `catch_all` result is not
evidence the mailbox exists. Contacts enriched from catch-all domains are flagged as
send-risk in the audit log; ranking them below verified contacts *before* spending
is cheaper than discovering it afterward.

## Stating cost before a run

Every credit-consuming step is confirmed with the user before spending, with the
total stated upfront (operating principle 3). The estimate for a signal scan is:

```
1                        company search
+ (1 x accounts enriched)      org enrichment      [Excellent + Good tiers]
+ (1 x accounts)               job postings        [hiring motion only]
+ (1 x people matched)         people enrichment   [after reachability ranking]
```

Report actual burn by category at the end of the run, not just the total — a run
that came in under estimate because matches failed is a different outcome from one
that came in under estimate because fewer accounts qualified.
