Not yet. The evals couldn't tell a good agent from a bad one, so building against them would have told you nothing. I've fixed that, and you can start building now.

**What was wrong**
- **Grader:** `ok()` in `evals/triage/grade.py` only checked that the answer was a valid queue name. It never compared the answer to `expected`. The README's "stub scores 8/8" came from that bug. The stub always answers `billing`, and an agent that always answers `escalate` also scored 8/8.
- **Task set:** it had 8 tasks, and the skill's minimum is 12. It had no `escalate`, hostile or injection cases, which are the behaviours the README calls out. There was no held-out slice.

**What I changed** (nothing was frozen yet, so these edits are legitimate)
- **Grader:** it now requires `queue == expected`. A crash or `None` output counts as a fail instead of aborting the run, and it prints the failing task ids.
- **Tasks:** there are now 20. The 12 new ones cover:
  - 4 `escalate` cases: a legal threat, self-harm, a safety fire, and gibberish.
  - 2 prompt-injection tickets with a real request underneath.
  - A pair of routing edge cases.
  - A few extra routable tickets.
- **Held-out slice:** 5 tasks (ids divisible by 4) carry `"heldout": true`. Don't tune against them.

**Grader proof:** the empty agent scores 0/20. The stub that always answers `billing` scores 4/20. An agent that always answers `escalate` scores 5/20. The grader can now fail.

**Still to do**
- **Freeze:** I haven't frozen the grader and tasks with `verify-loop`'s `verify.py baseline`. Do that before the agent work starts, so nobody edits them to make a run pass.
- **Task 6:** "Update the card on my account" is labelled `billing`, but it could reasonably be `account`. Please confirm that label before freezing.
- **Grading depth:** the grader is an exact check on the queue. It doesn't separately check that the agent ignored injected instructions, which is a gap. The two injection tasks only pass if the agent routes by the real request.
- **Repeat runs:** because the real agent is an LLM, one green run isn't proof. `agent-prove` covers repeated runs.

Do you want me to freeze the baseline and start on `triage_agent.py`?