The project's context files are all in place and checked. The one specified behaviour (the checkout total) passes strict local verification, and the product code (`app.py`, `SPEC.md`, the test) is unchanged. Everything is in `fixture/`, which I treated as the project root because `AGENTS.md` says to run commands from that folder. The folder is not a git repository.

| category | file | state | what I did | evidence |
|---|---|---|---|---|
| startup | AGENTS.md | present | refreshed: added one start-here block below the existing text | Original bytes kept exactly, including the MANUAL line and the agent-routing block; *proven* by byte comparison and the foundation check (no issues) |
| intent | BRIEF.md | present | created | Goal and decisions taken from SPEC.md and AGENTS.md; open questions listed. Still partial: intended behaviour for other inputs is unknown |
| work | BUILD.md | present | created | Current state, blockers and one Next step with a completion check; handoff check found 0 gaps |
| features | FEATURES.md | present | created | *traced*: `app.total` → `app.py:1-2` → `tests/test_total.py`. This is the whole package; there is no CLI, HTTP or job entry point |
| verify | VERIFY.md | present | refreshed | Manual blind spot kept word for word; *proven*: strict run green, mutation caught |
| architecture | docs/architecture.md | present | created | *traced* small diagram with sourced edges and unknowns; written by hand, not with `arch-map` |
| commands | docs/commands.md | present | created | *proven*: the test and verification commands were run; no build, launch or deploy commands exist |
| memory | .project-context/index.sqlite | present | created | Index built, with a structural check and a test search; it does not prove product behaviour |

**Verification**
- **Environment:** Python 3.13.4, standard library only, run from `fixture/`.
- **What is checked:** the Checkout total. `total(100)` returns 110, as SPEC.md requires.
- **Can the check fail:** yes. Changing the fee to 1 cent in a scratch copy made the test fail with `AssertionError: 101 != 110 : expected total 110`, which matches the failure message `VERIFY.md` expects.
- **Commands run:**
  - `python -m unittest discover tests` (OK)
  - `verify.py challenge` with `verification/fee-mutation.json` (caught)
  - `verify.py baseline`
  - `verify.py run --strict`
  - `verify.py status`, which printed `VERIFY-STATE: green`
  - `verify.py tests --strict` (1 test, mapped, can fail)
- **Result:** locally verified for that one behaviour only.

**Other files I added or changed**
- `verification/fee-mutation.json`: the deliberate wrong result used in the challenge.
- `.gitignore` (new; there was no existing ignore setup): ignores `.verify-state.json`, `.verify-evidence/`, `.project-context/` and `__pycache__/`.
- `VERIFY.md` was rewritten with the same CRLF line endings the file had before.
- I did not change any test.

**Not yet covered**
- **Inputs with no requirement:** nothing says what `total` should do with zero, negative or non-integer prices, so those cases are listed as gaps rather than guessed.
- **Payment gateway:** the live gateway is out of scope, per the manual note.
- **Fee value:** only a 100-cent price is checked.
- **Rationale:** there is no packaging manifest, and the reason for using integer cents is not recorded.

**Keep in mind:** the verifier hashes every file in the folder. Editing any file, including the context docs, turns its status to `stale` until `verify.py run --strict` is run again.

**Next step:** ask the owner how `total` should handle zero, negative and non-integer prices. Then write the answer into `SPEC.md`, add a test for it, give that test its own failing proof, and re-run the strict verification.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

Goal: a small Python checkout library that returns the price plus a fixed fee (source: SPEC.md).

## Constraints and decisions in force
- Amounts are integer cents (source: AGENTS.md, marked MANUAL). The reason is not recorded.
- Checkout adds a fixed fee of 10 cents to the supplied price (source: SPEC.md).
- Preserve product behavior and the live gateway note (source: AGENTS.md).
- No CI or deployment setup requested (source: AGENTS.md).

## Acceptance
- `total(100)` returns `110` (SPEC.md, checked by tests/test_total.py; recipe in VERIFY.md).

## Out of scope
- The live payment gateway is outside this local project (VERIFY.md blind spot, MANUAL).

## Open questions
- Expected behavior for zero, negative or non-integer prices is not specified; there is no check for them.
- Whether the 10-cent fee ever varies (currency, region, promotion) is not stated; the spec says "fixed".
- Who uses this library, and how it is packaged or imported, is not documented.

Changing a decision: replace its line here, keeping the source.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

## Current
- Context foundation prepared on 2026-10-11; product code unchanged.
- Checkout total: strict verification green (see VERIFY.md). Rejection proof: fee changed to 1 cent in a scratch copy, test failed with "expected total 110".

## Blockers
- None for current scope. Unspecified inputs (zero, negative, non-integer) stay unverified until the owner states the requirement (BRIEF.md, Open questions).

## Next
- Ask the owner what `total` should do with zero, negative and non-integer prices; record the answer in SPEC.md/BRIEF.md, then add a spec-backed test to tests/test_total.py.
- Done when: the new requirement is in SPEC.md, the test is mapped in VERIFY.md with its own rejection proof, and `verify.py run --strict` then `status` print `VERIFY-STATE: green`.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features

Map status: partial in principle, but this is the whole observed package (one module, one public function).

| Feature | Requirement | Entry point | Implementation | Check | Evidence |
|---|---|---|---|---|---|
| Checkout total (price + 10-cent fee) | SPEC.md | `from app import total`; `total(cents)` | app.py:1-2 | tests/test_total.py (`python -m unittest discover tests`) | proven: strict green, rejection receipt (VERIFY.md) |

## Entry-point families
- Library API: `app.total` is the only public function (app.py). Traced.
- CLI, HTTP routes, UI, jobs: none found.
- Integrations: live payment gateway is mentioned but not in this project (MANUAL note in VERIFY.md).

## Unmapped
- Behavior for zero, negative and non-integer prices: no requirement, no check.


<!-- file written by the agent: fixture/docs/architecture.md -->
<!-- context-paths: app.py, tests/test_total.py, SPEC.md -->
# Architecture (as-is)

Traced 2026-10-11 from the source. The whole package is one module.

```
caller (library user)          tests/test_total.py
        |                              |
        |  total(cents)                |  from app import total   (tests/test_total.py:2)
        v                              v
   app.py: total(cents) -> cents + 10       (app.py:1-2)
```

## Boundaries
- `app.py`: owns the checkout total. Pure function; no state, storage, I/O or dependencies.
- `tests/`: unittest suite; imports `app` from the project folder, so commands run from this folder.

## External
- Live payment gateway: referenced in a MANUAL note (VERIFY.md) as outside this project. No code edge exists here.

## Placement
- Source at the project root (`app.py`), tests in `tests/`, verification mutations in `verification/`.
- Local caches (`.verify-state.json`, `.project-context/`) are ignored in `.gitignore`.

## Unknowns
- No packaging manifest (pyproject.toml, setup.py) and no lockfile; how callers install or import the library is unknown.
- Design reasons (for example, why integer cents) are not recorded.


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

Run from the project folder (the one containing `app.py`). Prerequisite: Python 3 (observed 3.13.4); no third-party packages.
No manifest or lockfile exists; the test command comes from AGENTS.md.

| Purpose | Command | Source | Status |
|---|---|---|---|
| Run tests | `python -m unittest discover tests` | AGENTS.md | ran 2026-10-11: 1 test, OK |
| Strict verification | `python <verify-loop>/scripts/verify.py run --strict` then `status` | VERIFY.md | ran 2026-10-11: VERIFY-STATE green |
| Mutation challenge | `python <verify-loop>/scripts/verify.py challenge . --feature "Checkout total" --mutation verification/fee-mutation.json` | verification/ | ran 2026-10-11: caught |
| Search project memory | `python <project-context>/scripts/context.py --repo . search "<terms>"` | top-tier-engineer plugin | ran 2026-10-11 (index built) |

`<verify-loop>` and `<project-context>` are the installed top-tier-engineer skill folders, not files in this project.
No build, launch, CI or deployment commands exist.
