**Playbook:** large program plus dependent PR stack, read-only. I read it as a review and sequencing task. I did not read it as permission to act on the forge. I read `SKILL.md`, `program-delivery.md`, `README.md`, `program.md` and `stack.json`. I created no RUN.json because nothing is being edited.

## Highest verified PR from the bottom: #201

The stack runs 201 → 202 → 203 → 204.

| PR | Status | Why |
|---|---|---|
| **#201** | **Verified** | `reviewer-1` is not the author. The verdict's base `trunk-900`, head `a201` and patch `p201` all match the PR, and checks are green at `a201`. |
| **#202** | **Blocker** | The PASS verdict was recorded against head `b202-old`, but the PR head is now `b202-rebased`. The patch ID still matches (`p202-current`). That only suggests the rebase didn't change the diff. It doesn't show the new head was reviewed or built. The verdict is stale and needs a fresh independent review at `b202-rebased`. Green CI at the new head doesn't replace that. |
| #203 | Unverified | It has no verdict (`null`). |
| #204 | Unverified | It has a PASS at `c203`→`d204`, but it sits above two gaps. A passing descendant doesn't extend the ceiling. |
| #205 | Independent | It passes on its own against `trunk-900`. It is outside the chain and doesn't repair the gap. |

**Caveats:**
- `stack.json` is a recorded snapshot. I didn't read the live forge, so a live re-check of 201's identities is still owed before anyone relies on it.
- Nothing here says #201 has merged. This is local verification only.

**What would extend the ceiling:**
1. An independent review of #202 at `b202-rebased`, with its base SHA, head SHA and patch ID recorded.
2. A first independent verdict on #203.
3. A re-check of #204 against the live base. Its verdict is only valid if #203's head is still `c203`.

I took no forge actions: nothing was armed, retargeted, pushed or merged. Any landing needs your explicit authority and `safe-release`. That would start with #201 alone, then a re-read of the stack before touching #202.

## Practical sequence for the program

1. **A, the contract.** The record isn't finalized and everything depends on it, so finalize it first. Check it with the valid, empty and malformed unit tests.
2. **B, the parser.** It follows A. The check includes malformed input and round-trip fields.
3. **C and D, which can run in parallel.** Only run them in parallel after confirming they share no files beyond the owned paths. A shared persistence or store layer isn't listed, and I'd check for one. The program allows only one executor at a time, and no dispatcher exists. So plan to run them sequentially unless the host provides workers. Each one needs its own check: invoke the CLI and read the persisted record, and call the endpoint and read the stored record.
4. **E, the docs.** It has no code dependency, so it can be drafted any time. Its "examples match the accepted schema" check can't pass until A and B settle, so validate it last.
5. **F, the integration journey.** It runs only on the integrated result. Submit through both the CLI and the API, then read back identical fields. Rerun it after each slice is integrated.

Treat any change to A as invalidating B through F's proof. Rerun those checks rather than carrying them forward.

If the PR stack is meant to carry this program, I can't tell from these files which PRs correspond to A–F. Tell me the mapping and I'll fold it into the sequence.