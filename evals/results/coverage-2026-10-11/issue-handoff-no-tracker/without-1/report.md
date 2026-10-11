I didn't file any issues. `gh` isn't logged in to GitHub here, `fixture/` has no git remote, and there's no `GH_TOKEN` or `GITHUB_TOKEN` set. I can't sign in for you in a non-interactive session, and I'd be guessing at which repo to file against.

Once you run `gh auth login` and add a remote (or tell me the `owner/repo`), I can file these. The four issues I'd create from `AUDIT.md` are:

- **M1: one rounding rule.** Use `round_half_up` in `cart.py:41` and `invoice.py:88`, and add `money.py`. It's first in order.
- **M2: tax per line, not per order.** Change `cart.py:52-70`. It comes after M1.
- **M3: clean up the rounding helpers.** Tidy `utils/num.py` after M1. It has no proof command, and its "what" ("tidy up") is vague, so I'd flag it as needing a definition before someone picks it up.
- **M4: tax breakdown on the invoice PDF.** Change `invoice_pdf.py:120`. It comes after M2.

Each issue would carry the audit's shared constraints: everything ships behind the `TAX_V2` flag (off by default), and the auth model stays unchanged. I'd also link the "after M1" and "after M2" dependencies between issues.