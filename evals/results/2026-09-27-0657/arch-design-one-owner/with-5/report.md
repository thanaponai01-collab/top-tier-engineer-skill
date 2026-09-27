**Verdict: messy in places, but small.** The most important thing for someone new to know is that `billing/invoice.py:1` looks like a fourth copy of the date helper and must not be merged with the others. The tax authority requires ISO-8601 dates in the filing, and the comment at `billing/invoice.py:2` says changing that format "rejects the whole filing." Right now that comment is the only thing protecting it. No test checks it.

What they should know before changing anything:

1. **Don't let the billing date follow the display date.** `invoice_date` changes when the tax spec changes. The display helpers change when the product's look changes. Anyone cleaning up duplicates will want to fold billing in; don't. *(traced: the comment is the recorded reason. There's no git history to check beyond it.)*
2. **The display date format is copied three times under three names:** `fmt_date` (`web/views.py:2`), `format_date` (`api/serializers.py:2`) and `date_str` (`jobs/export.py:2`), all `"%d/%m/%Y"`. Changing the format means editing all three, and missing one ships inconsistent dates. *(proven: I grepped for it and a separate subagent recounted, same result.)*
3. **Two of those three may not be purely for display.** The API field `placed_at` and the CSV export may be read by outside code. Nothing in the repo says whether they are, so ask before changing either format. That change would be hard to undo; merging the helpers is not.
4. **`providers/` is a plugin system with one plugin and no callers.** It has a base class, a registry and `SmtpProvider`, and `registry.get` has zero call sites inside `fixture/`. It may be called from outside this folder, so treat it as *suspected* unused and don't delete it without proving that. Add a second provider only through the registry.
5. **There's no safety net.** There are no tests and no git history, so any change is currently checked by eye.

**The most useful fix, in two moves:**
- **Move 1:** add tests that fix the output format of every date: billing, API, export and web page. This one change protects the tax filing. (Small.)
- **Move 2:** replace the three display helpers with a single `display_date` function, leaving billing's separate on purpose. A display-format change then touches 1 file instead of 3, and the Move 1 tests make any accidental change to the API or export output fail loudly. (Small, lands after Move 1.)

**About the file's check:** everything is written up in `fixture/docs/arch-design.md`. The skill's `check` script reported 0 broken references when run from the repo root in a scratch copy, but it still exits 1. That's because it compares the file against a git commit, and `fixture/` isn't a git repository, so it will keep failing until the code is committed and the `at:` line is set to that commit. I didn't draw a diagram; for seven files it wouldn't add much.

The three future changes I judged the structure against are assumed, since there's no history or issue tracker: changing the date format, adding a message provider, and adding an order field. If the team expects different changes, the priorities may shift.

<!-- file written by the agent: fixture/docs/arch-design.md -->
# ARCH-DESIGN
- at: no-git (fixture/ is not a git repository; analysis true of the working tree on 2026-09-27)
- question: what should someone new know about fixture/'s structure before changing it?
- yardstick: change the customer-facing date format (3 modules: web, api, jobs); add a second message provider (1 module: providers, plus the unknown caller); add a field to order output (3 modules: web, api, jobs). All three assumed, since there is no history, tracker or requirements.
- status: open
- verdict: messy in places
- context: output formats stay byte-identical; billing/invoice.py keeps its own ISO-8601 formatter
- diagram: none. The codebase is 7 files and the moves are local.

## Finding 1: The display date format is copied three times under three names
- where: web/views.py:2, api/serializers.py:2, jobs/export.py:2
- cost: 3 identical `"%d/%m/%Y"` helpers (`fmt_date`, `format_date`, `date_str`). Changing the display format touches 3 modules, and missing one ships inconsistent dates.
- badge: strong
- evidence: proven. grep found 3 copies, and an independent subagent recount agreed. Open question from the same-reason test: web is plainly customer display, but api `placed_at` and the jobs CSV may be machine contracts that outside consumers parse. Nothing in the code says either way.

## Finding 2: billing's date formatter looks like a duplicate but must not be merged
- where: billing/invoice.py:1
- cost: 1 formatter (`%Y-%m-%d`). Its comment at billing/invoice.py:2 says a change "rejects the whole filing". No test enforces this. Only the comment protects it.
- badge: strong
- evidence: traced. The recorded reason is the comment at billing/invoice.py:2 (tax authority upload spec, ISO-8601). Same-reason test: it changes when the tax spec changes, the display helpers change when the UX changes, so it has a different owner.

## Finding 3: The provider plugin system has one plugin and no callers
- where: providers/base.py:1, providers/registry.py:6, providers/smtp.py:4
- cost: 3 files, 1 implementation (the docstring at providers/base.py:2 admits it). 0 call sites of `registry.get` inside fixture/.
- badge: speculative
- evidence: suspected. The caller may live outside fixture/, and deadness has not been proven (latent-audit's job). It only pays off if a second provider is coming. No deletion proposed.

## Decision 1: Who owns the display date
- options: A) one shared `display_date` used by web, api and jobs | B) web owns display, and api and jobs each pin their own format as a contract
- forces: A makes a UX format change a 1-file edit. B stops a UX change from silently breaking API clients or CSV consumers. Nobody knows yet whether outside code parses api/jobs dates.
- door: two-way. Merging the helpers changes no output. Changing the API's date format later is a separate one-way decision and not part of this.
- evidence: proven (identical strings by grep). Recommend A plus the contract tests in Move 1: a later format change then fails loudly in api/jobs instead of drifting silently.

## Move 1: Pin every date format with a test before touching any helper
- cost: 0 tests today. The billing invariant rests on a comment alone (billing/invoice.py:2).
- pays: change the display date format. Any change that would move billing, api or jobs output now fails a test instead of reaching the tax authority or a consumer.
- files: billing/invoice.py:8, api/serializers.py:5, jobs/export.py:5, web/views.py:5
- owner: a new tests/test_date_formats.py owns the output contracts
- callers: none (test-only addition)
- door: two-way, land it and go
- proof: `cd fixture && python -m pytest tests/test_date_formats.py` passes, asserting `line({'id':1,'placed_at':date(2026,1,2)}) == '1|2026-01-02'`, `order_json(...)['placed_at'] == '02/01/2026'`, `rows([...]) == ['1,02/01/2026']`, and `order_page(...)` contains `02/01/2026`
- effort: S
- after: nothing

## Move 2: One owner for the customer display date
- cost: 3 copies at web/views.py:2, api/serializers.py:2, jobs/export.py:2
- pays: change the display date format goes from 3 files to 1
- files: web/views.py:1, api/serializers.py:1, jobs/export.py:1
- owner: a new formats.py, function `display_date`. billing/invoice.py:1 `invoice_date` stays separate and deliberately does not import it.
- callers: web/views.py:6 (`fmt_date`), api/serializers.py:6 (`format_date`), jobs/export.py:6 (`date_str`)
- door: two-way, land it and go
- proof: the Move 1 tests still pass unchanged, and `grep -rn '%d/%m/%Y' fixture --include=*.py` returns only formats.py
- effort: S
- after: Move 1
