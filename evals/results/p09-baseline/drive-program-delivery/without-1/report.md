**Highest verified PR from the bottom: #201.** #202 is the first break, so nothing above it counts as verified.

## Stack verdict check

| PR | Base matches the PR below? | Verdict matches current head? | Status |
|---|---|---|---|
| 201 | Yes, `main` at `trunk-900` | Yes, `a201` and `p201` | **Verified**: PASS by reviewer-1, checks green |
| 202 | Yes, `a201` | **No.** The PASS was for head `b202-old`, but the head is now `b202-rebased` | **Stale.** Checks are green, but the review predates the rebase. The patch id is the same (`p202-current`), so the content is probably unchanged, but nobody has re-reviewed it. |
| 203 | Yes, `b202-rebased` | No verdict at all (`null`) | **Unreviewed** |
| 204 | Base is `c203`, which matches | PASS matches `d204` and `p204` | **Not verified from the bottom.** Its PASS is valid in isolation, but it sits on 202 (stale) and 203 (unreviewed). |

- **#205** is independent, based on `main`, and has a PASS at `e205`. It has no stack dependency, but I can't confirm its base: its record carries no top-level `base_sha`, only the one inside the verdict (`trunk-900`). It can be judged separately from the stack.
- Treat 202's verdict as stale, not as failed. A fresh review or an explicit re-attestation on `b202-rebased` would restore it. I can't tell from this data whether the rebase changed any behavior.
- #204's PASS gives no assurance for the stack, because it was reviewed against a base that has since changed underneath it.

## Practical sequence for the program

The plan's PR numbers (201–204) aren't mapped to work items A–F anywhere in the fixture. I'm assuming the stack follows A→B→C→D, but that mapping needs confirming.

1. **A, the canonical record, first.** Everything depends on it. The plan says the record is "not finalized", so settle the schema before building on it. If #201 is A, it's the verified part.
2. **B, the JSON parser, next.** It needs A. This is the point where the stale #202 matters if #202 is B.
3. **C (CLI) and D (API) in parallel** after A and B land. They own disjoint paths, so there's no file conflict. In the stack as built, they appear to be chained (203→204) when they could be siblings on B. Consider re-basing one of them if the chain is only for convenience.
4. **E, docs, any time.** It has no code dependency. Its examples should be checked against the final schema, so it's best to land it after A is frozen.
5. **F, the integration journey, last.** It needs B, C and D. It has to exercise both entry points against the integrated result, so it can't be verified before 203 and 204 are.

## What to do next

- Get a fresh verdict on #202 at `b202-rebased`.
- Review #203, which has no verdict.
- Then re-confirm #204 on top of the updated base.
- Keep #205 out of the stack gating.

I changed nothing and contacted no forge.