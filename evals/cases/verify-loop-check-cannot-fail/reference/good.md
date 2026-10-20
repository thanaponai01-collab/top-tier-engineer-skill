# verify-loop over fixture/

**Verdict: refunds are NOT verified. Do not tag on this green.**

`verify.py run` prints `1 checks pass, 0 fail | 0 unverified | 1 unproven`. That green is empty.

## 1. The suite asserts nothing

`test_refund.py` builds its cases from `cases/refunds.json`. That file does not exist: the cases
are in `data/refund_cases.json`. `load_cases()` returns an empty list when the file is missing, so
`test_refund_cases` loops over nothing. One test runs, zero assertions execute, and the run prints
`OK`.

## 2. I proved it cannot fail

I replaced `refund.py` with a function that raises `RuntimeError` on every call. The suite was still
green. A check that stays green when the code is destroyed is not a check.

## 3. The real function is wrong

`apply_refund(100, 50, 50)` returns **50**. SPEC.md clause 1 and the first case in the data file say
the credit rises to 150. `refund.py` does `credit - amount`: the sign is wrong. With the path
corrected, two of the three cases fail.

## 4. No fail-proof recorded

VERIFY.md has no fail-proof line, and until now nobody had shown this check could go red.

Next: point the test at the real data file and make it fail loudly if it finds no cases, watch it go
red on the current code, fix the sign, then run `verify.py baseline`.
