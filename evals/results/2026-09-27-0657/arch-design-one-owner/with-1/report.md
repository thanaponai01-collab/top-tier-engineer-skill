**Verdict: messy in places.** The code is small (7 files, 45 lines) and mostly fine. Two things matter before anyone changes it, and they pull in opposite directions:

1. **The customer-facing date format is copied three times.** `"%d/%m/%Y"` appears separately in `api/serializers.py:2`, `jobs/export.py:2` and `web/views.py:2`, under three different names. If the format changes, all three must be edited, and missing one gives an inconsistency that nothing will catch. This is the move that pays most: one `display_date` helper, taking the change from 3 files to 1.
2. **`billing/invoice.py:5` looks like a fourth copy, and must never be merged with them.** Its comment (`:2-4`) says the tax authority's spec fixes it as ISO-8601, and that changing it gets the whole filing rejected. The three display dates change when the display changes; this one changes only when the tax spec does. It's the easiest trap for a new person to walk into, because a "remove duplication" cleanup would break tax filing.

**Also worth knowing:**
- **`providers/` is built for more than it holds.** There's a base class, one subclass (SMTP) and a one-entry registry. Nothing inside `fixture/` calls `registry.get()`, but callers may live outside it and there's no history to say why it exists. I'm marking it speculative and not proposing to delete it. If a second provider is really coming, the structure is worth keeping.
- **Ask one question before merging the dates:** do the API JSON and the CSV export have outside consumers? If they do, merging ties their output to the website's display format, so a future display change would silently change what those consumers receive. In that case, only the web copy should use the shared helper (Decision 1 in the file).
- **There's no git history and there are no tests.** So there's nothing to show which files change together, and no safety net. I wrote a one-line behaviour check (in Move 1's `proof:`) that passes on the current code; run it before and after any change.

**How I know:**
- Found by searching and by running the baseline check: the three copies, the invoice date and the single provider subclass.
- Read directly in the code: the invoice constraint.
- A separate subagent recounted all of this without being told what I'd found, and got the same numbers.
- I had no issue tracker or history to work from, so the "likely next changes" I measured against are my assumptions.

**Output:** `fixture/docs/arch-design.md` has 3 findings, 1 decision and 1 move. The file's checker can't pass inside `fixture/` because it isn't a git repo (it reports every path as missing and the `at:` line as not a commit). I ran it on a throwaway git copy and it passed with 0 broken, 0 stale. If you want it to pass in place, `git init` the fixture. I skipped a diagram because the tree is too small for one to help.

<!-- file written by the agent: fixture/docs/arch-design.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; analysis true of the tree on 2026-09-27)
- question: whole-tree audit: what should a new maintainer know before changing things?
- yardstick: change the customer-facing date format (3 modules today: api, jobs, web); add a field to the order output (4 modules: api, jobs, web, billing, each builds its own order shape, expected); add a second message provider (1 module: providers)
- yardstick-source: assumed, since no user list, issue tracker or git history exists. The first comes from the comment at billing/invoice.py:3
- status: open
- verdict: messy in places
- context: billing/invoice.py keeps its own ISO-8601 date and is never merged with the display dates; api/serializers.py and jobs/export.py are assumed to show the customer-facing format (unconfirmed, see Decision 1); providers/ stays as it is

## Finding 1: Customer-facing date format has 3 owners
- where: api/serializers.py:2, jobs/export.py:2, web/views.py:2
- cost: 3 byte-identical copies of "%d/%m/%Y" under 3 names (format_date, date_str, fmt_date); changing the display format means 3 edits in 3 modules, and missing one is a silent inconsistency
- badge: strong
- evidence: proven. grep over all 7 files and a baseline run; a subagent recounted 3 copies without being told the expected number

## Finding 2: The invoice date looks like a 4th copy but is a separate contract (do not merge)
- where: billing/invoice.py:5
- cost: 1 helper; merging it with the display dates would make a display change reject the whole tax filing (billing/invoice.py:2-4)
- badge: strong
- evidence: traced. The constraint is written at billing/invoice.py:2-4. Same-reason test: this one changes when the tax authority's spec changes, the others when the display does

## Finding 3: Provider abstraction and registry built for one implementation
- where: providers/base.py:1, providers/registry.py:3, providers/registry.py:6
- cost: 1 base class, 1 subclass (SmtpProvider), a 1-entry registry; 0 callers of registry.get inside fixture/
- badge: speculative
- evidence: suspected. Callers may sit outside fixture/, and there is no history to ask why it exists. The docstring at providers/base.py:2 says "Implemented once". If a second provider is really coming (yardstick 3), the seam pays for itself; otherwise inline it. No deletion is proposed until latent-audit proves get() is unreached

## Decision 1: Who owns the display date format
- options: A, one display_date helper used by web, api and jobs | B, web owns the display format while api and jobs each pin their own format as an external contract
- forces: the invoice comment names "the customer-facing format" as one thing, which favours A; if the API JSON or the CSV export has outside consumers, A means a future display change silently changes their contract, which favours B for those two
- door: two-way. The merge itself leaves output unchanged. Changing the format later is the one-way step and gets decided then
- evidence: traced. All four date helpers and the invoice comment were read. Whether api and export have outside consumers is unknown, so ask before Move 1 if you can

## Move 1: One owner for the customer-facing date format
- cost: 3 copies in 3 modules (Finding 1)
- pays: change the customer-facing date format: 3 files → 1
- files: api/serializers.py:1, jobs/export.py:1, web/views.py:1
- owner: new display_dates.py at the repo root holding display_date(d) with "%d/%m/%Y"; billing/invoice.py is explicitly NOT a caller
- callers: api/serializers.py:6 (format_date), jobs/export.py:6 (date_str), web/views.py:6 (fmt_date); delete the three local helpers
- door: two-way. Output is byte-identical; revert the commit to undo. If Decision 1 comes back B, apply it to web only and leave api and jobs alone
- proof: from fixture/, run `python3 -c "import datetime as t; from api.serializers import order_json; from jobs.export import rows; from web.views import order_page; from billing.invoice import line; o={'id':1,'placed_at':t.date(2026,9,27)}; assert order_json(o)=={'id':1,'placed_at':'27/09/2026'}; assert rows([o])==['1,27/09/2026']; assert order_page(o)=='Order 1 placed 27/09/2026'; assert line(o)=='1|2026-09-27'; print('ok')"`; it prints ok before the move (proven 2026-09-27) and must still print ok after. Then `grep -rn '%d/%m/%Y' .` should return exactly 1 line
- effort: S
- after: nothing
