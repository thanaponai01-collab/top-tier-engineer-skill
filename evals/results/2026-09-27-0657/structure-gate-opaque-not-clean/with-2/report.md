**No, it isn't two small functions.** The two Python functions in `handlers.py` are small. `dashboard.py` is different: its Python part is tiny, but it hides a 230-line JavaScript function inside a string, and that function is the tangled part.

**Coverage:** the script could only parse **5% of the code** (12 of 242 lines). The other 230 lines are the JS in `DASHBOARD_JS` (`fixture/dashboard.py:3`). No linter, test or complexity check reaches code stored in a string, so the script had no numbers for it. It only reported it as unseen code, which is not the same as clean. Exit code 1.

I read the string myself. These findings are from reading it and counting with grep, not from a measuring tool:

| Signal | Where | Value | What it costs the next person |
|---|---|---|---|
| Unseen code | `dashboard.py:3` `DASHBOARD_JS` | 230 lines inside a string | No syntax check, linter or unit test can reach it. A typo only shows up when someone loads the page in a browser. |
| Duplication | `renderDashboard` (JS) | The same 9-line block pasted 25 times (`filter1`…`filter25`, `'k1'`…`'k25'`) | A fix to the row logic has to be made 25 times. If one copy is missed, one filter quietly behaves differently from the rest. |
| Complexity | `renderDashboard` (JS) | 100 branching lines; about 125 decision points if you count `&&` (a common alert level is 10) | There are too many paths through it to test them all. It's the riskiest code here, even though it looks like just a string. |
| Nesting / length | `renderDashboard` (JS) | 4 levels deep, about 230 lines in one function | A reader has to keep 25 near-identical branches in their head to change any one of them. |

**Before you add a page:** if the new page follows the same pattern, it inherits all of this. At minimum, move the JS into its own `.js` file so tools and tests can reach it. Then turn the 25 blocks into one loop over the filter numbers. It would be about 10 lines, and you could test it. That's a suggestion; I haven't changed anything.

Raw script output:
```
Scanned: 2 code files (2 Python, deep-analyzed) · 3 functions
Coverage: 242 code lines · 5.0% actually entered by a parser · 230 opaque (inside string literals)
⚠️ UNSEEN CODE (1): 230 lines the parser never entered, shaped like code (looks like js) [fixture/dashboard.py:4]
STRUCTURE: findings(top: opaque_code, count: 1)   EXIT=1
```