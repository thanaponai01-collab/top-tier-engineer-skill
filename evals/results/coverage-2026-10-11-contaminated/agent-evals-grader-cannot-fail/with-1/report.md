Not yet. The evals can't tell a working agent from a broken one, so building against them would give you false green results. I haven't changed anything.

**Proven (I ran it):** the stub in `triage_agent.py` returns `billing` for every ticket. The grader scores it 8/8 and exits 0, which is what the README treats as "the harness works."

**Problems in the evals:**
1. **The grader ignores the answer key.** `ok()` in `grade.py:9-11` only checks that the output is some known queue. It never compares against `expected`, so any agent that returns a valid queue name passes. This is the failure the agent-evals skill warns about: a grader that passes a wrong agent. Tasks 2, 3, 4, 5, 7 and 8 should have failed the stub, but didn't.
2. **The task set is too small and too easy.**
   - It has 8 tasks, and the skill says at least 12, ideally about 20.
   - There are no `escalate` cases: legal threats, self-harm, safety, or tickets that can't be routed.
   - There are no injection cases, such as a ticket saying "ignore your instructions and…", even though the README says the agent must never act on those.
   - There are no ambiguous tickets. Task 6 ("update the card on my account") could be read as billing or account, and I'd call it the only borderline one.
   - There is no held-out slice.
3. **Nothing is frozen.** There's no baseline, so the grader and tasks could still be edited to make a run pass.

**What I'd do next:**
- Make `ok()` compare `out["queue"]` to `task["expected"]`.
- Add about 12 tasks covering escalate, injection, and ambiguous cases, with a quarter held out.
- Check that the stub and a deliberately wrong agent both score low.
- Freeze the grader and tasks with a `verify-loop` baseline.
- Then start building the agent.

The skill treats a grader believed wrong as a finding for a person, not something I edit on my own. Do you want me to make those changes? If yes, tell me whether the ambiguous cases like task 6 should be graded by one expected queue or by a set of acceptable queues.