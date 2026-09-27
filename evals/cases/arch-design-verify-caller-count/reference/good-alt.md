# Architecture note — shipping/

Verdict: messy in places, and it is not clear to delete yet.

`shipping/base.py` defines `ShippingCalculator`. `shipping/flat_rate.py`'s
`FlatRateCalculator` is the only class that implements it — this is the
"built ahead of need" shape: one implementation, and nothing in the
requirements calls for a second carrier.

That does not make it dead. I checked every place the registry function is
reached, not just where it is spelled the same way. `checkout/cart.py` calls
`get_calculator("flat")` directly. `jobs/reprice.py` imports the very same
function under a different local name — `get_calculator as pick_calc` — and
calls it as `pick_calc("flat")`. A search for the literal text
`get_calculator(` finds only the first one; tracing the import statement
finds the second. Two places depend on this seam, not one, so deleting it
without updating `jobs/reprice.py` would break the nightly reprice job.

## Move

Inline `ShippingCalculator`/`FlatRateCalculator` into `shipping/registry.py`
as a plain function, and update both dependents:
- `checkout/cart.py` (`get_calculator("flat")`)
- `jobs/reprice.py` (imported as `pick_calc`, called on its own line)

Proof: run both `total_with_shipping` and `reprice_open_orders` before and
after the change and confirm the quotes are unchanged. Two-way door — nothing
outside the codebase depends on the class shape.
