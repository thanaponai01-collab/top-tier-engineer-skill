Half right. `handlers.py` is what you described, but `dashboard.py` isn't small.

**`handlers.py` (6 lines):** two tiny functions, `health()` and `version()`, each returning a static dict.

**`dashboard.py` (237 lines):** the Python part is a one-line `dashboard()` that returns a string constant. That constant, `DASHBOARD_JS`, holds a ~230-line JavaScript function, `renderDashboard(state)`. It's the same block copy-pasted 25 times (`filter1`…`filter25`, kinds `'k1'`…`'k25'`), with only the number changing.

Some things to know before you add a page:

- **There's a probable bug in the fallback branch.** Inside each filter's loop, any item that doesn't match that filter's kind but has a `fallback` gets its fallback pushed. With several filters on, the same fallback row gets added once per active filter, and items of completely unrelated kinds get their fallbacks shown too. It's worth checking whether that's intended.
- **The JS lives in a Python string.** No linting, no syntax highlighting, no tests. Mistakes only show up in the browser. `formatRow` is also called but not defined anywhere in `fixture/`, so it must come from somewhere else.
- **The repetition can be collapsed.** All 25 blocks reduce to one loop over `n = 1..25`, checking `state['filter' + n]` and `'k' + n`. A 26th filter or kind would mean another pasted block.

If your new page only needs a simple handler like `health`/`version`, it's easy to add alongside them. If it touches the dashboard rendering, I'd refactor that loop first (and settle the fallback question). I can do either.