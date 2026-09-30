**Verdict: messy in places, and the mess is small.** The one thing to know before Monday is that `billing/invoice.py` looks like a duplicate of the other date helpers but must not be merged with them.

**What a newcomer should know**

1. **There are four date helpers, and one of them is different on purpose.** `api/serializers.py:1`, `web/views.py:1` and `jobs/export.py:1` are three identical copies of `%d/%m/%Y`. `billing/invoice.py:1` uses `%Y-%m-%d`. Its comment at lines 2–4 says the tax authority's upload spec fixes that format, and changing it rejects the whole filing. If you "dedupe" all four, you break tax filing. *Traced: I read all four files.*
2. **A display-format change currently means editing three modules.** The move I'd make is to give the display format one owner and leave billing alone. `jobs/export.py` is the open question: a CSV export may be a machine-readable contract, unlike the two customer-facing outputs. Ask its owner before merging it. *Traced.*
3. **`providers/` is a seam with one implementer.** `Provider` has only `SmtpProvider`, and nothing in the tree calls `registry.get`. It's a guess about future providers, not a proven seam. *Traced.*
4. **Five modules look unreferenced.** The graph tool flags `web`, `api`, `jobs`, `billing` and `registry`. These are probably entry points called from outside `fixture/`, so I'm not calling them dead. Don't delete anything on this evidence. *Suspected: static import graph only.*
5. **The structure is otherwise clean.** There are 2 import edges, no cycles, no hubs, no pass-through layers and no I/O in the core. *Proven: I ran `graph-audit.py` and `dep-map.py`.*

**What I couldn't do.** `fixture/` isn't a git repository, so there is no change history, no co-change analysis and no owner information. The yardstick changes are assumed from the code, not taken from history.

**The written file doesn't pass its own check.** I wrote `docs/arch-design.md` with 4 findings and 1 move. `arch-design.py check` exits 1: it resolves paths and `at:` against a git repo root, so all 14 file references report as broken and `at:` reports as stale. The content is hand-verified against the files, but the check hasn't passed. Running `git init` and committing would probably clear it. I held off because that changes your directory and you didn't ask for it.

Files are in `C:\Users\thana\AppData\Local\Temp\tte-eval-z7813kbl`:
- `docs/arch-design.md`

<!-- file written by the agent: docs/arch-design.md -->
# ARCH-DESIGN
- at: no-git (fixture/ is not a repository; no history, no change-map)
- question: fixture/: what must a newcomer know before changing things?
- yardstick: change the customer-facing date format (3 modules: api, web, jobs); add a second message provider (2 modules: providers.smtp, providers.registry); change the tax filing date format (1 module: billing). Source: assumed from the code, no history or tracker available.
- status: open
- verdict: messy in places
- context: every move assumes billing/invoice.py's date format stays independent of display formats

## Finding 1: display date format copied three times
- where: fixture/api/serializers.py:1, fixture/web/views.py:1, fixture/jobs/export.py:1
- cost: 3 byte-identical copies of "%d/%m/%Y"; changing the display format edits 3 modules and a missed one silently disagrees
- badge: worth exploring
- evidence: traced, read all three files. Same-reason test not settled for jobs/export.py (a CSV export may be a machine contract, unlike the two customer-facing ones); ask its owner.

## Finding 2: billing date looks like a duplicate and must not be merged
- where: fixture/billing/invoice.py:1
- cost: merging it into the display helper would change "%Y-%m-%d" to "%d/%m/%Y" and, per the comment at lines 2-4, the tax authority rejects the whole filing
- badge: strong
- evidence: traced, comment at fixture/billing/invoice.py:2 states the constraint; it changes for a different reason (tax spec) than the three above. One copy, kept separate on purpose.

## Finding 3: Provider seam has one implementer
- where: fixture/providers/base.py:1, fixture/providers/registry.py:3
- cost: 1 implementer (SmtpProvider), 0 in-tree callers of registry.get (registry.py:6); dep-map reports 0 seams
- badge: speculative
- evidence: traced. Nothing in-tree calls it, so it may be used by out-of-tree code. Not proven dead; propose no deletion.

## Finding 4: five modules unreferenced in-tree
- where: fixture/web/views.py:5, fixture/api/serializers.py:5, fixture/jobs/export.py:5, fixture/billing/invoice.py:8, fixture/providers/registry.py:6
- cost: graph-audit lists 5 dead-module candidates, 5 unused defs
- badge: speculative
- evidence: suspected. Entry points (web framework, job runner) are outside fixture/; static import graph can't see them. latent-audit's disconnection proof is needed before any deletion.

## Move 1: one owner for the customer-facing date format
- cost: 3 copies today (Finding 1)
- pays: change the display date format: 3 modules -> 1
- files: fixture/api/serializers.py:1, fixture/web/views.py:1, fixture/jobs/export.py:1
- owner: format_date in fixture/api/serializers.py (or a new shared module), imported by the other two. Never fixture/billing/invoice.py.
- callers: serializers.order_json (serializers.py:6), views.order_page (views.py:6), export.rows (export.py:6); confirm out-of-tree callers first
- door: two-way, land it and go
- proof: characterization test that each of the three outputs is unchanged for one sample date (dd/mm/yyyy), plus one asserting invoice.line still emits ISO-8601; both pass before and after
- effort: S
- after: nothing
