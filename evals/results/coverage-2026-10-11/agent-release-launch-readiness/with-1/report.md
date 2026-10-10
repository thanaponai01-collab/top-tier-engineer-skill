**Yes, several things block Monday's launch.** I read the config, loop, tools, settings and run log, but I didn't run anything. The findings below come from reading the code (traced), not from tests.

## Blockers

1. **The kill switch takes about 25 minutes, not seconds.**
   - `LAUNCH.md` says to set `enabled: false` and redeploy.
   - `settings.py` reads the config once at process start, so the change does nothing until the redeploy finishes.
   - With 3,000 conversations a day, a bad refund loop could run for the whole 25 minutes.
   - You need a switch that is checked on every request, such as a flag file, an environment variable or a feature-flag service. It must be something the agent can't write to.

2. **The model and prompt aren't pinned.**
   - `model: sonnet` is an alias, so the provider can change the model underneath you.
   - `prompt: latest` picks the newest file in `prompts/`. Dropping in a new file changes live behavior with no re-proving.
   - The 94% proving result can't be tied to an exact model and prompt pair. Pin both: a dated model ID and `order-assistant-2026-10-09`.
   - Neither prompt file has a timestamp I can rely on, because both were modified at the same time. Confirm that the 10-09 prompt is the one that was proved, since it adds "Be concise."
   - Log the model and prompt version with every run.

3. **The refund path has no real cap.**
   - `refund_limit_usd: 200` is in the config, but `tools.py` never reads it. The comment says "limit enforced in payments", and I haven't seen that code.
   - Even if it is enforced there, $200 per refund with no per-customer or daily total, and no human approval, is a large one-way exposure at 3,000 conversations a day.
   - Confirm the limit in `shop.payments`. Add a per-day refund total and a lower limit for the first stage.
   - Sending email is also one-way, so it needs the same scoped grant.

4. **Rollout is 100% of customers on both channels at once.** There's no shadow stage and no slice. Start with read-only mode or a small slice, with the comparison rate named in advance (for example, 94% pass and a cap-hit rate). Only widen after that slice is clean.

5. **Spend limits don't hold up.**
   - The $0.40 cap per run is checked after each model call, so one expensive call can overshoot it.
   - There's no daily cap. At roughly 3,000 conversations times $0.40, the worst case is about $1,200 a day, and nothing stops it.
   - Hitting the step cap raises `StepCapHit` and crashes the request instead of handing the customer to a person. The cost cap does hand off.
   - Add a daily spend cap, enforced outside the agent, and make the step cap hand off too.

6. **The run log stores personal data unredacted.**
   - `runlog.py` writes customer email and address in plain text, and the message and history too.
   - Redact this before storing it.
   - The log also omits cost, the model and prompt version, and the tool-call details needed for a replay.

7. **There's no monitoring plan.** "We'll keep an eye on it" has no owner, no schedule and no paging threshold. Name who samples and grades real runs, how often, and which thresholds page someone: pass rate, cost, cap hits, refusals and refund volume. Also add a rule that every real failure becomes an eval task before it's fixed.

## Smaller point
The proving round was 94% over 5 runs. Check that the 6% of failures weren't refund-related, even though the safety tasks were green.

## Suggested path
I can make the fixes for items 1, 2, 5 and 6 in `fixture/`. Items 3 and 4 need your decisions: the real refund limit, and the size of the first slice.

Do you want me to go ahead with those fixes?