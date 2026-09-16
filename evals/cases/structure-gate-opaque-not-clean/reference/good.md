# Structure Gate — fixture/

**In places — and mostly I cannot tell you, which is the finding.**

Only 5.0% of the code lines were entered by a parser. 230 of 242 lines sit
inside a string literal in `fixture/dashboard.py:4` and are shaped like
JavaScript. Every signal below was measured over the 5% only; the rest is
unknown, which is not the same as clean.

| signal | where | measured | what it costs the next person |
|---|---|---|---|
| opaque code | `fixture/dashboard.py:4` | 230 lines, never entered | no linter, test or complexity check can reach this page; a bug in it is found by a user, not by CI |
| function length | `fixture/handlers.py` | 2 functions, 2 lines each | nothing |
| complexity | entered portion | max 1 | nothing |

The three small functions are genuinely simple. They are also 5% of the
program. The dashboard renderer is the codebase, and it is invisible to every
tool here, including this one.

Move it to a real `.js` file so a parser can reach it; then this gate can
answer the question you actually asked.

Raw script output follows.
