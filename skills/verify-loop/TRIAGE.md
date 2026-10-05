# Failure Triage Guide (pstack Taxonomy)

When `verify.py run` fails, never blindly modify product code. Triage the failure into one of three buckets:

```
                  ┌──────────────────────┐
                  │ Check goes RED (FAIL)│
                  └──────────┬───────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     [Harness Gap]     [Doc Drift]      [Product Gap]
    Port collision,   Spec changed,      Real code bug.
    timeout, seed.    outdated check.    Pin scope and
    Fix ## Run only.  Human approval     fix product.
                      & re-baseline.
```

---

## 1. Harness / Env Gap
- **Symptoms**: Port already in use, process failed to start, database connection refused, command timed out, missing local directory.
- **Action**: Fix `## Run` in `VERIFY.md`, start scripts, or seed data.
- **Rule**: Do NOT edit product logic.

## 2. Doc / Spec Drift
- **Symptoms**: Application behavior was intentionally updated or redesigned, but an existing test check still expects the obsolete behavior.
- **Action**: 
  1. Do not silently change the check!
  2. Report the drift to the user.
  3. With user confirmation, update the check and run `verify.py baseline` to register the new expectation.
- **Rule**: Changing test expectations without baselining triggers `CHECK CHANGED` failure.

## 3. Product Gap
- **Symptoms**: Test assertion failed, runtime output deviated from expected contract, regression occurred (`NEWLY RED`).
- **Action**:
  1. Lock touched files with `verify.py scope <files>`.
  2. Implement fix in minimal surgical slices.
  3. Run `verify.py run` until green.
  4. Ensure all passing tests remain green (`KEEP-GREEN`).
