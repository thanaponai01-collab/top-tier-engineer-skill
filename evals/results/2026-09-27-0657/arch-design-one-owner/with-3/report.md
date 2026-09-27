The codebase's structure is fine, and I'm not proposing any moves. The one thing a newcomer needs before Monday is that **the date helpers look like copy-paste, but they don't all do the same job, so they must not be merged.**

### What they should know

1. **`billing/invoice.py:5` must never change.** It uses the ISO-8601 format (`%Y-%m-%d`) because the tax authority's upload spec requires it. The comment on lines 2–4 says that changing it "rejects the whole filing." It sits next to three other date helpers, so it's easy to "clean up" by mistake. Of the four, this is the one line most worth protecting.

2. **The other three `%d/%m/%Y` copies aren't really the same thing either.** They are in `web/views.py:2`, `api/serializers.py:2` and `jobs/export.py:2`, and each serves a different consumer:
   - the web page, which is display;
   - the JSON API, a contract with outside clients;
   - a CSV export, whose consumer is unknown.

   If you fold them into one `display_date`, a routine UI format change would also silently change the API's output and the CSV. Merging would save 4 lines. Leave them apart until someone confirms that the API and export dates are meant to follow the UI.

3. **`providers/` is set up for more channels than it has.** There's an interface, a registry and one SMTP implementation, and I found no caller of `registry.get` anywhere in `fixture/`. That doesn't prove it's unused, because whatever entry point calls it isn't in this folder. Don't delete it on that basis. Don't build on it either unless a second channel (SMS, push) is actually planned. If one is, adding it means one new file plus one registry line.

4. **Changes that touch several modules are normal here.** For example, adding a field to order output means editing web, api, jobs and billing. That's one edit per consumer, which is expected, not a design flaw. Billing's pipe-delimited line follows the tax spec, so check that spec before adding anything to it.

### How I know
- I read all 7 files. `grep` shows each date helper has exactly one caller, inside its own file.
- **There's no git history**, because `fixture/` isn't a git repository. That means I couldn't check which files tend to change together. The three "likely next changes" I measured against are my own guesses (display format, a second channel, a new order field), not taken from any tracker.
- The audit is in `fixture/docs/arch-design.md`: 2 findings and 1 decision, with no strong findings and no moves. Its `at:` line says "not a git repo" because there's no commit to pin it to. The format checker requires git, so I ran it on a temporary git copy of the folder, where it passed with 0 broken and 0 stale. It won't pass inside `fixture/` as it is now.

If you know which of those three changes is actually coming next, tell me and I'll re-run the audit against it. The date-format decision in particular depends on it.

<!-- file written by the agent: fixture/docs/arch-design.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; the analysis matches the working tree as of 2026-09-27)
- question: what should a new engineer know about fixture/ before changing it?
- yardstick: change the customer-facing date format (1–3 modules: web, api?, jobs?; billing must not move); add a second message channel such as SMS (1 module: providers, 2 files); add a field to order output (4 modules: web, api, jobs, billing, one per consumer, as expected)
- yardstick-source: assumed. There is no git history, no issue tracker and no stated requirement, so these three are guesses from what the code does
- status: open
- verdict: clean. Nothing costs enough today to justify a move; there are two traps a newcomer could fall into
- context: every date helper's current output stays byte-identical until each consumer's owner confirms the format it relies on

## Finding 1: Four date helpers look like duplicates, but only some of them are
- where: api/serializers.py:2, web/views.py:2, jobs/export.py:2, billing/invoice.py:5
- cost: 3 identical `%d/%m/%Y` one-liners (api, web, jobs) plus 1 ISO-8601 helper in billing; 6 lines in total, 1 call site each
- badge: worth exploring
- evidence: traced. Read all 7 files, and grep shows each helper has exactly one caller, in its own file. billing/invoice.py:2-4 records that the ISO format is fixed by the tax authority and "must not move with" the display format. None of the other three records why it uses its format
- same-reason: billing changes when the tax spec changes, so it must never share a helper. web is display. api is a wire contract with outside clients. jobs is a CSV whose consumer is unknown. Three different reasons to change, so a merge would tie an API contract to a UI choice

## Finding 2: A provider abstraction with one implementation and no caller in the tree
- where: providers/base.py:1, providers/registry.py:6, providers/smtp.py:4
- cost: 1 interface, 1 implementation, 1 registry entry; `registry.get` has 0 callers inside fixture/
- badge: worth exploring
- evidence: suspected. Grep finds no caller, but the entry points that would call it are not in fixture/, so "unused" is not proven. The docstring (providers/base.py:2) acknowledges that there is only one implementation. It pays only if a second channel is actually coming

## Decision 1: Who owns the `%d/%m/%Y` format
- options: A) keep one helper per consumer (today's shape) and name each one by its consumer | B) one shared `display_date` used by web, api and jobs
- forces: B makes "change the display format" a 1-file edit; A stops a UI change from silently changing the public API's JSON and the export CSV, which are one-way changes for their consumers
- door: two-way (internal helpers; output is unchanged either way today)
- recommendation: A until someone confirms that the api and jobs dates are meant to follow the UI. The saving from B is 4 lines
- evidence: traced (all call sites read; consumer intent is unknown)
