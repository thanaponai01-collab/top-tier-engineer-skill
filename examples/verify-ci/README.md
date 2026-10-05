# Small CI example

This example verifies a real function, catches its wrong-answer mutation, and retains fresh
evidence tied to the checked-out commit. It uses only Python's standard library.

Run from a clean committed checkout of the plugin:

```bash
python skills/verify-loop/scripts/verify.py ci examples/verify-ci --plan verification/ci.json --output ../verify-ci-evidence
```

The output path must be outside the whole Git checkout. The hosted workflow additionally pins
the reviewed verifier checkout and uploads the report, state and output even on failure.
The unit tests also commit a weak check and a wrong product and require CI rejection.
