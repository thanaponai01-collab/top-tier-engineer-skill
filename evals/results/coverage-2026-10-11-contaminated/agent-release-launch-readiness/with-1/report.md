**Yes, four things block Monday, and the plan is also missing staged rollout and monitoring.** I read the config, loop, settings, tools, runlog and prompts. I ran nothing, so everything below is *traced*, not *proven*.

## Blockers

1. **The kill switch takes about 25 minutes, not seconds.**
   - `settings.py` reads `config.yaml` once at process start, and `LAUNCH.md` says to flip `enabled` and redeploy.
   - The release bar is a stop with no deploy.
   - Fix: re-read a flag file or env var on every `handle()` call.
   - Today, a bad refund loop would run for 25 minutes across ~3,000 conversations a day.

2. **The refund tool can send money with no human check, and the limit is unverified.**
   - `refund_limit_usd: 200` means refunds up to $200 go out without a person.
   - `tools.py` only says "limit enforced in payments". Nothing in `fixture/` shows that, and `config.yaml`'s value isn't visibly wired to it.
   - `LAUNCH.md` has no scoped grant for this one-way action.
   - Fix: confirm the limit is enforced in `shop.payments`. Start with refunds routed to a human or a lower limit until a slice is clean. Also cap refunds per day.

3. **The model and prompt are not pinned.**
   - `model: sonnet` is an alias, so a provider update changes behaviour silently.
   - `prompt: latest` takes the newest file in `prompts/`. Dropping in a new prompt file ships it untested.
   - The 10-09 prompt differs from 10-02 only by "Be concise.", but it's the one the proving round should cover. Confirm that.
   - Fix: pin the exact model ID and `order-assistant-2026-10-09`. A change to either means re-running `agent-prove`.

4. **There is no daily spend cap, and the per-run cap is checked too late.**
   - `max_cost_per_run_usd` is checked after each call returns. The one that crosses it has already been paid for, and the cap is never checked before a call.
   - At ~3,000 conversations a day and up to $0.40 each, the worst case is about $1,200 a day.
   - That worst case is the cap itself. The plan's "about $0.40" is an expected figure, not a bound.
   - Nothing limits total spend per day.
   - Fix: add a daily cap that trips the kill switch.

## Also fix

- **Logs store personal data in plaintext.**
  - `runlog.py` writes customer email and address to `logs/runs.jsonl`. Message and tool history are also unredacted.
  - Fix: redact before storing. Log the model and prompt version too, so a run can be replayed. It doesn't log them now.
- **The step cap raises an exception to the customer.**
  - `StepCapHit` is raised out of `handle()`. The cost cap returns a handoff message, so the step cap should too.
- **Rollout is 100% of customers on web and email at once.** The plan has no shadow or read-only stage and no slice. `email_customer` is another one-way action.
- **"We'll keep an eye on it" has no owner, schedule, or alert threshold.** The release note needs a named owner and sampling schedule, plus the thresholds that page someone for failure rate, cost, and cap hits. `agent-drift` covers the mechanics.
- **The 94% over 5 runs needs the bar named.** I couldn't find the grader or the bar in `fixture/`, so I can't say whether 94% clears it. Check that it was run against the 10-09 prompt and the real model ID.

## Suggested path for Monday

Launch to a small slice, say 5–10% of traffic, with refunds routed to a human and the new kill switch and daily cap in place. Widen once a named failure rate holds. The in-process kill switch and the pins are small edits. I can make them if you want. The refund-limit check needs someone who owns `shop.payments`.