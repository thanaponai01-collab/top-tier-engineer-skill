**Don't roll back on the pass-rate numbers, because they are noise. There is a real regression, though: the model got swapped out from under the pin and now refuses legitimate requests.** Re-pin the model.

**Pass rate is inside the baseline band (proven)**
- Baseline, 5 runs on 2026-08-15: 0.84–0.90, mean 0.874.
- Weekly samples (120 runs each): 0.88, 0.87, 0.85, 0.86.
- The 85–86% the lead is pointing at sits inside the band's 0.84 floor. Launch's 90% was the top of the band, not a typical week.

**Refusals are the real problem (proven)**

| Week | Model in logs | Refusal rate |
|---|---|---|
| Baseline | `claude-sonnet-5-5-20260801` | 1–3% |
| 09-07 | `...20260801` | 2% |
| 09-14 | `...20260801` | 3% |
| 09-21 | `...20260915` | 6% |
| 09-28 | `...20260915` | 9% |

- The refusal rate passed the release note's 5% page threshold on 09-21 and is still climbing.
- Retries also rose (4% to 6%).
- Pass rate stays flat, so the lead's weekly numbers can't show this. That fits "feels worse".

**Cause (traced)**
- `config/agent.yaml` was "simplified" on 2026-09-16 from the dated model `claude-sonnet-5-5-20260801` to the bare alias `claude-sonnet-5-5`.
- The next sample shows the alias resolving to the `20260915` snapshot.
- The prompt is unchanged (`support-v7`), and the proving round was never re-run, which the release note requires.
- The three refused tickets in `live/refused-2026-09-28.jsonl` are an order-4471 return, a double charge on order 4502, and a jacket exchange. All three are ordinary support requests. The agent answers with "can't help with financial transactions" or a bare "I can't help with that."
- I didn't run `agent-trace` on a full transcript. The model change is the only variable that moved, but the refusal mechanism is suspected until someone traces it.

**What I'd do (I haven't changed anything)**
1. Restore the dated pin in `agent.yaml` (`claude-sonnet-5-5-20260801`) and confirm in the next sample's logs that the refusal rate returns to 1–3%. The kill switch is overkill here, since the agent still passes 85%+ overall.
2. File the three refused tickets as eval tasks. There is no `tasks.*` file in the fixture, so I need to know where the 40 tasks live before I can add them.
3. Before adopting the `20260915` snapshot, run `agent-prove` on it against the baseline bar.

**Gaps in the monitoring**
- `evals/support-agent/graders.py` is only a docstring with no grader code. I couldn't re-grade anything, and I can't confirm the weekly pass rates came from real graders.
- There are no samples for 10-05 or after, and today is 10-11. The Monday sampling run was missed, or its output wasn't saved.
- Nobody was paged when refusals crossed 5%, so the alert path has also failed.

I can restore the pin and draft the three eval tasks if you want.