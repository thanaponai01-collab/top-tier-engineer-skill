Mtimes are all identical, so they tell me nothing. This review comes from reading the code only. The provider call and the `shop` package (`payments`, `orders`, `mail`) aren't in this copy.

## Likely blockers

1. **The rollback takes about 25 minutes, and nothing else can stop the assistant.**
   - `config.yaml` is read once at process start, and `ENABLED` is frozen at import.
   - The assistant can issue refunds and send email on its own, to every customer, from 10:00.
   - The plan has no faster way to stop it, such as a flag or env var checked on each request.
   - Fix: re-read `enabled` on every request, or add a kill switch outside the deploy path. Test it before Monday.

2. **"Latest" prompt vs. what the proving round tested.**
   - `prompt: latest` takes the newest file in `prompts/` by filename sort.
   - Any file added to that folder, even a draft, becomes live on the next restart without review.
   - `LAUNCH.md` doesn't say which prompt file the 94% run used. I can't tell from the files whether it was `2026-10-09`.
   - Fix: pin `prompt: order-assistant-2026-10-09`, assuming that's the tested file. Confirm that first.

3. **Refund safety rests on code I can't see.**
   - `tools.py` says the limit is "enforced in payments", but `refund_limit_usd: 200` is in this config and nothing here reads it.
   - If `payments` has its own hardcoded limit, or none, the config value does nothing.
   - Also check that the limit is per refund, and that repeated refunds on one order are capped. Otherwise the assistant could issue five $199 refunds.
   - Fix: check `shop/payments.py` before launch.

## Should fix, but not necessarily blocking

4. **Budget doesn't add up.**
   - 3,000 conversations a day at up to $0.40 each is up to $1,200/day, about $36k/month. That's the ceiling, not the average.
   - The cap is per run (`max_cost_per_run_usd`). There is no daily or total cap.
   - Fix: add a daily spend limit with an alert.

5. **Step cap raises an exception.**
   - After 12 steps, `StepCapHit` is raised instead of returning a handoff message. The cost cap hands off cleanly.
   - Unless the caller catches it, customers could see an error or get no reply.
   - It's also an obvious hole in 5 proving runs. Check whether any hit it.

6. **Logs hold customer PII.**
   - `runlog.py` writes email, address, and full message history in plaintext to `logs/runs.jsonl`, with no rotation or retention.
   - Confirm that's approved and the file is access-controlled.

7. **Tool calls have no error handling.**
   - `TOOLS[reply.tool](**reply.args)` has no try/except and no argument validation.
   - A hallucinated tool name or bad arguments crash the run.
   - `email_customer(to, body)` takes any address. A prompt-injected message could make it email someone other than the customer.
   - Fix: bind `to` to the authenticated customer.

8. **No monitoring plan.**
   - "We'll keep an eye on it" isn't one. Combined with the 25-minute rollback, a bad refund pattern could run for a long time.
   - Fix: name who watches refund volume, handoff rate, and errors during the first day. Set alert thresholds.

## Bottom line

I'd treat items 1 to 3 as blockers. Each is a small fix: a per-request kill switch, a pinned prompt, and a read of `payments.py`. I'd also do 5 and 7 before Monday, and write down who owns monitoring (item 8).

I can make the fixes for 1, 2, 5, and 7 now if you want. For item 3, point me to the `shop` package.