# Get started (canonical fragment)

The block between the two markers below is the single source of truth for the
"Get started" instructions. It is repeated **verbatim** in `README.md`, `CLAUDE.md`, and
`AGENTS.md` so that whichever file a person or an agent opens first, the same four steps
are there and no one has to be routed somewhere else to begin.

That redundancy is the point, and it is also the risk: three copies drift the moment one
is edited alone. `tests/test_get_started_consistent.py` asserts all three are byte-identical
to this one and that the install commands still match `.claude-plugin/marketplace.json`, so
the drift fails the build instead of shipping.

Paths inside the block are written as plain backticked paths rather than markdown links,
because the block has to read correctly from the repo root and from this directory both.

<!-- BEGIN GET STARTED -->
## Get started

GTM OS is a **Claude Code plugin**, not a prompt and not a hosted service. Opening this
repo's URL in a chat window installs nothing and runs nothing — the skills only exist
once the plugin is installed.

**1. Install it.** In Claude Code:

```
/plugin marketplace add NicT89/gtm-os
/plugin install gtm-os@gtm-os
```

**2. Set it up.** In a working directory of your own — not a clone of this repo — say:

```
set up my environment
```

The `environment-setup` skill drives it, and it diagnoses what you already have before it
suggests anything, because **not set up almost never means not owned**. The usual
situation is that you own the tool and have simply never shaped it for this engine.
Diagnosis is free: every probe it runs is a read-only call, and none of them spends a
credit.

**3. Know how well it speaks your stack.** Bring the CRM and data tools you already use.
`references/platform-support.md` says plainly which platforms are built in natively, which
run generically, and which are not built yet. A platform that is not native still works —
it is just not as good, and the engine tells you which one you are on rather than
pretending they are equivalent.

**4. Run something.** Ask in your own words — `run a signal scan`,
`create a GTM blueprint for <company>`, `audit my sequence`. Every skill states what it
needs and stops when a connector is missing rather than guessing around it.

Full walkthrough: `SETUP.md`. Nothing from your instance — IDs, prospects, reports, logs —
ever comes back to this repo.
<!-- END GET STARTED -->
