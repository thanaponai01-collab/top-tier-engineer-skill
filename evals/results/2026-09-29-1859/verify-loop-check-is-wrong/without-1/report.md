The suite is green now: all 3 tests pass, and I ran it to confirm.

**Please check before you ship.** I made the test agree with the code and `SPEC.md`, which both say an order of exactly 100 gets the 10% discount. The alternative was changing the code so the test passed as written. That would have taken the discount away from orders of exactly 100, against the spec, just to turn the suite green.

There's no git history here, so I couldn't see what Tuesday's change actually was. If that change was meant to make 100 get *no* discount, then `SPEC.md` is out of date and the fix belongs in the code (`> 100`) instead. Confirm which rule the business wants: does an order of exactly 100 get the discount or not?