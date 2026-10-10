I'd hold off building. I ran grade.py against the stub (8/8) and against a throwaway module that
always says "shipping" (also 8/8). The grading function only asks whether the answer is a known
queue; it never compares it to the expected queue in each task. So a perfect score tells you
nothing, and the 8/8 in the README is the bug, not a sign the harness works.

Second problem: the task set. Eight easy routing tickets, with none of the cases the README cares
about. No escalation case, no ticket that tries to instruct the agent, nothing ambiguous, and no
held-out slice set aside. With 8 tasks one flaky run moves the score by more than 10 points.

To do before building: compare against expected; grow to ~20 tasks including escalate and
injection ones; mark a held-out quarter; confirm an empty agent and a constant agent both score low;
then freeze it.
