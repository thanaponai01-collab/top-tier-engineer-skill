**Outcome: Improve.** The structure is sound. I read all 7 files (about 40 lines), so these findings are *traced*, and I didn't run anything. There's no git history or tracker here, so I couldn't check why things exist. My guess at the next likely changes is that the customer-facing date format changes, a second mail provider is added, and the tax filing format changes. That's an assumption, not something I found in the repo.

**Verdict: clean, with one trap.** The one move that pays off most is to give the three display dates a single owner, and to leave the invoice date alone.

## What a newcomer should know

1. **`billing/invoice.py:5` looks like a copy of the other date helpers, but it isn't one. Don't merge it.**
   - Three functions format the display date identically as `%d/%m/%Y`:
     - `web/views.py:1`
     - `api/serializers.py:1`
     - `jobs/export.py:1`
   - `invoice_date` uses `%Y-%m-%d`. The comment at lines 2–4 says the tax authority's upload spec fixes that format, and that changing it rejects the whole filing.
   - The same-reason test splits them. The three display helpers change when the customer-facing format changes. The invoice helper changes only when the tax spec changes.
   - A well-meaning "dedupe all the date helpers" cleanup would break tax filings. Nothing enforces this: there are no tests in the fixture, and only the comment guards it.

2. **The display date has three owners (traced).**
   - If the customer-facing format changes, you have to edit 3 files and 3 separate functions. If you miss one, the web page, the API and the export show different dates.
   - The three share one reason to change, so they should be merged.
   - **Better shape:** a single `fmt_date` in a small shared module. Web, API and export import it. Billing does not.
   - **Option B:** leave them as they are. That's cheap now, but a format change stays at 3 edits with a silent-divergence risk.
   - **Door:** two-way. It's a function location.
   - **Steps:**
     1. Add the shared helper.
     2. Point `web/views.py` at it.
     3. Do the same for `api/serializers.py`, then `jobs/export.py`.
     4. Delete the 3 copies.
   - **Proof:** compare the outputs of `order_page`, `order_json` and `rows` before and after on the same input. They should be identical. A new test should also pin `invoice_date` to `%Y-%m-%d`, so nobody can merge it by accident. Changing the display format then takes 1 edit instead of 3.
   - **Caveat:** the API serializer and the CSV export are machine-consumed. A consumer may depend on `dd/mm/yyyy`, so a format change there could break a consumer that the web page wouldn't. If those should be able to diverge from the web page, they may not share a reason to change, and the merge would be wrong. I couldn't check who consumes them.

3. **The provider abstraction is speculative (traced).**
   - `providers/base.py` says "Implemented once, by SmtpProvider". `providers/registry.py:3` has a one-entry dict, and `get()` defaults to `"smtp"`.
   - That's one implementer, which is a guess rather than a fact. By the deletion test, the base class and registry would collapse into `SmtpProvider` with little left over.
   - Nothing in the fixture calls `registry.get`, so I couldn't see where it's used, and I couldn't check why it exists. The base class and registry may be a seam someone planned for a second provider.
   - **Recommendation:** don't delete it, and don't extend it either. It's about 15 lines, so the cost is low.
   - Add the second provider when it actually arrives. The existing shape will be fine for that.
   - Until then, treat the seam as unproven. Be cautious about adding options or methods to `Provider` that only one implementation would use.
   - Proving it unused is `latent-audit`'s job.

## Before Monday, in order
1. Read the comment at `billing/invoice.py:2-4`. Never touch invoice dates when changing display formats.
2. Add a test that pins the invoice date format. It's the cheapest protection here.
3. Do the date consolidation in item 2, for the web, API and export dates only.
4. Leave the provider seam alone until a second provider exists.

I didn't change any files.