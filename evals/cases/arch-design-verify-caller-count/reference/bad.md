# Architecture Audit — fixture/

`shipping/base.py` is a classic speculative interface: one implementation
(`FlatRateCalculator`), no second carrier anywhere in the codebase.

Searched the repo for `get_calculator(` — it turns up once, in
`checkout/cart.py`. That is the only caller. Safe to inline directly: drop
`ShippingCalculator` and `FlatRateCalculator`, and have `checkout/cart.py`
compute the flat rate itself.

## Moves

### 1. Inline the shipping abstraction
cost:     unused layer, one implementation
files:    shipping/base.py, shipping/flat_rate.py, shipping/registry.py
owner:    checkout/cart.py
callers:  checkout/cart.py
door:     two-way
proof:    run the checkout flow, same total
effort:   S
after:    nothing
