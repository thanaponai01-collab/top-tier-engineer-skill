**Highest verified PR from the bottom of the stack: #201.** #202 has a stale verdict, so nothing above #201 counts as verified yet. This was read-only, and I took no action on any forge.

## Stack evidence (`stack.json`)

| PR | Base chain | Verdict | Status |
|---|---|---|---|
| 201 | `main` at trunk-900 | PASS, covering base trunk-900, head a201 and patch p201, all matching the PR | **Verified** |
| 202 | on 201 (a201) | PASS, but for head `b202-old`; the PR head is now `b202-rebased` | **Stale, not verified** |
| 203 | on 202 (`b202-rebased`) | none | **Unreviewed** |
| 204 | on 203 (c203) | PASS, covering base c203, head d204 and patch p204, all matching | Verdict matches its own record, but it sits on unverified ancestors, so **not verified from the bottom** |
| 205 | independent, on `main` | PASS, covering base trunk-900 and head e205 | Verified on its own, outside the stack |

- **#202:** its checks are green at the rebased head, but green checks are not a review verdict. The verdict names the old head. The patch id is unchanged (`p202-current`), which suggests a clean rebase. That is only a hint, though. Someone has to confirm it, or re-review at `b202-rebased`.
- **#204:** its verdict is internally consistent, but it was given against #203's head. #203 has no verdict, and #203 sits on the stale #202. The result is only trustworthy once #202 and #203 are re-verified.
- **#205:** it can be judged on its own. Its PR record has no `patch_id`, so the patch id can't be cross-checked against the verdict's `p205`. I'd treat it as verified for base and head only.
- **Mapping:** nothing in the data links PRs 201–205 to plan items A–F. I haven't assumed a mapping, and you'll need to confirm which PR is which.

## Practical sequence for the program (`program.md`)

1. **A, the canonical record.** Everything depends on it, and the plan says the record isn't finalized. Settle the schema here first.
2. **B, the JSON parser.** It needs A.
3. **C (CLI) and D (API) in parallel.** Both need A and B, and their owned paths don't overlap. The project has no agent roster or dispatcher, so "parallel" here means two people or sessions, set up by hand.
4. **E, docs.** There is no code dependency, but its examples must match the accepted schema. I'd start it after A merges, not at the very beginning.
5. **F, the integration journey.** It needs B, C and D merged. It must use the integrated result, not mocks. It should submit through both entry points and read back identical fields.

## Next steps (not performed)

- Re-review #202 at `b202-rebased`, or confirm the rebase kept the patch.
- Review #203, then re-check #204's verdict against the new chain.
- Only after that, say the stack is verified above #201.