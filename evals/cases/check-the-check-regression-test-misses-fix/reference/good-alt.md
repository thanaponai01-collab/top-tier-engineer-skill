Short answer: the fix looks correct, the test does not show it.

I reverted only billing.py to the main version (scratch dir, nothing touched here) and ran
test_billing.py: all six tests passed, including test_due_date_is_not_late. So the test did not
fail on the buggy code; it wouldn't have caught #12.

The reason: late_fee was never broken, it already used `paid > due`. The overcharge came from
invoice_total, which had its own `paid >= due` fee calculation and never called late_fee. The PR
makes invoice_total call late_fee (good), but the regression test still only exercises late_fee.

Ask for a test on invoice_total with a payment on the due date expecting 200.0. I checked that it
fails on main (210.0) and passes on the branch.
