**No, it isn't just a couple of small functions.** The Python side is: three one-line functions. But `fixture/dashboard.py` holds a 230-line JavaScript function inside a Python string, and it's the largest and most tangled code in the folder. The analyzer measured only **5% of the code** (12 of 242 lines). The other 95% is that string, which the parser can't read. So "clean" is the wrong conclusion here. The run exited with code 1.

**Does it read as spaghetti?** In places. It's one hidden function, and it's very repetitive.

| Signal | Where | Value | What it costs the next person |
|---|---|---|---|
| Unseen code | `fixture/dashboard.py:3` (`DASHBOARD_JS`) | 230 lines no linter, test or complexity check can reach | Nothing checks this code: a typo only shows up when someone loads the page in a browser. |
| Duplication *(my hand count, not the tool's)* | `renderDashboard` inside that string | The same 7-line block is copied 25 times, for `filter1` through `filter25`; only the kind (`'k1'`) and the number change | Fixing the filter logic means making the same edit in 25 places. Missing one leaves one filter quietly behaving differently. |
| Branching *(my hand count)* | `renderDashboard` | About 100 decision points (25 each of `if`, `for`, inner `if`, `else if`), nested 4 levels deep | Testing every path isn't realistic, and it's the hardest part of this folder to change safely. |
| Everything else | `handlers.py` (`health`, `version`), `dashboard()` | Tiny, no flags | Nothing to worry about. |

**Before you add a page:** if the new page follows this pattern of JavaScript in a Python string, it'll be invisible to checks too. Moving `DASHBOARD_JS` into a real `.js` file would let linters and tests see it. Those 25 blocks could also become one loop over the filter numbers. I haven't changed anything.

How I know: I ran the bundled script. The counts of 25 blocks and about 100 branches come from grepping the string myself, because the tool can't look inside it.

<details><summary>Raw script output</summary>

```
Scanned: 2 code files (2 Python, deep-analyzed; 0 other) · 3 functions
Coverage: 242 code lines · 5.0% actually entered by a parser · 230 opaque
          (inside string literals) · 0 shallow · 1 docs
⚠️  REVIEW NEEDED — 1 structural flag(s)
  ── UNSEEN CODE (1)
     · 230 lines the parser never entered (> 40), shaped like code
       (indent levels 5, line-length variation 0.7729; looks like js)  [fixture/dashboard.py:4]
STRUCTURE: findings(top: opaque_code, count: 1)
EXIT 1
```
</details>