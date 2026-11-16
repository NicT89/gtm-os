# Brand context: where a skill gets the seller's own brand, and in what order

Every skill that composes in the seller's voice, names their products, or writes to a CRM
context center reads brand context from one of three places, in this order. A SKILL.md
cites this file; it does not restate the order or the fallback.

## The lookup order

1. **The Brand Kit OS connector**, when present. Start with `get_agent_briefing` (kit id
   from `{BRAND_KIT_OS_ID}` when set, otherwise the one kit the account can access; never a
   guessed id). This is the live, governed version: review queue, provenance, anti-slop
   rules and attack angles all live there.
2. **`{BRAND_CONTEXT_DIR}`** in the workspace (default `brand/`), when the connector is
   absent. These are the files `gtm-onboard` writes from the site scrape and the brand
   interview. Read only the files the task needs (the table below says which), and say
   once per run, in one line, that the files are the fallback and the connector is the
   live version. Say it once; do not repeat it per file or per draft.
3. **Ask the user**, when neither exists, for only what the task needs, and offer
   `gtm-onboard` to set the files up so the next run does not ask again.

Never mix sources inside one run. If the connector is present, the files are stale by
definition and are not read; `gtm-onboard` marks them `source: brand-kit-os` and read-only
after an import (see "Upgrading" below).

## The `brand/` folder

One file per Brand Kit OS entity, so the file layout and the kit are the same shape and an
import later is a mapping, not a rewrite.

| File | Holds | Read by |
|---|---|---|
| `README.md` | The references index: each file, what it holds, which skills read it, `last_verified` date | every skill, first |
| `company-profile.md` | What they sell, distribution models, GTM motion, proof points, pricing model (not prices), public channels | gtm-blueprint, provision-gtm-engine, the Apollo context-center step, content skills |
| `voice-and-expression.md` | Voice attributes, tone by channel, words used and words banned, example lines | copywriting, copy-editing, email-sequence, social-content, outreach-audit |
| `audiences.md` | Target audiences and segments | gtm-blueprint, pmf-five-gate-playbook, content skills |
| `personas.md` | Buyer personas: title, department, pains, value, objections they raise | gtm-blueprint, play-builder, email-sequence, the Apollo product entries |
| `products.md` | One section per product or offering, in the persona template's order | gtm-blueprint, the Apollo context-center product entries, pricing-strategy |
| `competitors.md` | Named competitors and the frame they are compared on | competitor-alternatives, gtm-blueprint, the Apollo context center |
| `objections.md` | Objections and the agreed response to each | email-sequence, outreach-audit, sales content |
| `proof-and-quotes.md` | Customer names (with permission), quotes, numbers with their source | every composing skill; the no-invented-numbers rule applies |
| `governance.md` | What is never said, never claimed, never named; approval rules | every composing skill; checked before any draft is shown |

Visual identity (palette, typography, logos) is the connector's domain. The files carry at
most a `visual-identity.md` with hex values and font names the user supplied, labeled like
everything else; `frontend-design` reads it when present and works from the brief otherwise.

## The front matter contract

Every file in `{BRAND_CONTEXT_DIR}` starts with:

```yaml
---
entity: company-profile          # the Brand Kit OS entity this file maps to
source: files | brand-kit-os     # who owns the truth right now
verified: 2026-11-08             # the date a person last confirmed the content
provenance_default: UNVERIFIED   # the label a line gets when it carries none
---
```

and every fact in the body carries a label: **KNOWN** (with a URL, or a named person and
date for interview answers), **INFERRED** (from what, in one clause) or **UNVERIFIED**.
**One fact per line, label at the end of the line.** The check is per line: a line that
carries two facts and one label passes on the label it has, so two facts on one line is a
writing error the audit cannot see. `scripts/check_workspace.py` fails a file with no front
matter or an unknown `source`, and a line (headings included) that asserts a number with no
label; it does not judge content.

These are the same three labels `evidence-register` uses, so a brand fact can be cited in
a report with no translation.

## Upgrading to the connector

When Brand Kit OS is connected after a deployment has run on files, `gtm-onboard` offers
to create the kit from the files, one entity at a time, each write as a dry run shown to the
user and then confirmed. Provenance maps to the kit's own `basis`:

| File label | Kit `basis` |
|---|---|
| KNOWN with a URL | `page_verbatim` when quoted, else `scrape_inferred` |
| KNOWN from a named person | `customer_stated` (or `operator_stated` when the person operates the engine) |
| INFERRED | `ai_inferred`, with the clause as the note |
| UNVERIFIED | not imported; listed back to the user as open |

After the import every file gets `source: brand-kit-os`, and from then on the lookup order
above skips them.

## Why not one file

The content skills want voice and personas; the context-center step wants profile,
products, competitors and objections; `pmf-five-gate-playbook` wants audiences. One file
would load all of it on every call and would be re-verified as a whole or not at all.
