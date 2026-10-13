**Highest verified PR from the bottom of the stack: #201.** The stack is not verified above that.

## Stack evidence

| PR | Base matches the PR below | Checks | Verdict bound to current base, head and patch? | Status |
|---|---|---|---|---|
| 201 | Yes (`main` at `trunk-900`) | green at `a201` | Yes, all three match | **Verified** |
| 202 | Yes (`a201`) | green at `b202-rebased` | **No.** The verdict is for head `b202-old`, but the current head is `b202-rebased`. | Stale verdict, not verified |
| 203 | Yes (`b202-rebased`) | green at `c203` | **No verdict** | Unverified |
| 204 | Yes (`c203`) | green at `d204` | Yes, its own tuple matches | Verdict is valid on its own, but it sits on an unverified chain |

- **#202:** The `patch_id` is the same on both sides, so the rebase probably didn't change the content. That is an inference, not a receipt. The PASS was issued for a different head SHA, and green checks don't replace a review. #202 needs a fresh verdict, or a recorded attestation that the rebase was content-neutral, at `b202-rebased`.
- **#204:** Its verdict is sound for what it covers, but it can't count while #202 and #203 below it are unverified. Anything above a broken link is unverified regardless of its own receipt.
- **#205:** It is outside the stack and based directly on `main`. Its verdict matches `trunk-900` and `e205`, so it is verified on its own terms. It does not raise the stack's verified height. The PR entry has no `patch_id` field; the patch ID appears only inside the verdict, so I couldn't cross-check it.
- **Plan mapping:** `stack.json` doesn't say which PR is plan item A, B, C and so on, so I can't tie these PRs to plan items. Please confirm the mapping.

## Practical sequence for the program

1. **Finalize A first.** `program.md` says the shared record isn't finalized, and B, C, D and F all depend on it. Treat A as a gate: tests for valid, empty and malformed records, and an agreed shape.
2. **B next**, with the parser tests (malformed input, round-trip fields).
3. **C and D in parallel**, both based on B and neither on the other. The current stack is linear, so if C and D are stacked one above the other, their independence is lost. Re-base one onto B if that's the case.
4. **E (docs) anytime.** It has no code dependency. Its examples should be checked against the final schema from A, so merge it last, or after A is final.
5. **F last**, run against the integrated result. It should submit through both entry points and read back identical fields. Don't write it against mocks.

The project has no agent roster or dispatcher, so "parallel" here means separate people or sessions you assign by hand. Don't assume automation.

## Next steps (all for you to authorize)

- Get a re-review of #202 at `b202-rebased`.
- Get a first review of #203.
- After that, check that the #204 verdict is still bound to the head that sits on the then-current #203.
- Don't arm, retarget, or merge anything above #201 until those are done.

I made no changes and contacted no forge.