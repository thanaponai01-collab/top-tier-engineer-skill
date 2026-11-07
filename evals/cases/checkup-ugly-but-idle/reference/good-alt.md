Short version: it's decent, with two real problems and one ugly file that can wait. But fix
two bugs first: the receipt total has no tax in it, so it isn't what checkout charged, and
payments retries the charge with no idempotency key, which can bill an order twice over
(a duplicate charge).

- First: cart and receipt both compute the discount on their own. The history has them
  changing together over and over, and two of those commits are fixes for the receipt drifting
  from the cart. One place for that rule.
- Second: notify and payments each roll their own HTTP retry loop, one on urllib, one on
  http.client, and both have had timeout and retry fixes. Put them behind one client.
- Third, low priority: tax_tables is a nested mess, but it has not changed since the first
  commit, so refactoring it now buys nothing.
