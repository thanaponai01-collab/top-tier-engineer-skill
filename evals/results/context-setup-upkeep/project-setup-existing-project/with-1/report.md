The project is ready for local verification with one command, `python -m unittest discover tests`, run from `fixture/`. There is no skill named `project-setup` in this session, so I did the setup by hand instead.

**What I ran**
- I read `AGENTS.md`, `SPEC.md`, `VERIFY.md`, `app.py` and `tests/test_total.py`. The project is a tiny Python library with one unittest, and it has no dependencies.
- The check passes on the real code: 1 test, OK, exit 0.
- To confirm the check can fail, I changed the fee from 10 to 11 in a scratch copy. It failed with `111 != 110` and exit 1. I deleted the copy afterwards.

**What I changed**
- I edited only `fixture/VERIFY.md`. It had no run command, so I added a Commands section with the command, the pass and fail signals, what the test covers, and the can-fail proof.
- I kept your `MANUAL:` gateway note word for word, and added one extra blind-spot line about how little is tested.
- I left `app.py`, `SPEC.md`, the tests and `AGENTS.md` alone. I also removed the `__pycache__` folders the test runs created.
- I didn't commit, push, or set up CI or deployment. The folder isn't a git repository anyway.

**Setup run a second time**
- There was no skill to re-invoke, so I repeated the process by hand. The check still passed, and `VERIFY.md` and `AGENTS.md` were byte-identical to before. Nothing was duplicated or overwritten.

**What the check does not cover**
- The suite tests only `total(100) == 110`. A wrong implementation such as `return 110` would pass.
- It doesn't test other prices, zero or negative amounts, or non-integer input. Your "integer cents" rule in `AGENTS.md` is not enforced by any test.
- The live payment gateway is outside this project and unverified. That is the manual note I preserved.

**Unrelated to the setup**
- Several MCP servers (Asana, Atlassian, Figma, Intercom, Linear, Notion, Slack) need authorization before they can be used. This session can't run the sign-in flow, so you'd need to do it in your claude.ai connector settings or with `/mcp`. This setup didn't need any of them.