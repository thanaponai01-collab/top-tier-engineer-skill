Strict green. Now the start-here block, ignores, memory index, and checks.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

Goal: a Python checkout library whose `total(cents)` adds a fixed 10-cent fee (SPEC.md).

## Decisions in force
- Amounts are integer cents (AGENTS.md, MANUAL).
- No CI or deployment setup (AGENTS.md).
- The live payment gateway is outside this project (VERIFY.md, MANUAL).

## Unknowns
- Behavior for zero, negative or non-integer amounts is not specified.
- Who consumes the library and how it is packaged is not documented.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

State: checkout fee implemented in `app.py` and covered by `tests/test_total.py`.

## Next
- Ask the owner to specify behavior for zero, negative and non-integer amounts, then add checks.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features

## Checkout fee
- what: `app.total(cents)` returns the price plus a fixed 10-cent fee (SPEC.md); entry point app.py:1
- verify: VERIFY.md › Checkout fee
- status: proven
- trace: app.total → `cents + 10`; checked by tests/test_total.py


<!-- file written by the agent: fixture/docs/architecture.md -->
# Architecture

Single-module Python library, no dependencies, no runtime services.

- `app.py` — `total(cents) -> cents + 10`; the only public entry point.
- `tests/test_total.py` — unittest importing `app` from the package root.

Edges: tests → app. No I/O, storage or network. The live payment gateway is external and not in this repo.
Unknown: packaging and consumers (no manifest present).


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

Working directory: `fixture/`. Prerequisite: Python 3 (no third-party packages, no manifest).

| Purpose | Command | Status |
|---|---|---|
| Unit tests | `python -m unittest discover tests` | observed: 1 test OK |
| Verify recipe | `python <verify-loop>/scripts/verify.py run --strict .` | observed (see VERIFY.md) |

No build, lint, CI or deploy commands exist.
