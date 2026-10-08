**Verdict: messy in places, not tangled.** The codebase is small (7 files, about 35 lines). Outcome chosen: **Improve**, because the problems are local. You can override that.

## What a newcomer should know

**1. `billing/invoice.py:5` is deliberately different. Don't "tidy" it.**
- It formats dates as `%Y-%m-%d`. The other three date formatters use `%d/%m/%Y`.
- The comment at `invoice.py:2-4` says the tax authority's upload spec fixes ISO-8601, and a change "rejects the whole filing."
- The four formatters look like duplicates, but this one changes for a different reason. A naive "merge all date helpers" refactor would break tax filings.
- Status: **traced**. I read the comment, but there is no test guarding it. I'd add one before anyone touches dates.

**2. The customer-facing date format exists in three copies.**
- The copies are `web/views.py:1` (`fmt_date`), `api/serializers.py:1` (`format_date`) and `jobs/export.py:1` (`date_str`). All use `%d/%m/%Y`.
- Changing the display format means editing 3 files, and missing one gives inconsistent output.
- The same-reason test passes for the web and API copies. Both are "how a customer sees a date."
- The export job is less certain. If its CSV is read by machines or other systems, it may need its own format. Ask its owner before merging it.
- This is the best-value move, since a date-format change is the likeliest next change. Status: **traced**.

**3. The provider abstraction is speculative, but harmless.**
- `providers/base.py:1`, `registry.py:3` and `smtp.py:4` form a base class, a registry and one implementer.
- `base.py:1` says "Implemented once," and the registry's `get()` defaults to `"smtp"`.
- One implementer is a guess, not a fact. Deleting the base class and registry would collapse the complexity, but it's only about 10 lines of savings.
- I couldn't check why it exists. The directory isn't a git repo, so there is no history, and I haven't proven it's unused. I propose **no deletion**. If a second provider is planned, keep it.
- Nothing in `fixture/` calls `registry.get()`, so the callers are outside what I audited. Check them before changing it.

## Ranked moves

**Move 1 (improve): one owner for the customer-facing date.**
- Steps:
  1. Add a `display_date` function in one shared module.
  2. Point `web/views.py` and `api/serializers.py` at it, one file per landing.
  3. Do `jobs/export.py` last, and only if its output is meant to match what customers see.
- Leave `billing/invoice.py` alone.
- Second option: do nothing and add a comment in each file. That is cheaper, but the 3-file edit cost stays.
- Door: two-way, because it's a function location.
- Proof:
  - Before step 1, add a test pinning `invoice_date` to `2026-10-08` and a test pinning the display format to `08/10/2026`.
  - Run those tests after each step.
- Payoff: changing the display format goes from 3 files to 1.

**Move 2 (tidying): leave the provider layer as is.**
- Revisit it only when a second provider is or isn't coming.

## Risks
- **No tests are visible.** The fixture has none, so the invoice format has nothing guarding it.
- **No history.** I couldn't check for past decisions beyond the comment in `invoice.py`.