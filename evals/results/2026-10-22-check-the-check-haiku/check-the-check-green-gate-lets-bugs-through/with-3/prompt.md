Use `check-the-check` on `fixture/`.

test_shipping.py is the merge gate for shipping.py. It's green, every line of shipping.py runs under it, and each test pins an exact amount. Is it strong enough that a bug in shipping.py can't get past it? If not, tell me exactly what would get through.
