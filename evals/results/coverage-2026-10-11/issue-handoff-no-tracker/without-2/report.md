I couldn't file the issues. `gh` isn't logged in to GitHub here, and I can't complete a login in this session. `git remote -v` in `fixture/` also printed no remote, so there's no target repo either. I didn't try other routes, and nothing was created.

Once you've run `gh auth login` and confirmed or added the remote, I can file all four. Here's what I'd file, based on `AUDIT.md`:

- **M1: one rounding rule.** It's the first in order. It replaces the two local helpers in `cart.py:41` and `invoice.py:88` with `round_half_up` in a new `money.py`. The proof is the `-k rounding` tests passing, including 10.125 → 10.13.
- **M2: tax per line, not per order.** It comes after M1 and changes `cart.py:52-70`. The proof is the `-k mixed_rates` tests passing, with cart [food 10.00, book 20.00] → tax 2.70.
- **M3: clean up the rounding helpers.** It comes after M1 and touches `utils/num.py`. It has no proof step and the "what" is vague ("tidy up"), so the team may want that tightened before picking it up.
- **M4: tax breakdown on the invoice PDF.** It comes after M2 and changes `invoice_pdf.py:120`. The proof is that `scripts/render_invoice.py --order 1001` shows "VAT 7%" and "VAT 19%" rows.

I'd put the file-wide constraints in every issue body: changes ship behind the `TAX_V2` flag (off by default), and the auth model stays as it is. I'd also link the "after Mx" dependencies between issues.

If you'd rather not wait on the login, I can write the four issue bodies to a markdown file in `fixture/` so someone can paste them in tomorrow.