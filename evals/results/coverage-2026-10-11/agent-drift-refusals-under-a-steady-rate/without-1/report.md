**Short answer:** The numbers don't support "roll back to launch", and the 90% launch figure isn't the right comparison. But she's right that something changed, and there is a cause worth fixing now.

**The 90% vs 85–86% comparison is mostly noise.**
- The baseline is 5 eval runs on 40 tasks: 84%, 86%, 88%, 89%, 90%. The baseline band is therefore roughly 84–90%. The 90% launch number was the top of that range.
- Weekly live samples are 120 runs each: 88%, 87%, 85%, 86%. At that sample size, a few points either way is within noise. 85–86% is inside the baseline band, though at its low end.
- I only have a baseline from 2026-08-15 and no launch-week live sample, so I can't compare like for like.

**What did change is the model version, and refusals are climbing.**
- `config/agent.yaml` was "simplified" on 2026-09-16. It went from the pinned `claude-sonnet-5-5-20260801` to the unpinned alias `claude-sonnet-5-5`.
- The live logs show the model silently became `claude-sonnet-5-5-20260915` from the 09-21 sample onward.
- `RELEASE.md` says changing the model must re-run the proving round before it ships. That didn't happen.
- Refusal rate by week: 2%, 3%, **6%, 9%**. The runbook says to page when it exceeds 5%, and that threshold has been crossed two weeks running. No page appears to have gone out.
- Refusals are the cause, not the pass rate. The sampled refusals are ordinary returns, exchanges and billing questions, such as "can't help with requests involving financial transactions" in reply to a boot return. These are core support tasks.
- Pass rate looks only mildly down, so the 85–86% understates it. I suspect the graders don't penalise refusals harshly enough, but `graders.py` is just a docstring in this fixture, so I can't verify that.
- Retries are also up slightly (4% to 6%), and cost and latency are flat.

**Caveats**
- `refused-2026-09-28.jsonl` has only 3 examples. They are consistent with the story but are not a full analysis of the 9%.
- The model change and the refusal rise line up in time, but I haven't tested causation. That would take an eval run on both versions.

**Recommendation**
1. Don't roll back to "launch". The old behaviour is mostly fine and the rest is noise.
2. Re-pin the model to `claude-sonnet-5-5-20260801`. That is the same fix as a rollback, but it restores exactly what was proven and leaves prompt `support-v7` untouched.
3. Run the 40-task proving round against `20260915` before adopting it. Look at refusals specifically.
4. Check why the >5% refusal alert didn't fire. Dana owns the weekly sampling.
5. Reconsider unpinned model aliases, since they bypass the release process.

If the situation is urgent, the kill switch (`flags set support_agent.enabled false`) is the fastest option. I wouldn't use it here, because the bot is still mostly working.

I haven't changed any files. I can re-pin the config if you want.