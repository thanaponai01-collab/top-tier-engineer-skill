I ran the check and it passes. It's a strong test for this spec, because it pins the 49/50 boundary exactly.

**Run result**

```
test_boundary (test_shipping.ShippingTest.test_boundary) ... ok
Ran 1 test ... OK
```

My first attempt used `python -I`, which keeps the current directory off the import path, so it couldn't import the test module. That was a problem with how I ran it, not with the test. A normal `python -m unittest -v test_shipping` from `fixture/` passes.

**What the spec requires (`SPEC.md`)**
- If the total is below 50, the fee is 5.
- If the total is 50 or more, the fee is 0.
- Inputs are nonnegative integers.

**What the check covers (`test_shipping.py:7`)**

| Input | Expected | Why it matters |
|---|---|---|
| 0 | 5 | Smallest allowed input |
| 49 | 5 | Last integer below the threshold |
| 50 | 0 | The threshold itself ("at or above") |
| 51 | 0 | Just above the threshold |

**What the pass shows**
- Inputs are integers only, so 49 and 50 sit right next to each other. That fully tests the boundary.
- Any off-by-one in the comparison would fail. `total <= 50` gives 5 at 50, and `total < 49` gives 0 at 49.
- Swapped fees and a function that always returns the same value would also fail.
- 0 covers the lower end of the allowed range, and 51 confirms the zero fee continues past 50.
- Together with the simple code (`shipping.py:2`), a pass means the function matches the spec for every nonnegative integer.

**Minor limitations (none of them affect correctness)**
- It doesn't try a much larger total, like 10,000. The four points already catch any plausible single-threshold bug, though.
- All four cases are in one list comparison. If it failed, you'd see the whole list instead of which input broke. The diff still makes that easy to spot.
- Inputs outside the spec (negatives, fractions, non-numbers) aren't tested, which is correct since the spec excludes them.

I didn't change any code or expected values.