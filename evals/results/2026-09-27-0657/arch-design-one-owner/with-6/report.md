**Verdict: messy in places, and the mess is small.** The most important thing for the new person on Monday is a trap, not a cleanup. `fixture/` has four date helpers that look like copies of each other. Three of them are. The fourth, billing's, must never be merged with the rest.

## What they should know

1. **Leave `billing/invoice.py:1` (`invoice_date`) alone.** It prints `%Y-%m-%d` because the tax authority's upload spec requires it. The comment at `billing/invoice.py:2` says changing it "rejects the whole filing." It will look like a fourth copy to anyone tidying up date helpers. It isn't one: it changes for a different reason than the display format does.
2. **The customer-facing date format is copied three times.** The same `%d/%m/%Y` helper appears in `api/serializers.py:1`, `web/views.py:1` and `jobs/export.py:1`. Changing that format today means finding and editing 2–3 files. (*Proven*: I grepped for it, and a separate subagent recounted it and found the same 3 copies with 1 call site each.)
3. **`jobs/export.py` has no known reader.** Its date format matches the display format today, but a CSV export may feed another system the way billing does. Ask who reads it before treating it as display.
4. **`providers/` is set up for more than one provider but has only one.** There's a base class, one SMTP subclass, and a registry with a single entry. Nothing inside `fixture/` calls `registry.get`, so the callers must be outside, or there are none. It's harmless, and it makes adding SMS cheap. Don't delete it without finding those callers first. (*Suspected*: there's no history to explain why it exists.)
5. **Ways to be wrong:**
   - The folder has no git history, tests or issue tracker.
   - I guessed the three changes most likely to come next (changing the date format, adding a message channel, adding an order field) rather than taking them from anywhere.
   - The only safety net is the one-line check written into the move below. It passes against the current code.

## The one move worth making
Create a new `display/dates.py` with a `display_date` function. Have `api/serializers.py` and `web/views.py` use it, and delete their local copies. That takes a date-format change from 2 files to 1. It's small and easy to undo. Billing and export stay untouched.

## The file
The report is at `fixture/docs/arch-design.md`: 4 findings and 1 move, each with the file and line it's based on. Its format check can't pass in place, because `fixture/` isn't a git repo and the check needs git to find the project root and a commit hash. I ran it on a throwaway git copy instead, where it passes with 0 errors. Running `git init` in `fixture/` would let it pass in place; I didn't do that myself.

I skipped the architecture diagram because one move in a 7-file codebase doesn't need one.

<!-- file written by the agent: fixture/docs/arch-design.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; analysis true of the working tree on 2026-09-27)
- question: what should a new engineer know about fixture/'s structure before changing it?
- yardstick: change the customer-facing date format (2 modules now: web, api; 3 if jobs/export is display); add a second message channel e.g. SMS (1 module: providers); add a field to order output (4 modules: api, web, jobs, billing — one per consumer, expected)   (all three assumed: no history, no tracker, no stated requirements)
- status: open
- verdict: messy in places
- context: billing's ISO date stays separate from every display format; the providers package's public shape (registry.get) stays, since its callers live outside fixture/

## Finding 1: customer-facing date format copied into three modules
- where: api/serializers.py:1, web/views.py:1, jobs/export.py:1
- cost: 3 byte-identical "%d/%m/%Y" helpers (format_date, fmt_date, date_str), 1 call site each; changing the display format means editing 2–3 files and remembering all of them
- badge: strong
- evidence: proven, grep for strftime over fixture/ plus a subagent recount (told only to list formatters and callers) returned the same 3 copies and 3 call sites

## Finding 2: billing's invoice_date looks like a fourth copy and must not be merged
- where: billing/invoice.py:1
- cost: 1 helper, "%Y-%m-%d"; the comment at billing/invoice.py:2 says the tax authority's upload spec fixes it and a change "rejects the whole filing"
- badge: strong
- evidence: traced, read billing/invoice.py:1-9; same-reason test fails (tax spec vs. customer display), so any date-helper consolidation must leave it out

## Finding 3: provider abstraction built for one provider
- where: providers/base.py:1, providers/registry.py:3
- cost: 1 base class with 1 subclass (SmtpProvider), a registry dict with 1 entry, 0 callers of registry.get inside fixture/
- badge: speculative
- evidence: suspected, callers may live outside fixture/ and there is no history to say why it exists; it also makes yardstick change 2 cheap (new file + 1 registry line), so the deletion test is ambiguous. No move proposed

## Finding 4: jobs/export's date format has no stated consumer
- where: jobs/export.py:1
- cost: 1 helper whose format matches display today, but a CSV export may feed another system the way billing does
- badge: worth exploring
- evidence: suspected, nothing in fixture/ says who reads the export; ask before folding it into the display owner

## Move 1: give the customer-facing date format one owner shared by web and api
- cost: 2 identical display-date helpers in api/serializers.py:1 and web/views.py:1
- pays: change the customer-facing date format: 2 files → 1
- files: api/serializers.py:1, web/views.py:1
- owner: new file display/dates.py, `display_date(d)` returning d.strftime("%d/%m/%Y")
- callers: api/serializers.py:6 (format_date → display_date), web/views.py:6 (fmt_date → display_date); delete the two local helpers. Do not touch billing/invoice.py or jobs/export.py
- door: two-way, land it and go
- proof: from fixture/ run `python3 -c "import datetime as D; from api.serializers import order_json; from web.views import order_page; from billing.invoice import line; from jobs.export import rows; o={'id':1,'placed_at':D.date(2026,9,27)}; assert order_json(o)['placed_at']=='27/09/2026'; assert order_page(o)=='Order 1 placed 27/09/2026'; assert line(o)=='1|2026-09-27'; assert rows([o])==['1,27/09/2026']; print('ok')"` prints `ok` before and after
- effort: S
- after: nothing
