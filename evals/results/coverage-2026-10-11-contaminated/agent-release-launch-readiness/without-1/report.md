**Yes, I'd hold the Monday all-customers launch until two things are fixed.** The first is the kill switch and the second is the cost and refund exposure. I read all the code in `fixture/` and diffed the two prompts. I did not run anything. The `shop` package (payments, mail, orders) and the proving-round results aren't in the fixture.

**Blockers**

1. **The kill switch takes about 25 minutes, not seconds.** `settings.py:9` reads `enabled` once at process start. Turning it off means editing the config and redeploying, as `LAUNCH.md` says. At 3,000 conversations a day that's about 2 per minute, so roughly 50 conversations run with refunds and customer emails still live. This is proven by reading the code. Fix: re-read the flag on each request, or use an env or feature flag, so a flip takes effect immediately.
2. **There's no total spend cap, and refunds have no aggregate limit.**
   - The $0.40 cap applies per run. It is also checked only after the model call (`loop.py:20`), so a run can overshoot it.
   - The $0.40 figure in `LAUNCH.md` is the expected cost and also the cap. Worst case is 3,000 × $0.40 = $1,200 a day, with no daily ceiling.
   - `refund_limit_usd: 200` lets refunds up to $200 go out without a human, per refund and with no daily total. `tools.py:10` says the limit is "enforced in payments", but nothing in this fixture reads that config key. I can't confirm it's enforced.
   - Fix: add a daily spend cap and a daily refund total cap, and confirm in `shop/payments` that the limit is enforced there.
3. **The prompt may not be the one you tested.**
   - `prompt: latest` (`settings.py:14`) uses the newest file in `prompts/`. `order-assistant-2026-10-09.md` adds "Be concise." to the earlier prompt. That is the same day as the proving round, so I can't tell which version scored 94%.
   - The model is the unpinned alias `sonnet`.
   - Any new file dropped into `prompts/` goes live untested. Fix: pin the prompt file and a dated model ID, and record which pair passed.
4. **There's no staged rollout and no monitoring.** The plan is everyone at once, then "keep an eye on it". Nothing alerts on refund volume, cost, handoff rate or step-cap errors.

**Should fix before launch**

- **Step-cap crash.** `handle` raises `StepCapHit` (`loop.py:29`) instead of replying, so the customer sees an error. An unknown tool name also raises a `KeyError` (`loop.py:26`), and tool exceptions aren't caught.
- **Email recipient.** `email_customer(to, body)` accepts any recipient. Order data and inbound emails are untrusted text that can steer the model. Restrict `to` to the authenticated customer's address.
- **Customer data in logs.** `runlog.py` writes the customer's email, address and full history to `logs/runs.jsonl` in plaintext, with no retention rule or access control.

**Suggested path:** fix 1 and 2, pin 3, then launch to about 5% of traffic with alerts on cost and refunds. Raise the share if it holds.

Tell me if you want me to make these changes. I can also read `shop/payments` once you point me to it.