## Findings, worst first

1. **Free store credit.** `place_order` never checks that `qty` is positive. A negative quantity
   makes the total negative, it passes `total > user.credit`, and the credit goes up. Ran it: bob
   ended with 1004.50.
2. **Anyone's invoices.** The export route reads `customer_id` from the body and `export_csv`
   never compares it to the caller. Bob exported alice's invoice 100. IDOR.
3. **Signup overwrites accounts.** In `auth.py`, the taken-check uses the name as typed and the store key is
   lowercased, so signing up as `ALICE` replaces alice. She can no longer log in.
4. **Token key in source.** `SECRET_KEY` is hard-coded in `settings.py`, so anyone who sees the
   code can forge a token for staff. Move it out and rotate it, since history keeps it.

Not findings: the public catalog (intentional per README); `get_invoice`, which checks the owner.
