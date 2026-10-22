# PR #13: Don't charge a late fee on the due date (fixes #12)

Issue #12: a customer paid invoice INV-881 on its due date (2026-03-31) and was billed $210.00
instead of $200.00.

This PR fixes the late-fee calculation so paying on the due date is on time, and adds
`test_due_date_is_not_late` as the regression test. All tests pass.
