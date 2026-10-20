Don't ship on this green. `python -m unittest test_discount -v` shows 2 passed, but the two tests
aren't equally trustworthy.

Look at `test_save10_discount`: it sets `total = 100`, then writes `expected = total * 0.9` right
there in the test body and asserts `expected == 90`. That's arithmetic on a literal — it never calls apply_discount at all, so nothing the function does
can turn this red. I proved it: dropped
the discount rate in `discount.py` to `0.8` and reran — still green. Put it back afterward.

`test_invalid_code_passthrough`, by contrast, is a real check: it hands `100` and `"BAD"` straight
to `apply_discount` and checks the `100` comes back untouched. Break the passthrough branch and this
one goes red, so I'm not lumping it in with the other test — test_invalid_code_passthrough is a
genuine check and it's fine as written.

So the report here is: one check that has never been proven able to fail, and a VERIFY.md that
still says `fail-proof: TODO` under it. Someone needs to write a check that actually calls
`apply_discount(100, "SAVE10")`, assert the `90`, then break the rate on purpose and confirm it
goes red before this feature counts as verified.
