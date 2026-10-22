Not strong enough. Line coverage is 100% but two boundaries are untested, and a bug at either one
gets through:

- A subtotal of exactly $50.00. If `>=` became `>`, a $50.00 order would pay shipping. Tests cover
  49.99 and 50.01 only; I ran that mutant and the suite stays green.
- A parcel of exactly 20 kg. If `>` became `>=`, a 20 kg parcel would be charged the $15 fee. Tests
  cover 19.5 and 25 only; that mutant survives too.


Add a test at exactly 50.00 and one at exactly 20 kg.
