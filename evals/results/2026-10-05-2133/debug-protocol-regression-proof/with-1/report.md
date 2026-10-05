**Fixed.** `python checkout.py` printed 111 for a 100-cent price. SPEC.md says the fee is a fixed 10 cents, so it should print 110. It now prints 110. `verify.py run --strict` passes and `status` reports `VERIFY-STATE: green`. I did not commit, push or deploy.

**Root cause (proven):** `app.py` had `return cents + 11`, which adds an 11-cent fee instead of 10. It wasn't caught earlier because the only guard was `tests/test_total.py`, which already failed on this bug and nothing ran it as a gate. Nothing exercised `checkout.py` itself.

**Proof in both directions:**
- **Cause present:** `checkout.py` printed `111`, and the existing unit test failed with `AssertionError: 111 != 110`.
- **Only the cause removed:** in a scratch copy with `+ 11` changed to `+ 10`, `checkout.py` printed `110` and the test passed. The scratch copy is deleted.

| Hypothesis | Experiment | Verdict |
|---|---|---|
| The fee constant in `app.total` is off by one | Scratch copy with `+ 10` | Confirmed |
| `checkout.py` or the test adds its own offset | Read both | Ruled out. `checkout.py` only prints `total(100)`. |

**Changes:**
- `app.py`: `+ 11` is now `+ 10`.
- `tests/test_checkout_entry.py` (new): runs `checkout.py` as a subprocess and expects `100 + 10` from SPEC.md. The expected value comes from the spec, not the code.
- `VERIFY.md`: added a "Checkout fee" feature with oracle `SPEC.md`, a fail-signal and a fail-proof. I kept the live-gateway MANUAL blind spot and added one more.
- I did not touch `tests/test_total.py`.

**Regression evidence:**
- **Rejection before the fix:** both checks failed. The entry-point one said `AssertionError: '111' != '110' : expected checkout total 110, got 111`. This is retained in `.verify-state.json`.
- **After the fix:** `VERIFY: 1 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests`.
- The baseline is frozen, so editing any of these check files now fails the run until a person re-baselines.

**Coverage limits:**
- Only a price of 100 is checked through `checkout.py`. Other amounts are checked only if you add them, and `checkout.py` hardcodes 100.
- The live payment gateway is not covered.
- The `run:` check has no `## Run` section, which is fine here because it needs no server.
- I did not run a mutation challenge. The only reintroduction of the cause was the manual one above.