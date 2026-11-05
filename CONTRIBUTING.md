# Contributing to GTM OS

Most people who improve this engine never open a pull request. They run their own copy,
hit something wrong, and say so. That is the contribution that matters most, and it is
the one this file makes cheap.

## Report a bug, ask for a feature, or rate a skill

Three ways, in the order they cost you the least:

1. **From the engine.** Say "report this bug", "send feedback" or "request a feature" in
   the session where it happened. The `gtm-os-feedback` skill asks you three questions,
   strips anything that identifies your instance, shows you the exact issue body, and
   files it only through a command you approve. Without `gh` it hands you the body and
   the right form instead.
2. **From GitHub.** <https://github.com/NicT89/gtm-os/issues/new/choose> has the same
   three forms: bug, feature request, skill feedback.
3. **By email**, for anything that must not be public: a credential or an instance
   value you found in this repo, or a skill that could write somewhere it should not.
   That is a security report; [`SECURITY.md`](SECURITY.md) says where it goes.

### What never goes in an issue

This tracker is public. Nothing from your instance belongs in it: no Apollo, Airtable or
HubSpot IDs, no prospect or customer names, no credentials, no run reports, no links into
your workspace. The skill replaces those with `[redacted: <kind>]` markers before you see
the body; if you type an issue by hand, replace them yourself with `{KEY}` or
`[redacted]`. A reproduction that needs a real ID can be described ("the posts table",
"the contact play field") and the maintainer will ask in the thread if more is needed.

### What happens next

The maintainer triages issues in the order they arrive and labels each one with its area
(`area: skills`, `area: setup`, `area: references`, `area: tooling`, `area: ci`). A
confirmed bug gets a fix in the next patch release, which every fork or private copy
receives through its upstream sync (`FORKING.md`, section 3). A feature request is
answered with one of three outcomes, in the thread: **built** (it is universal and belongs
in the engine), **guided** (it differs per organization, so the engine gets guidance for
the field rather than a fixed option; `CLAUDE.md` explains the distinction), or
**declined**, with the reason. A skill-feedback issue informs the next revision of that
skill and is closed when that ships, with a note saying what changed.

No issue is closed without a reply. If one sits for more than two weeks without a
response, comment on it; the maintainer is one person.

## Propose a change yourself

Welcome, and entirely optional. Everything below is for a change to the engine; a change
to *your* copy lives on your fork and never needs to come here (`FORKING.md`).

- Read [`CLAUDE.md`](CLAUDE.md) first. It is written for an agent changing the repo and
  it holds the conventions a review will check: tokenized values, no invented numbers,
  one word per axis, checks that are proven to fail.
- Re-tokenize every deployment value to a `{KEY}` before you push. Nothing resolved from
  your instance may leave your machine; `scripts/scan_secrets.py` catches credential
  shapes, but only you can catch your own IDs.
- Open the PR against `main`, fill in every section of the template, and expect the
  review loop in [`MAINTAINING.md`](MAINTAINING.md#the-review-loop).
- A skill adapted from someone else's work keeps their license file beside it and names
  the source in the README table; the existing rows show the form.

## License

By contributing you agree your contribution is licensed under the repository's
[PolyForm Noncommercial License 1.0.0](LICENSE). The commercial grants the maintainer
issues cover the engine as a whole, contributions included; a contributor is not owed a
share of one.
