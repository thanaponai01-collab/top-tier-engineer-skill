**Don't roll back the prompt or the release. The model changed underneath you, so pin it again.** A pass rate of 85–86% sits at the bottom of the noise band, but refusals are the real problem, and a model swap explains them.

**What I found** (proven, from the files):
- **Baseline:** the 5 runs from 2026-08-15 range from 84% to 90% pass, average about 87.4%. The "90% at launch" figure is the best single run. Refusal rate was 1–3%.
- **Pass rate:** 88%, 87%, 85%, 86% over the four live weeks. That is inside the baseline's range. It only looks like a drop next to the 90% run.
- **Refusals:** 2%, 3%, 6%, 9%. The 6% and 9% weeks are over the 5% page threshold in `RELEASE.md`, and nobody was paged.
- **Cause:** logs for the weeks of 09-07 and 09-14 show `claude-sonnet-5-5-20260801`. Logs for 09-21 and 09-28 show `claude-sonnet-5-5-20260915`. On 2026-09-16, `config/agent.yaml` was "simplified" from the pinned model ID to the floating `claude-sonnet-5-5`. The prompt stayed `support-v7`. This breaks the release rule that changing the model re-runs the proving round.
- **Symptom:** `live/refused-2026-09-28.jsonl` has three refusals. Ordinary return, exchange and double-charge questions get "I can't help with financial transactions" or "I can't help with that request."

**Why the pass rate hasn't fallen further** (suspected): the refusal-rate drift is much bigger than the pass-rate drift. I can't tell why from these files, since each live file has only aggregates and I can't see per-task grading. `graders.py` is a one-line docstring with no grading code. The "frozen" graders can't be audited from this fixture, so the pass-rate numbers rest on trust.

**Recommendation:**
1. Restore the pinned ID `claude-sonnet-5-5-20260801` in `agent.yaml`. This is a config change, and putting it back is the rollback. I haven't made the edit. Say so if you want it done.
2. Run the 5-run proving round on the new model, `claude-sonnet-5-5-20260915`, before it ships again. Check whether refusals reproduce on billing and returns prompts.
3. Tell Dana the 5% refusal alert didn't fire for two weeks. Find out why, or whether anyone checked.
4. Re-read the 09-28 refusals on the full 120-run sample. I only saw 3 examples, and their billing/returns routes look consistent with the cause but don't prove it.

Caveats: weekly samples of 120 runs carry about ±3 points of sampling noise on their own. That's another reason not to read 90→85 as a trend.