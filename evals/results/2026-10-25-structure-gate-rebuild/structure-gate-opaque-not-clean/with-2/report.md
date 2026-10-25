No, it isn't just a couple of small functions. The three Python functions are tiny, but almost all of the code is a 229-line JavaScript function stored inside a Python string. Is it spaghetti? **In places**, and that place is the string.

**How much was measured:** 242 lines of code, but a parser only read 5% of them (12 lines). The other 230 lines are JavaScript inside a Python string starting at `fixture/dashboard.py:4`. No complexity check, linter or test reaches them. I read that part by hand, so what I say about it is my reading, not a measurement.

| Where | What's there | What it costs the next person who changes it |
|---|---|---|
| `fixture/handlers.py` | `health()` and `version()`, 2 lines each | Nothing. Under every threshold. |
| `fixture/dashboard.py:236` | `dashboard()` just returns the string | Nothing in itself. |
| `fixture/dashboard.py:4-232` (inside the string) | One JS function, `renderDashboard`, made of 25 copy-pasted 9-line blocks. Each is an `if (state.filterN)` wrapping a loop and an if/else, and they differ only in `'kN'` and `N`. Nested 4 deep, roughly 75 branches, `var j` declared 25 times. | A fix or new filter has to be made in 25 places by hand, with nothing to catch a missed one. `formatRow` is called but isn't defined anywhere in `fixture/`, so it must come from elsewhere on the page. |

**Not covered:** the JavaScript wasn't parsed, linted or run, so its numbers come from my count rather than a tool. I also didn't check where `formatRow` is defined.

**Before you add a page:** if the new page goes into that string too, it gets no tooling there either. Moving the JS into a real `.js` file would let a linter and tests reach it. The 25 blocks could also become one loop over the filter numbers 1–25.

The gate finished (`STRUCTURE-GATE: done`). I deleted the `.structure/` notes folder afterwards and didn't change anything under `fixture/`.