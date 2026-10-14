# SPEC.md: done

Playbook: build a specified feature locally; nothing to release. RUN.json records the run.

**Who built it.** I read the routing policy and kept the work in this session (Opus) rather than
dispatching `drive-executor`: the modules are small and tightly linked through the cart totals, so
briefing a worker and re-checking its diff would have cost more than writing them. No subagent ran.

**What changed.** `shop/cart.py` and `shop/invoice.py`, plus new `shipping.py`, `inventory.py`,
`orders.py`, `giftcards.py` and `loyalty.py` under `shop/`.

**Proof (proven: run after the last edit).**
- `python acceptance/check.py` → `ACCEPTANCE: 21/21 passed`, exit 0.
- `python -m unittest` → the three existing tests pass.

`acceptance/check.py` was not touched.
