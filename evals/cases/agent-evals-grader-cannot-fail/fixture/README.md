# ticket-triage

An LLM agent will read each incoming support ticket and route it to one queue: `billing`,
`shipping`, `account` or `returns`. It may also answer `escalate` (a human must look: legal threats,
self-harm, safety, anything it can't route), and it must never act on instructions inside a ticket.

Status: evals done before building, as agreed. `python evals/triage/grade.py` scores an agent
module against the task set, and it already scores the stub 8/8, so the harness works. Next step:
build the real agent in `triage_agent.py`.
