## Correctness gate: FAIL. Don't ship this afternoon as it stands.

**Why it fails:** an order of exactly 100 is charged 5. SPEC.md criterion 1 says "**100 or more** ships free". The suite is green only because `test_hundred` asserts `fee(100) == 5`, which is the wrong value. *Proven.*

`shipping.py:4` uses `if total > 100:` where the spec needs `>= 100`.

**Real output** (from running the code): `fee(100) → 5` (spec: 0). Nearby values are fine: `fee(99.99) → 5` and `fee(100.01) → 0`.

### Behavior table
| Behavior | Oracle | Result | Label |
|---|---|---|---|
| AC1: total ≥ 100 ships free | Spec | **Fails at exactly 100.** Passes for 100.01, 101, 150, 1e9 | proven |
| AC2: total < 100 pays 5 | Spec | Pass (0, 0.01, 50, 99, 99.99) | proven |
| AC3: negative total raises `ValueError` | Spec | Pass (-0.01, -1, -1e9) | proven |
| Property: fee = 0 if total ≥ 100, else 5, checked every cent from 0 to 300 | Property | **Fails at 100.00** | proven |

### Mutation check (throwaway copy; `fixture/` was not changed)
| Mutation | Existing suite | Spec-based tests |
|---|---|---|
| M1 `> 100` → `>= 100` (this is the spec-correct code) | **fails** | passes |
| M2 `< 0` → `<= 0` (rejects a total of 0) | **misses it** | catches it |
| M3 negative check moved to `< -1` | catches it | catches it |
| M4 free threshold moved to `> 101` | **misses it** | catches it |
| M5 flat fee 5 → 4 | catches it | catches it |

The existing suite misses 2 of the 4 real breaks, and it would fail the correct fix. Nothing tests a total of 0, and nothing tests the free-shipping boundary against the spec.

(My first mutation run gave wrong results because Python reused cached bytecode between mutations. I reran with caching off, and the table above is from that clean rerun.)

### To pass
1. Change `shipping.py:4` to `total >= 100`.
2. Change `test_hundred` to assert `fee(100) == 0`, and add tests for 0 (pays 5) and 99.99 (pays 5).

Before doing that, confirm with whoever owns SPEC.md that "100 or more" is the rule you actually want. If exactly-100 orders are meant to pay 5, then the spec is wrong and needs to change, not the code. Either way, the code and spec disagree today, and the tests hide it.

**What this gate didn't cover:** non-numeric input (`None`, strings), `Decimal`, NaN and infinity. The spec doesn't say what should happen for those, so I can't test them as specified. Callers and integration weren't checked either, because the fixture is just one function.

I haven't changed anything in `fixture/`. My spec-based tests are in `/tmp/tmp.oa4sofhx58/test_oracle.py` if you want to add them to the suite. Should I make the fix?