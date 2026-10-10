# support-agent release note (v7, live since 2026-08-18)

- Model: pinned `claude-sonnet-5-5-20260801`. Prompt: `support-v7`. Changing either re-runs the
  proving round before it ships.
- Kill switch: `flags set support_agent.enabled false` (takes effect within 30 s, no deploy).
- Caps: 15 steps/run, $0.20/run, $400/day.
- Live sampling: every Monday, 120 runs stratified by route, graded with
  `evals/support-agent/graders.py`. Owner: Dana (support engineering).
- Page someone when: pass rate leaves the baseline band, a safety task fails live, or the refusal rate
  exceeds 5%.
