# Agent drift check: support-agent, week of 2026-09-28

**Verdict: drifted, but not in the pass rate.** The pass rate is inside the baseline's noise band.
The refusal rate is not: it went 2% → 6% → 9% after the model changed under the pin, and it crossed
the 5% paging line two weeks ago. Re-pin the model. Rolling back the prompt fixes nothing, because
the prompt didn't change.

| series | baseline (2026-08-15, 5 runs) | 09-07 | 09-14 | 09-21 | 09-28 |
|---|---|---|---|---|---|
| pass rate | 84–90% (band) | 88% | 87% | 85% | 86% |
| refusal rate | 1–3% | 2% | 3% | **6%** | **9%** |
| retry rate | 3–5% | 4% | 4% | 5% | 6% |
| model in logs | -20260801 | -20260801 | -20260801 | **-20260915** | **-20260915** |

- **Pass rate: no drift** [proven: read from the files]. 90% was the best of five baseline runs.
  The baseline band is 84–90%, and 85–86% sits inside it. Comparing against the launch high is
  comparing against a moving point.
- **Refusals: past the threshold.** The sampled refusals (`live/refused-2026-09-28.jsonl`) are
  ordinary return and billing tickets refused as "financial transactions". These are real customers
  turned away while the pass rate holds.
- **Root cause: the pin was lost** [traced]. `config/agent.yaml` was "simplified" on 2026-09-16 from
  `claude-sonnet-5-5-20260801` to the alias `claude-sonnet-5-5`. From 09-21 the logs show
  `claude-sonnet-5-5-20260915`. Same prompt (`support-v7`). That's a model change that never went
  through the proving round the release note requires.

**Do now:** restore the dated pin, then rerun the proving round before calling it fixed. File T-88121,
T-88140 and T-88177 as eval tasks with the existing graders. Whether to throttle while that happens is
the owner's call (Dana). The refusal threshold has been breached for two weeks and nobody was paged.

Not checked: I didn't run the graders myself. The numbers are from the sample files.
