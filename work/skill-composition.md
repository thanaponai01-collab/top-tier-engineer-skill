# Skill composition - 2026-10-13

Owner requirement: useful skill reuse without large context, automatic chains or unnecessary cost.

Implemented locally: conditional routing in pick-skill/Drive; scoped handoff inputs and verdict
ownership; partial foundation feature batches versus strict complete-map validation; optional
setup and narrower onboarding description; Drive agent contract/abuse-case preparation;
assessment versus authorized repair in verification and correctness handoffs.
No skill names or public commands changed. No edits were made to run records or unrelated implementation.

Evidence: 485 repository tests passed (98.239s); final standalone checks 8/8;
catalog check passes, listing 4993/5000 chars; diff whitespace check passed.
Context budget: no overruns. Handoff checker reports an unrelated sample include in
verify-loop/VERIFY_FORMAT.md pointing to absent packages/auth/VERIFY.md; left as a reported gap.
Changed context index/check passes (structural only).

Live evidence: evals/RESULTS.md and evals/results/2026-10-13-1224/.
Five of six single with-plugin regression trials passed; foundation skipped required helpers.
After tightening its reuse wording, replay passed all action checks (helpers and retained state)
but timed out at 90 seconds, so overall completion remains unproven.
Replay: evals/results/skill-composition-foundation-replay/.
First batch reported $1.37; replay cost unavailable. Phrase and action graders were used;
no rubric judge or model override. No context savings or baseline improvement is claimed.

## Next
Before release, complete the foundation live trial within an appropriate recorded budget;
done when both action evidence and overall run succeed. Local instruction fixes are complete.
User authorized commit and push; release remains pending.
