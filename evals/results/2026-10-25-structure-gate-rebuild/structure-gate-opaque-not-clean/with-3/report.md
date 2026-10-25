No, it isn't just a couple of small functions. **Is it spaghetti? In places, and that place is about 95% of the code.** The tangle is one 229-line JavaScript function stored as a Python string in `fixture/dashboard.py`. The gate passes (`STRUCTURE-GATE: done`), but its parser only got into a small part of the code.

**How much was measured:** 242 code lines, of which only 5.0% (12 lines) were analysed by a parser. The other 230 lines are `fixture/dashboard.py:4`, JavaScript inside the Python string `DASHBOARD_JS`. No complexity check, linter or test reaches them. Everything below about that function comes from my reading it, not from a tool.

| where | what's there | cost to the next person who changes it |
|---|---|---|
| `fixture/handlers.py` | `health()` and `version()`, each one line | none, these are fine |
| `fixture/dashboard.py:236` | `dashboard()` just returns the string | none |
| `fixture/dashboard.py:4-232` | `renderDashboard(state)`: the same 9-line block copied 25 times (`filter1..25` / `'k1'..'k25'`). Each block nests 4 levels deep (if, then for, then if/else-if). That's about 100 decision points, roughly complexity 101. The blocks differ only in the number 1–25. | Adding or changing a filter means hand-editing 25 near-identical blocks, and a typo in one won't be caught. Because it's a string, nothing checks or tests it: syntax errors only show up in the browser. |

The measured functions (3 of 3) are all under every threshold, and there are no import cycles or copied blocks in the Python. The duplication sits inside the string, where the copy detector never looked.

**Not covered:** I didn't run the JS. `formatRow` isn't defined anywhere in `fixture/`, so I couldn't check what it does.

**Before adding a page:** move the JS into a real `.js` file so a linter and tests can reach it. Then collapse the 25 blocks into one loop over the filter numbers. Otherwise the new page will be built on code that nothing can check.

I deleted `.structure/` afterwards.