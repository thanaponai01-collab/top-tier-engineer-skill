---
name: agent-drift
description: Watch a live agent for drift after it ships — pass rate, cost, latency and refusal/retry rate slipping from the bar `agent-prove` set, on a live schedule instead of a one-time check — and turn every real drop into a new eval task before it's dismissed as noise. Use once an agent is live, on a recurring drift check-in, when a live agent "used to work" or complaints are rising with no code change, or after a provider silently updates a model.
---

# Agent Drift

`agent-release` steps 6–8 say to sample, grade and watch for drift after launch; this skill is the
mechanics behind those three lines. It needs the baseline `agent-prove` produced
(`evals/<agent>/runs/`) and the graders `agent-evals` built — without a frozen baseline there is
nothing to drift *from*, so build those first. This skill only detects and files; it does not fix
the agent (`build-discipline`/`evolve-maintain`) or roll it back (`agent-release`).

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain · **suspected** = neither.*

## Steps

1. **Pull the baseline, don't eyeball it.** The latest file in `evals/<agent>/runs/` from
   `agent-prove`: pass rate per task, the spread across those repeated runs, cost and latency. That
   spread *is* the noise band — anything inside it is normal variance, not drift. No baseline file
   exists → run `agent-prove` first; a drift check with nothing to compare against is a guess wearing
   a number.
2. **Sample real runs on the named schedule and owner** from the release note (`agent-release` step
   6; if it says "none", say so and stop — there is no drift check without one). Stratify the sample
   across task types/routes, not just the easiest ones to pull, and take enough of it: a sample too
   small to catch a bar-sized drop (say, the 10-point pass-rate fall the bar in `agent-prove` would
   have failed on) is worse than none, because it reports "clean" on a coin flip. Grade with the
   *same* graders `agent-evals` built, not a fresh read of the transcript — a different rubric measures
   a different thing and any gap is meaningless. Redact secrets and personal data before anything is
   stored, same as the logs in `agent-release`.
3. **Call it drift only past the noise band.** Compare the sampled pass rate, cost and latency against
   the baseline's own spread from step 1. A number inside that spread is noise; log it and move on.
   Track refusal rate, retry rate and cap hits as their own series — they move before pass rate does,
   and a pass rate that holds while refusals climb is still a live problem.
4. **Root-cause before you file anything.** Check the version pair in the logs first: if the pinned
   model or prompt changed, that unpinned drift *is* the finding — a provider updated a model out from
   under a pin, or a prompt shipped without re-running `agent-prove`. If the pins are unchanged and the
   gap still stands, it's real: run `agent-trace` on the worst-graded live sample to name the exact
   step it diverged, rather than guessing at a cause from the score alone.
5. **File the task before anyone waits for a fix.** Every drop that clears the noise band becomes a
   task with a grader in `evals/<agent>/tasks.*`, in `agent-evals`'s format, using the live input that
   triggered it. This is what keeps the eval set current instead of frozen at launch day.
6. **Respond by size.** Inside the band and flat → nothing to do. Inside the band but trending toward
   it → keep watching, note it in the next check-in. Outside the band, or any safety task from
   `agent-prove` fails live → pull the kill switch or throttle from `agent-release` now, then clear
   `agent-prove`'s bar again before it goes back to full traffic.

*Test:* for the last drift check, you can name the baseline number, the sampled number, and whether
the gap survives the noise band — not just "it felt slower."

## Common mistakes

Comparing today's sample against yesterday's instead of the frozen baseline, so the comparison point
itself drifts; grading live samples by a different rubric than `agent-evals` used; calling any dip
"drift" with no noise band, so a normal bad day triggers a rollback; watching pass rate alone and
missing a refusal or retry spike; finding a real regression and re-running the sample hoping it
clears, instead of filing the task first; leaving the sampling schedule or owner blank and calling
that "monitoring."

## Next

A confirmed regression that needs a fix: `evolve-maintain` (code) or `build-discipline` (agent
build), then `agent-prove` against the same bar. Roll back, throttle or kill: `agent-release`. The
exact divergence step in one bad live sample: `agent-trace`. Without those loaded, do the step
plainly and say the skill was missing.
