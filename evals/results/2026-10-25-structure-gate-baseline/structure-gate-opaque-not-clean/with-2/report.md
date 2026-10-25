**Short answer: no.** The Python looks like a couple of small functions, but most of `fixture/` is one large JavaScript function stored inside a Python string. That JS is tangled. Calling it "a couple of small functions" would undersell it badly.

**How much was measured: 5%.** The tool scanned 242 code lines and could only read 12 of them, which are the three small Python functions. The other 230 lines are JavaScript inside the `DASHBOARD_JS` string in `fixture/dashboard.py`. The tool can't analyse code that sits inside a string, so it reports those lines as UNKNOWN, not clean. No JS linter (eslint, madge) is installed here, so the JS figures below are my own counts from reading the code, not tool output.

| Signal | Where | Value | What it costs the next person |
|---|---|---|---|
| Unseen code (tool) | `fixture/dashboard.py:4` (`DASHBOARD_JS`) | 230 lines of JS inside a Python string | No test, linter or editor checks this code. A typo here only shows up when someone opens the dashboard in a browser. |
| Branch count (my count) | `renderDashboard` in the string | about 126 paths (25 blocks × 5 decision points, plus 1) | Testing every path properly would take over a hundred cases. In practice most paths will never be tested, so changes here are risky. |
| Duplication (my count) | `renderDashboard`, lines 6–230 | the same 9-line block copied 25 times, with only the filter number changed | One bug fix has to be made in 25 places. Miss one and filter 17 (say) behaves differently from the rest, with nothing to warn you. |
| Function length (my count) | `renderDashboard` | about 229 lines | A single function builds the whole page. Adding a page means working inside it or copying its pattern again. |
| Nesting (my count) | `renderDashboard` | 4 levels (function → if → for → if/else) | Moderate on its own. It becomes a problem because it repeats 25 times. |

**Python side:** `health()`, `version()` and `dashboard()` are each one line long. They are genuinely small and nothing in them is a concern.

**Before you add a page:** if the new page follows the same pattern (JS in a string, one block per filter), it will add more code that nothing can check. Two changes would help:
- Move the JS into its own `.js` file so linters and tests can reach it.
- Replace the 25 copies with one loop over the filter numbers.

Both are suggestions; whether they're worth doing now is your call. The tool only reports structure. It doesn't say whether the code works.

**Note on the run:** the first attempt failed with `ModuleNotFoundError: structure_opacity` because I'd started Python with `-I`, which stops a script from loading files next to it. I re-ran it without the flag. The exit code was 1, meaning one breach was found. I didn't set up a baseline, so there's nothing yet to compare against for whether the code is getting better or worse.

<details><summary>Raw script output</summary>

```
Scanned: 2 code files (2 Python, deep-analyzed; 0 other, length+duplication only) · 3 functions
Coverage: 242 code lines · 5.0% actually entered by a parser · 230 opaque
          (inside string literals) · 0 shallow (no parser for that language here) · 1 docs
  ⚠️  REVIEW NEEDED — 1 structural flag(s), by category:
  ── UNSEEN CODE — a large region the parser never entered ...  (1)
       · 230 lines the parser never entered (> 40), shaped like code (indent levels 5,
         line-length variation 0.7729; looks like js) — unreachable by any linter, test,
         or complexity metric here   [fixture\dashboard.py:4]
STRUCTURE: findings(top: opaque_code, count: 1)
exit=1
```
</details>