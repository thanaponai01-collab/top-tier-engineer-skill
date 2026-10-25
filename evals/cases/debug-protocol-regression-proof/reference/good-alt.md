The fee constant in `total()` was 11, not the 10 cents SPEC.md fixes. The regression test was red
before the fix (expected 110, got 111) and is green after it. Not covered: the live payment gateway,
which stays a manual check.
