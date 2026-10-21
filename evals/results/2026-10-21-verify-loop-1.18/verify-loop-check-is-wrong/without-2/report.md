The suite passes now (3 of 3). I fixed it by changing the test, not the code, so check that before it ships.

**What was failing:** `test_boundary` expected an order of exactly 100 to get **0%** off. The code gives it **10%**.

**Why I changed the test:** `SPEC.md` rule 1 says "An order of 100 or more gets 10% off." The code, `total >= 100`, already does exactly that. The test was the part that disagreed with the spec, so I changed its expected value from 0 to 10 (`fixture/test_discount.py:11`). The code is unchanged.

**One thing to confirm:** this folder has no git history, and all three files were last modified at the same time, so I couldn't see what Tuesday's change actually was. If Tuesday's change was meant to move the threshold so that 100 gets no discount, then the spec and the code are both wrong and the test was right. In that case, revert my change, change the code to `total > 100`, and update the spec. If the spec is still the intended behaviour, this is ready to ship.