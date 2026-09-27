# Architecture Audit — fixture/

**Messy in places.** The shipping seam is a built-for-"gonna need" abstraction,
but it is not yet safe to inline — a second caller was hiding behind a
renamed import.

`shipping/base.py:1` (`ShippingCalculator`) has exactly one implementation,
`shipping/flat_rate.py:4` (`FlatRateCalculator`), and no requirement here asks
for a second carrier. That's the shape of an interface built ahead of need.

Before clearing it to inline, I counted every caller of the registry seam, not
just the literal text `get_calculator(`. `checkout/cart.py:4` calls it
directly. `jobs/reprice.py:2` reaches the same function through
`from shipping.registry import get_calculator as pick_calc` and calls it as
`pick_calc(...)` at `jobs/reprice.py:5` — a plain grep for `get_calculator(`
would have missed that call site entirely. Two callers, not one.

| # | sign | where | what it costs today | move | effort | badge |
|---|---|---|---|---|---|---|
| 1 | built for "gonna need" | shipping/base.py:1 | one implementation, no second caller of the abstraction itself | inline `ShippingCalculator`/`FlatRateCalculator` into the registry, update both callers | S | Worth exploring |

## Moves

Context: no second shipping carrier is in scope for this move.

### 1. Inline the shipping abstraction
cost:     a layer that only forwards to one implementation, no cost felt yet
files:    shipping/base.py:1, shipping/flat_rate.py:1, shipping/registry.py:1
owner:    shipping/registry.py keeps `get_calculator`, returns a plain quote
          function instead of a class instance
callers:  checkout/cart.py:4 (`get_calculator("flat")`), jobs/reprice.py:2
          (imported as `pick_calc`, called at jobs/reprice.py:5)
door:     two-way — internal reshuffle, nothing outside the codebase depends
          on the class shape
proof:    run `total_with_shipping` and `reprice_open_orders` on the same
          order before and after; same quote both times
effort:   S
after:    nothing
