**Verdict: messy in places, but small.** The one thing to know before Monday is that `fixture/billing/invoice.py` must never share a date helper with the other three date functions.

I ran `arch-design` in audit mode and wrote the findings to `docs/arch-design.md`. Its own `check` script fails, so the file isn't validated. It resolves paths against a git root and `fixture/` isn't a repo. I didn't run `git init` in your directory. The only failures were the missing repo root and `at:` (7 "not a file in the repo" errors, 1 stale), not content errors. I didn't check for a git root above `fixture/`, so I haven't shown that initialising one would fix it.

**What to tell them**
1. **Don't merge the invoice date with the others.** `billing/invoice.py:2-5` formats dates as ISO-8601 because the tax authority's upload spec requires it. Its comment says changing it "rejects the whole filing". It looks like a copy of the three date helpers below, but it changes for a different reason. Any "dedupe the date helpers" cleanup must leave it alone.
2. **The customer-facing date format is copied three times.** `%d/%m/%Y` appears in `api/serializers.py:1`, `web/views.py:1` and `jobs/export.py:1`, so changing it means editing 3 files. This is the strong finding. The suggested fix is one shared helper for `api` and `web` (effort S).
3. **Leave `jobs/export.py` out of that merge until someone knows who consumes the CSV.** It may need to change for a different reason than the customer-facing pages.
4. **The `providers/` abstraction has one implementation.** `base.py` says "Implemented once" and `registry.py` has a single `smtp` entry. This is speculative, not a defect. I found no in-tree callers of `registry.get`, but callers outside `fixture/` are invisible to me, so nothing is proven dead and I'd delete nothing.

**What checked out clean:** there are no import cycles, no hub modules and no pass-through layers. The import graph has only 2 edges, both inside `providers/`.

**What I couldn't measure:**
- **History:** with no git history I couldn't check what changes together, or why the provider seam exists.
- **Yardstick:** the three likely changes I used are my assumptions, not sourced from a tracker.
- **Layer rules:** no layer rules are declared, so layer breaches are unmeasured.

<!-- file written by the agent: docs/arch-design.md -->
# ARCH-DESIGN
- at: none (no git)
- question: what must a newcomer know before changing fixture/?
- yardstick: change the customer-facing date format (3 modules today: fixture/api/serializers.py, fixture/web/views.py, fixture/jobs/export.py; source: assumed, no history/tracker); add a second message provider (2 modules: fixture/providers/smtp.py + fixture/providers/registry.py); change the tax filing date format (1 module: fixture/billing/invoice.py)
- status: open
- verdict: messy in places
- context: every move assumes the invoice date format stays independent of the display format, and that the layout of fixture/ stays as is.

## Finding 1: customer-facing date format is copied three times
- where: fixture/api/serializers.py:1, fixture/web/views.py:1, fixture/jobs/export.py:1
- cost: 3 byte-identical copies of "%d/%m/%Y" (format_date, fmt_date, date_str); one format change touches 3 modules
- badge: strong
- evidence: proven, read all three files; graph-audit shows no import between them. Same-reason test: api and web both show dates to customers (same reason). fixture/jobs/export.py writes CSV rows for some unknown consumer, so it may change for a different reason (suspected).

## Finding 2: fixture/billing/invoice.py looks like a fourth copy and must not be merged
- where: fixture/billing/invoice.py:2-5
- cost: none today. Merging it into the display helper would make a display-format change reject the tax filing (comment at invoice.py:2-4).
- badge: speculative
- evidence: traced, read the comment and function. It is a guardrail, not a finding to fix.

## Finding 3: provider base class and registry have one implementer
- where: fixture/providers/base.py:1, fixture/providers/registry.py:3
- cost: 1 implementer (SmtpProvider), 1 registry entry, 0 in-tree callers of registry.get (registry.py:6)
- badge: speculative
- evidence: suspected. base.py:2 docstring says "Implemented once". graph-audit lists registry.get as unreferenced, but callers may live outside fixture/, so nothing here is proven dead. No history to say why the seam exists.

## Decision 1: where the shared display date format lives
- options: one helper module imported by web and api (export.py stays separate until its consumer is known) | leave the copies and accept the 3-file change
- forces: the same-reason test favours merging api and web; export.py's reason is unknown; the invoice format must stay apart
- door: two-way
- evidence: traced, read all four date functions.

## Move 1: give api and web one display-date helper
- cost: 2 identical copies today (serializers.py:1, views.py:1); 3 with export.py
- pays: change the customer-facing date format: 3 files → 1 for api and web (export.py stays a separate question)
- files: fixture/api/serializers.py:1, fixture/web/views.py:1
- owner: a new fixture/common/dates.py, function display_date
- callers: fixture/api/serializers.py:6 (format_date), fixture/web/views.py:6 (fmt_date). Grep any callers outside fixture/ before landing; none exist in-tree.
- door: two-way, land it and go
- proof: add a test that display_date(date(2026,1,2)) == "02/01/2026" and that billing.invoice.invoice_date(date(2026,1,2)) == "2026-01-02"; both must pass before and after. No old tests exist to replace.
- effort: S
- after: nothing
