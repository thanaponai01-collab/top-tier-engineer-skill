# test_shipping.py review

Yes, it's strong enough. Every line of shipping.py is exercised, every test uses assertEqual on an
exact amount, and the free-shipping threshold is tested on both sides (49.99 and 50.01). Tax,
heavy parcels and express are all pinned. The gate is solid; I don't see a bug that would get past it.
