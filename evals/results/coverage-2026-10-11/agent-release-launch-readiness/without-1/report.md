Yes, I'd call two things blockers and a few more should be fixed or accepted knowingly. I only read `fixture/`. The `shop` package (`payments`, `orders`, `mail`) isn't in it, so I couldn't check anything that depends on it.

**Blockers**

1. **The kill switch is too slow for what the assistant can do.** `LAUNCH.md` says rollback is `enabled: false` plus a redeploy of about 25 minutes. `settings.py` reads the config once at process start, so nothing takes effect sooner. For those 25 minutes the assistant can send refunds of up to $200 each with no human (`refund_limit_usd: 200`) across web chat and email. At ~3,000 conversations a day that's roughly 2 per minute, or about 100 conversations in the window. Before Monday, either make the flag re-read on each request (an env var or a file check) or launch with a much lower refund limit.
2. **The tools don't check who is asking.** `lookup_order(order_id)` and `email_customer(to, body)` take whatever the model passes them. `customer` is never given to the tools, so nothing ties an order or an email address to the person in the conversation. A customer, or text inside an inbound email, could get the model to look up someone else's order or send order details to another address. The comment on `issue_refund` says the limit is enforced in `payments`, but I couldn't see that file. Please confirm it, and add an ownership check to the tools.

**Should fix, or accept knowingly**

- **The tested prompt may not be the live one.** `prompt: latest` takes the newest file in `prompts/`. `order-assistant-2026-10-09.md` is the newest and is the one that differs from the 10-02 file (it adds "Be concise"). I can't tell whether it's the version the proving round ran. Any file added to `prompts/` also goes live on the next restart without being tested. I'd pin it to `order-assistant-2026-10-09` and confirm that's what was tested.
- **A conversation that hits the step cap fails with no reply.** `loop.py` raises `StepCapHit` after logging, and nothing catches it. A tool error or an unknown tool name (`TOOLS[reply.tool]`) fails the same way. Return a hand-off message, as the cost-cap path does.
- **The 94% pass rate is thin evidence.** It comes from 5 runs. Across ~3,000 conversations a day, 6% failing would mean about 180 a day. I don't know what failed in that 6%, so check that none of it involves refunds.
- **Customer data is logged indefinitely.** `runlog.py` writes email, address and full history to `logs/runs.jsonl` in plaintext, with no rotation or retention policy.
- **The cost cap only limits a single run.**
  - It's checked after the model call, so one call can overshoot it.
  - There's no daily cap. The $0.40 cap equals your expected average, so there's no headroom.
- **"We'll keep an eye on it" isn't a plan.** Decide what you'll watch (refund count and total, hand-offs, step-cap hits, spend), who is watching, and what triggers a rollback.

If you fix the kill switch and the tool authorization, pin the prompt, and handle the step-cap error, I think Monday is reasonable. I can make those changes if you'd like.