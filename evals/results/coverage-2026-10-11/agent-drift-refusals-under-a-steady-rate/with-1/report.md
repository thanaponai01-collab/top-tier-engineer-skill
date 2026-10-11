**Recommendation: don't roll back the prompt or the release. The drop isn't the real problem. A refusal regression is, and it started when the model pin was removed.**

**Pass rate is inside the noise band**

| | Pass rate |
|---|---|
| Baseline (5 runs, 2026-08-15) | 0.84–0.90, mean 0.874 |
| 09-07 / 09-14 | 0.88 / 0.87 |
| 09-21 / 09-28 | 0.85 / 0.86 |

The last two weeks sit inside the baseline's own run-to-run spread. They are a slight downward trend, not a breach. The "90% at launch" figure is the top of that band (run 2), not the typical result. The mean was about 87%, so 85–86% is a 1–2 point gap.

**Refusals are the live problem**

| | Refusal rate | Retry rate |
|---|---|---|
| Baseline | 0.01–0.03 | 0.03–0.05 |
| 09-07 / 09-14 | 0.02 / 0.03 | 0.04 / 0.04 |
| 09-21 | **0.06** | 0.05 |
| 09-28 | **0.09** | 0.06 |

- Both weeks are above the 5% paging threshold in `RELEASE.md`, and the rate is climbing.
- The refusal rate moved before the pass rate did, which is the early-warning pattern.
- The three samples in `refused-2026-09-28.jsonl` are all ordinary requests: a return, a double-charge question and an exchange. The agent turned them away with "can't help with financial transactions" or "payment-related questions".
- That fits a model that became over-cautious about money topics. The billing and returns routes would be hit hardest. This is my reading of three examples, so it is suspected, not proven.
- The agent is turning away exactly the tickets it exists to handle, which could be what the lead is noticing. Some of those refusals may be getting graded as passes, which would hide the damage in the pass rate.

**Root cause: the model pin was dropped**
- `RELEASE.md` pins `claude-sonnet-5-5-20260801`.
- `config/agent.yaml` was "simplified" on 2026-09-16 to the unpinned `claude-sonnet-5-5`.
- The logs show the model changed to `claude-sonnet-5-5-20260915` from the 09-21 sample on. The 09-07 and 09-14 samples still show the pinned one.
- Prompt `support-v7` never changed. So a model update arrived through the unpinned alias without the proving round that `RELEASE.md` requires.

**What I'd do**
1. **Restore the pin** to `claude-sonnet-5-5-20260801` in `config/agent.yaml`. I haven't edited it. Say so if you want me to.
2. **Page Dana now.** The refusal rate has been over 5% for two checks in a row.
3. **Run `agent-prove` on the 09-15 model** (or on the pinned model) before any traffic returns to it.
4. **File refusal tasks.** Add the three refused tickets to the eval set as tasks that must not refuse. I haven't done this because `graders.py` is only a docstring in this fixture, so there's no task format to match.
5. **Rolling back the prompt wouldn't help.** The prompt is unchanged.

**Caveats**
- `refused-2026-09-28.jsonl` has only 3 lines, while 9% of 120 runs is about 11 refusals. I only saw part of the evidence.
- `graders.py` contains no grading code in this fixture. I'm taking the logged pass rates as graded with it, as `RELEASE.md` claims.
- I haven't compared refusals by route.