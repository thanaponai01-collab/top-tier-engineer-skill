I'd call the structure decent at the module level but fragile underneath. The code is small (about 130 lines of Python) and split into sensible modules: `catalog`, `cart`, `receipt`, `checkout`, `payments`, `notify`, plus a `legacy/tax_tables`. The weak points are duplicated logic, almost no tests, and network code with no test coverage. I read every file and the git history and ran the tests (2 pass). I changed nothing.

The history shows where the trouble is. Of the 12 commits after the initial one, 6 are fixes, and they cluster in two places:
- **Pricing (`cart.py` and `receipt.py`):** 6 commits, 3 of them fixes, each for the receipt and cart totals not matching.
- **Network calls (`payments.py` and `notify.py`):** 5 commits, 3 of them fixes, all to retry logic that has no tests.

`legacy/tax_tables.py` is the ugliest file but hasn't changed since the first commit.

## Fix first, in order

**1. Give pricing one source of truth, and put tax on the receipt.**
- `shop/receipt.py:3-24` is a copy of `shop/cart.py:3-15`, constants included. Every discount change so far has had to be made twice, and the history shows it went wrong three times (`716a01b`, `fa4e4f0`, `6c240fd`). The test added in `1a0f135` only catches the mismatch after it happens. The fix is to have `receipt` call `cart_total`, or to move both onto one pricing function.
- **There is also a live bug:** `checkout` charges the card `cart_total + sales_tax` (`shop/checkout.py:9-11`), but `render` prints the total *before* tax (`shop/receipt.py:29`). So in any region with tax, the printed total is less than what the customer was charged. For example, `tee=3 cap=2` in `north` is charged $100.95 while the receipt says $94.35. The fix is to compute the total once in checkout and pass that same number to both `charge` and `render`.

**2. Make payment retries safe, and test the network code.**
- `charge` (`shop/payments.py:10-20`) retries a `POST /charge` on any `OSError`, including a read timeout after the payment provider may already have taken the money. It sends no idempotency key, so a slow response could charge the customer twice. Whether that actually happens depends on how the provider handles repeat requests with the same order ID; I couldn't check that from the code.
- `payments.py` and `notify.py` each have their own retry loop, and between them they've needed three fixes (connection leak, timeouts, no backoff). Neither has a single test.
- Plan: one shared retry helper with backoff, an idempotency key on the charge, and tests that use a fake HTTP server or mocked client.

**3. Fix the tax inputs before touching the tax table.**
- `checkout` always passes the category `"general"` and taxes the whole cart as one amount (`shop/checkout.py:10`). The catalog has no categories, even though a T-shirt is clothing. As a result, the food, clothing and books rules in `tax_tables.py` never run, and clothing is probably taxed at the wrong rate in every region.
- Steps: add a category to each catalog product, compute tax per line, and first write characterization tests that pin down what `sales_tax` does today. The east-region clothing rule, which changes the rate depending on whether the cents amount is even or odd (`legacy/tax_tables.py:40-50`), needs a decision from whoever owns tax, since it may be a bug carried over from the old till software.
- Don't rewrite the nested if-statements in the tax table just to make it cleaner. It's stable, and there are no tests yet to catch a mistake.

## Smaller items, not top three
- `app.py` doesn't validate input: an unknown product code or a malformed `sku=qty` argument crashes with a raw error.
- The return value of `send_order_email` is ignored, so failed emails go unnoticed.
- The webhook and payment hosts are hard-coded, with no configuration.
- Amounts in cents and prices with decimals are both used, which works but is easy to mix up.