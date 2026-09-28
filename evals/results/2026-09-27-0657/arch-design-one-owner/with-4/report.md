The codebase is **messy in places, not tangled**. The most important thing to tell the new person: **the date helpers look like duplicates you should merge, and one of them must never be merged.**

## What they should know before Monday

1. **Don't let `billing/invoice.py:invoice_date` share a date helper with anything else.** It formats dates as `%Y-%m-%d` because the tax authority's upload spec requires it. The comment at `billing/invoice.py:2-4` says changing it gets the whole filing rejected. Nothing enforces this except that comment: there's no test and no shared constant. This is the easiest serious mistake to make here.

2. **The display date format is written out three times.** `%d/%m/%Y` appears in `api/serializers.py:2`, `web/views.py:2` and `jobs/export.py:2`, each with one caller and nothing linking them. A format change today means editing all three, and it's easy to miss one. Don't merge them on sight, though:
   - The API's `placed_at` field is a public contract that clients parse.
   - The export file is probably read by other programs, not people.
   - Only the web page is purely for display.

   These three may need to change for different reasons.

3. **`providers/` has an abstraction for one implementation.** `Provider` has a registry and one subclass (`SmtpProvider`), and nothing in `fixture/` calls `registry.get`. Treat it as untested extension machinery, not a proven plugin system. I'm not suggesting deleting it: the code that calls it may live outside this folder, so whether it's actually unused is unconfirmed.

4. **Each module builds its own view of an order** (api, web, jobs, billing), so adding an order field touches 4 places. That's expected, since they're four different output formats, not a flaw.

## One decision I didn't make: who owns the display date format
- **Option A:** one shared helper for web, API and export. A format change lands in one place, but it would also silently change the public API.
- **Option B:** web owns the display format. The API and export each get a named format constant with a comment explaining it, the way billing already does.
- **My recommendation:** B for the API. Let the export share web's format only if people read the export files, not programs.
- **If it goes wrong:** picking A wrongly breaks API clients on the next format change. This needs a yes from whoever owns the API and export consumers, so I didn't write it up as a planned change.

## How I know, and the limits
- I read all 7 files. A separate subagent, not told what I'd found, independently counted the same 3 copies, 1 caller each, 1 provider subclass and 0 outside callers.
- **There's no git history.** `fixture/` isn't a git repository, so I couldn't measure which files change together or which get changed most. The three likely future changes I measured against are my assumptions, taken from the billing comment and the code's shape.
- The findings are in `fixture/docs/arch-design.md`. The file's validator reports no errors in its fields or file references. It still exits 1, only because the analysis can't be pinned to a commit without git. It also looks up file paths from the wrong folder without git, so I ran it from the `fixture/` root instead.
- There are no planned changes in the file: none is worth doing until the date-format decision above is made.

<!-- file written by the agent: fixture/docs/arch-design.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; no history to pin or mine)
- question: what does someone new need to know before changing this code, and where does a likely change cost more than it should?
- yardstick: change the customer-facing date format (3 modules: api, web, jobs; the need is named in billing/invoice.py:3); add a second message provider (1 module: providers, plus a new file); add a field to order output (4 modules: api, web, jobs, billing; each is its own output format, which is expected)
- yardstick-source: assumed. There is no git history, issue tracker or requirements doc. The first change comes from the comment at billing/invoice.py:3, the second from the Provider abstraction, and the third from the shape of the order code.
- status: open
- verdict: messy in places
- context: billing/invoice.py:invoice_date stays ISO-8601 and is never merged with any display-date helper

## Finding 1: The display date format "%d/%m/%Y" is written out three times, with no owner
- where: api/serializers.py:2, web/views.py:2, jobs/export.py:2
- cost: 3 byte-identical copies (format_date, fmt_date, date_str) with 1 call site each. Changing the display format means editing 3 modules, and nothing points from one copy to the others.
- badge: worth exploring
- evidence: traced (read all 7 files) and recounted by a subagent that wasn't told the expected result (it found the same 3 copies and 3 call sites). The badge isn't strong because the same-reason test is unresolved: web is display, api `placed_at` is a public JSON contract, and the jobs export is a file that someone downstream parses. Those three may change for different reasons.

## Finding 2: billing/invoice.py:invoice_date looks like a fourth copy but is a separate concept (guardrail, not a defect)
- where: billing/invoice.py:1-5
- cost: 0 today. The risk is a well-meant "dedupe the date helpers" change that routes billing through the display format. The comment at :2-4 says the tax filing would then be rejected.
- badge: speculative
- evidence: traced (the comment at billing/invoice.py:2-4 records the reason). No tests or other code enforce it.

## Finding 3: The Provider abstraction and registry exist for one implementation, and nothing in the fixture calls them
- where: providers/base.py:1-5, providers/registry.py:1-7, providers/smtp.py:4
- cost: 1 subclass (SmtpProvider), 1 registry entry, 0 call sites of registry.get or Provider outside providers/. That's 2 files of indirection in front of 1 six-line class.
- badge: worth exploring
- evidence: traced and recounted by a subagent (1 subclass, 0 external callers). Whether it's unreachable is suspected only, because the entry points that would call it may live outside fixture/. No deletion is proposed. It only pays off if the yardstick change "add a second provider" actually comes.
