**Verdict: messy in places.** This is a small codebase (7 files, about 35 lines), and it's mostly fine. The one thing a newcomer must know is that one date format must not be merged with the others. I chose **Improve** because the problems are local, and I read every file (traced). There's no git history and no tracker here, so I couldn't check why anything exists. The "likely next changes" below are my assumptions, not requirements.

## What to know before changing things

**1. `billing/invoice.py:2-5` is a trap. Don't "dedupe" it with the other date functions.**
- The comment says the format is fixed as ISO-8601 by the tax authority's upload spec. Changing it "rejects the whole filing."
- It looks like the same helper as three others, but it changes for a different reason. That's the same-reason test.
- Today it's `%Y-%m-%d`, and the other three are `%d/%m/%Y`. A shared `format_date` would make a future display change, such as a locale switch, break tax filings.
- Nothing in the repo enforces this. Only the comment protects it, and no test pins the format. That is the highest-risk gap.

**2. The display date is defined three times, byte-identical.**
- The copies are `api/serializers.py:1`, `web/views.py:1` and `jobs/export.py:1`, all `%d/%m/%Y`.
- A "change the date format" request means touching 3 files, and missing one gives inconsistent output between API, page and export.
- Same-reason test:
  - The API and web copies are both customer-facing display, so one owner is right.
  - The CSV export (`jobs/export.py:5-6`) may be a different case. A machine-read export often wants a stable format regardless of display preferences. Ask who consumes it before merging it.
- **Option A:** one `format_date` shared by the API and web, with the export and invoice left alone. It's the simplest and safest.
- **Option B:** all three share it. That's less code, but it's riskier if the export has downstream parsers.
- This is a two-way door, so decide it in a line. Check the export's consumers first.

**3. The `providers/` package is more structure than the code needs.**
- `providers/base.py` is an interface that says "Implemented once", `providers/smtp.py` is its one implementer, and `providers/registry.py:3` is a one-entry registry.
- By the deletion test, inlining all three into one `send_smtp` function would remove two files and one dispatch layer, and nothing would move elsewhere. One implementer is a guess.
- Nothing inside `fixture/` imports `registry.get`, so I can't tell whether it's used from outside or is dead (suspected, not proven). I have no history for why the abstraction was added. It may be a planned second provider.
- **Recommendation:** don't delete or inline anything yet. Find out whether a second provider is coming. If it isn't, inline later as a two-way move.

## Moves, ranked

1. **Pin the tax format with a test.** Add a test that `invoice.line()` outputs `id|YYYY-MM-DD`.
   - Proof: the test fails if someone changes `invoice_date`.
   - This is the highest value because a silent break rejects a whole filing.
   - It's cheap and has no behavior change.
2. **Merge the API and web display date helpers** into one module (Option A above).
   - Format change goes from 3 files to 2, or to 1 if the export is also merged.
   - Proof: a test that the API and the page render the same date string for one order.
3. **Decide on `providers/`** once you know whether a second provider is planned. This is tidying until then, so skip it if one is.

I made no changes. Because nothing in `fixture/` is shown to call `providers.registry`, check any callers outside `fixture/` before touching it.