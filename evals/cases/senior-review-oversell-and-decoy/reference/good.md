# Senior Review — fixture/

**Can't ship as-is. Biggest issue: `reserve_stock` will oversell — it never checks qty against
available stock.** Read: `inventory.py`, `cli.py`, `test_inventory.py`, `README.md` (all four files
in the fixture). Skipped: nothing, the fixture is small.

## 1. What is it for?

A CLI that reserves warehouse stock, one order at a time (README.md). It must never let a
reservation go through for more than is actually on the shelf.

## 2. What breaks it?

Ran, didn't just imagine:

- Empty input: `python cli.py widget` — crashes with an `IndexError` (expected: it's a CLI, a
  missing arg is a usage error, not a data-safety bug).
- Malformed/oversized qty, the one that matters: `python cli.py widget 999` prints `-989`. No
  exception, no rejection — `reserve_stock` does not validate qty against available stock (or that
  qty is positive) before mutating `_STOCK`, so it sells stock it doesn't have and stock goes
  negative with no signal to the caller.
- Two callers at once: not attempted. README.md states this is a single-process CLI with no
  concurrent access — each invocation is a fresh process reserving one order and exiting, so there
  is nothing here to run two callers against. Not exercised here, and I'm not claiming a finding I
  didn't run.

## 3. What happens when it fails?

Nothing visible happens — that's the problem. `reserve_stock("widget", 999)` returns `-989` and the
CLI just prints it. No error, no log line, nothing to undo; the bad state (negative stock) is
already committed to `_STOCK` by the time anyone notices.

## 4. Where would the next change land?

`inventory.py` is one file, `reserve_stock` is the one function anything would call — not a spread
problem yet, but the missing validation belongs right there.

## 5. What's the biggest gap?

The qty validation. `git log -S reserve_stock` shows one commit, the initial add — no attempt at
validation was ever made or dropped.

## Findings

| severity | finding | why it matters | evidence | fix |
|---|---|---|---|---|
| high | `reserve_stock` oversells (inventory.py:5) | stock can go negative with no rejection, no error | proven: `python cli.py widget 999` -> `-989` | validate `0 < qty <= get_stock(item)` before subtracting, raise otherwise |

Not a finding: the module-level `_STOCK` global has no lock, which looks unsafe, but this is a
single-process CLI per README.md with no concurrent access — nothing here lets me actually run two
callers at once and observe corruption, so I'm not calling it broken, just noting it as something to
revisit if this tool ever grows a server around it.

Next skill: `correctness-gate`, once qty validation exists, to pin the boundary (qty == stock is
fine, qty == stock + 1 is not).
