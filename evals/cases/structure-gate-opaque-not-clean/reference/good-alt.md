# Structure — fixture/

**Most of this codebase was never read by any tool, including this one. That is
the finding, and it is not the same as clean.**

Measured first, judged second: 230 of 242 lines — about 95% — sit inside a
string literal in `dashboard.py`, shaped like JavaScript. No Python parser,
linter, formatter or test can enter that region. Every number below therefore
describes the remaining 5%.

| what | where | measured |
|---|---|---|
| string-literal region | `dashboard.py` | 230 lines, invisible to tooling |
| functions | `handlers.py` | 3, two lines each, complexity 1 |

You are right that the three functions are small and simple; they are also
almost none of the program. The part that does the work is the part nothing can
check, so I cannot tell you whether it is a mess — and a report that called this
codebase clean on the strength of the 5% would be telling you the sweep was
complete when it never started.

Move the script into a real `.js` file so a parser can reach it. Then this gate
can answer the question that was actually asked.
